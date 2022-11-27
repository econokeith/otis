import copy
import os
import time

import cv2
import numpy as np

import otis.helpers.cvtools
import otis.overlay.bases as base
from otis.helpers import shapefunctions as shapes, cvtools, misc, coordtools, timers
from otis.overlay import bases

class ImageAsset(base.AssetWriter):

    def __init__(self,
                 src,
                 position = (100,100),
                 bit=0,
                 scale = 1,
                 #let's you flip the bit-mask 0, 1, or None
                 size = None, #if none stays the same, otherwise change
                 loc = (100, 100) #location of center
                 ):
        """
        src is the path to a directory that contains exactly 2 image files. The image or bitmap to be used and a 2D
        bit-mask that directs
        the writer which pixels to write and which to ignore. The naming convention is: name_of_image.jpg and
        name_of_image_mask.jpg
        :param src:S
        """
        files = os.listdir(src)
        files.sort(key=len)
        self.img = cv2.imread(os.path.join(src, files[0]))
        if scale != 1:
            self.img = cv2.resize(self.img, (0, 0), fx=scale, fy=scale)

        self.bit = bit
        self.coords = None

        if bit in [0, 1] and len(files)>1:
            self.mask = cv2.imread(os.path.join(src, files[1]))

            if scale != 1:
                # triple_mask = np.stack([self.mask]*3, axix=-1)

                self.mask = cv2.resize(self.mask, (0, 0), fx=scale, fy=scale)

            self.mask[self.mask <128] = 0
            self.mask[self.mask >=128] = 255
            self.locs = np.asarray(np.nonzero(self.mask == self.bit))

        else:
            self.mask = None
            self.locs = None

        #this might be wrong
        self.center = self.img.shape[0] // 2, self.img.shape[1] // 2
        self.dim = self.img.shape[:2][::-1]
        self._position = position

    @property
    def position(self):
        if self.coords is not None:
            return bbox_to_center(self.coords)
        else:
            return self.position

    #TODO THIS IS FLIPPING COORDINATEES
    def _c_to_tl_on_frame(self, f_center):
        """
        find the coords of the frame that represents the top corner of hte image asset given
        the coords of the center of the asset on the frame
        :return:
        """
        img_c = self.center
        return f_center[0] - img_c[1], f_center[1] - img_c[0]

    def write(self, frame, position=None, pos_type='c'):
        """
        loc type can either be 'c' for center or 'tl' for top right. must be given in absolute frame
        coords
        :param frame:
        :param pos:
        :param pos_type:
        :return:
        """
        v, h, _ = self.img.shape
        pos = self.position if position is None else position
        t, l = pos_type if pos_type == 'tl' else self._c_to_tl_on_frame(pos[::-1])
        b = t + v
        r = l + h

        if self.mask is None:
            frame[t:b, l:r] = self.img

        else:
            loc_y = self.locs[0]
            loc_x = self.locs[1]

            frame[t + loc_y, l + loc_x] = self.img[loc_y, loc_x]

def bbox_to_center(coords):
    t, r, b, l = coords
    return int((r+l)/2), int((t+b)/2)

class AssetWithImage(bases.AssetWriter):

    def __init__(self,
                 image=None,
                 mask=None,
                 resize_to=None,
                 resize_on_write = None,
                 scale = 1,
                 center = (100, 100),
                 ref = None,
                 hitbox_type = 'rectangle',
                 copy_updates = False,
                 mask_bit = 0,
                 ):

        super().__init__()

        self.locs = None



        self.coords = np.zeros(4, dtype=int)
        self.coords[:2] = center
        self.resize_to = resize_to
        self.scale = scale
        self.resize_on_write = resize_on_write
        if self.resize_on_write is not None:
            self.copy_updates = False
            self.resize_to = self.resize_on_write
        else:
            self.copy_updates = copy_updates

        if image is not None and self.copy_updates is True:
            self._image = copy.deepcopy(self.resize_image(image))

        elif image is not None and self.copy_updates is False:
            self._image = image

        elif image is None and resize_to is not None:
            w, h = self.coords[2:]
            self._image = np.zeros(3*w*h, dtype='uint8').reshape((h, w, 3))

        else:
            self._image = None

        self.mask_bit = mask_bit
        self.mask = mask
        self.ref = ref
        self.hitbox_type = hitbox_type


    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image):
        if self._image is None:
            self._image = self.resize_image(new_image)
            return

        if (new_image.shape == self._image.shape) is True:
            _image = new_image
        else:
            _image = self.resize_image(new_image)

        if self.copy_updates is True:
            self._image[:,:,:] = _image
        else:
            self._image = _image

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, new_mask):
        if new_mask is None:
            self._mask = None
        else:
            _mask = self.resize_image(new_mask)
            _mask[_mask < 128] = 1
            _mask[_mask >= 128] = 0
            self._mask = _mask.astype(bool)

    @property
    def shape(self):
        return self.hitbox_type

    @property
    def center(self):
        return self.coords[:2]

    @center.setter
    def center(self, new_center):
        self.coords[:2] = new_center

    @property
    def height(self):
        return self.coords[3]

    @property
    def radius(self):
        return self.coords[2]//2

    @property
    def width(self):
        return self.coords[2]

    @property
    def resize_to(self):
        return self._resize_to

    @resize_to.setter
    def resize_to(self, new_size):
        self._resize_to = new_size
        if new_size is not None:
            self.coords[2:] = new_size

    def resize_image(self, new_image):
        if self.resize_on_write is not None:
            return new_image

        if (new_image is None) or (self._image is None) or (self.shape[:2] == self._image.shape[:2]):
            return new_image

        if self.resize_to is not None:
            image = cv2.resize(new_image, self.resize_to)
        elif isinstance(self.scale, (float, int)) and self.scale != 1:
            image = cv2.resize(new_image, (0, 0), fx=self.scale, fy=self.scale)
        elif isinstance(self.scale, (tuple, list, np.ndarray)):
            image = cv2.resize(new_image, (0, 0), fx=self.scale[0], fy=self.scale[1])
        else:
            image = new_image

        self.resize_to = image.shape[:2][::-1]

        return image

    def add_image_from_file(self, path_to_images):

        abs_path = cvtools.abs_path_relative_to_calling_file(path_to_images)
        files = os.listdir(abs_path)
        image_file = min(files, key=len)
        self.image = cv2.imread(os.path.join(abs_path, image_file))

        if len(files) > 1:
            mask_file = max(files, key=len)
            self.mask = cv2.imread(os.path.join(abs_path, mask_file))

        return self

    def write(self, frame, image=None):

        _image = self.image if image is None else image

        if self.resize_on_write is None:
            _image = self.resize_image(_image)
        else:
            _image = cv2.resize(_image, self.resize_on_write)

        r,t,l,b = coordtools.translate_box_coords(self.coords,
                                                 in_format='cwh',
                                                 out_format='rtlb',
                                                 ref=self.ref,
                                                 dim=frame
                                                 )

        dr = dt = dl = db = 0
        h_f, w_f, _ = frame.shape
        h_i, w_i = self.coords[2:]

        # make sure that we aren't writing outside the bounds of the frame
        if l < 0:
            dl = -l
            l = 0

        if t < 0:
            dt = -t
            t = 0

        if r >= w_f:
            dr = r - w_f + 1
            r = w_f-1

        if b >= h_f:
            db = b - h_f + 1
            b = h_f - 1

        frame_portion = frame[t:b, l:r]
        image_portion = _image[dt: h_i-db+1, dl: w_i-dr+1]

        if self.mask is not None:
            # resize mask
            _mask = self.mask[dt: h_i-db+1, dl: w_i-dr+1]
            frame_portion[_mask] = image_portion[_mask]
        else:
            frame_portion[:,:,:] = image_portion

    def center_width_height(self):
        cx, cy, w, h = self.coords
        if self.hitbox_type == 'circle':
            return cx, cy, w//2, h//2
        else:
            return cx, cy, w, h



if __name__=='__main__':

    dim = (800, 800)
    fps = 30
    frame = np.zeros(dim[0] * dim[1] * 3, dtype='uint8').reshape((dim[1], dim[0], 3))
    fps_limiter = timers.SmartSleeper(1 / fps)
    image_asset = AssetWithImage(center=(400, 400)).add_image_from_file('./photo_assets/pie_asset')
    while True:
        frame[:,:,:] = 0
        image_asset.write(frame)
        cv2.imshow('', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break