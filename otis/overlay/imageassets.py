import os
import time

import cv2
import numpy as np

import otis.helpers.cvtools
import otis.overlay.bases as base
from otis.helpers import shapefunctions as shapes, cvtools
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
                 scale = 1,
                 center = (100, 100),
                 ref = None,
                 hitbox_type = 'rectangle'
                 ):

        super().__init__()

        self.locs = None
        self.resize_to = resize_to
        self.scale = scale
        self.image = image
        self.mask = mask

        self.coords = np.zeros(4, dtype=int)
        self.coords[:2] = center

        if resize_to is None:
            self.coords[2:] = image.shape[:2][::-1]
        else:
            self.coords[2:] = resize_to

        self.ref = ref
        self.hitbox_type = hitbox_type

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image):
        self._image = self.resize(new_image)

    @property
    def mask(self):
        return self._mask

    @mask.setter
    def mask(self, new_mask):
        self._mask = self.resize(new_mask)
        self.mask[self.mask < 128] = 0
        self.mask[self.mask >= 128] = 255

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
        return self.coords[2]

    @property
    def width(self):
        return self.coords[2]

    def resize(self, new_image):
        if self.resize_to is not None:
            image = cv2.resize(new_image, self.resize_to)
        elif isinstance(self.scale, (float, int)) and self.scale != 1:
            image = cv2.resize(new_image, (0, 0), fx=self.scale, fy=self.scale)
        elif isinstance(self.scale, (tuple, list, np.ndarray)):
            image = cv2.resize(new_image, (0, 0), fx=self.scale[0], fy=self.scale[1])
        else:
            image = new_image

        return image

    def add_image_from_file(self, path_to_images):

        abs_path = cvtools.abs_path_relative_to_calling_file(path_to_images)
        files = os.listdir(abs_path)
        image_file = min(files, key=len)
        self.image = cv2.imread(os.path.join(abs_path, image_file))

        if len(files) > 1:
            mask_file = max(files, key=len)
            self.mask = cv2.imread(os.path.join(abs_path, mask_file))
            self.locs = np.asarray(np.nonzero(self.mask == 0))


if __name__=='__main__':
    pass