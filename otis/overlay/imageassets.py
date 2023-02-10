import copy
import os
import time

import cv2
import numpy as np

import otis.helpers.cvtools
import otis.overlay.bases as base
from otis.helpers import cvtools, misc, coordtools, timers
from otis.overlay import bases, shapes


class ImageAsset(bases.AssetWriter):

    def __init__(self,
                 image=None,
                 mask=None,
                 resize_to=None,
                 scale=1,
                 center=(100, 100),
                 ref=None,
                 hitbox_type='rectangle',
                 copy_updates=False,
                 mask_bit=0,
                 use_mask=False,
                 border=False,
                 b_color='radius',
                 b_thickness=1,
                 ):
        """
        makes the images
        Args:
            image: cv2 frame or portion, default = None
            mask: mask to change the shape of the frame, default is None
            resize_to: resize the frame to (x, y), default = None (will set itself to frame size)
            scale: increases dimensions (w, h) by scale, default = 1, has no effect if resize_to is set
            center: (x,y) coords of the center of the object
            ref: reference point for (x, y), if ref = None, (x, y) are absolute if None, else cartesian relative coords
                 to the absolute reference point
            hitbox_type: either 'circle' or 'rectangle'.
            copy_updates:
            mask_bit:
            use_mask: loads, resizes, and uses a circle mask so only a circle centered at the center of the frame
                             is copied onto the frame. The frame needs to be perfectly square, otherwise, the pose_results can
                             be unstable
        """

        super().__init__()
        if isinstance(image, str):
            path_to_dir = os.path.abspath(os.path.dirname(__file__))
            path_to_image = os.path.join(path_to_dir, image)
            image = cv2.imread(image)


        self._image = None
        self.locs = None
        self._coords = np.zeros(4, dtype=int)
        self._coords[:2] = center
        self.resize_to = resize_to
        self.scale = scale
        self.copy_updates = copy_updates
        self._coord_format = 'cwh'

        if image is not None and self.copy_updates is True:
            self._image = copy.deepcopy(self.resize_image(image))

        elif image is not None and self.copy_updates is False:
            self._image = image

        elif image is None and resize_to is not None:
            w, h = self.coords[2:]
            self._image = np.zeros(3 * w * h, dtype='uint8').reshape((h, w, 3))

        else:
            self._image = None

        self.mask_bit = mask_bit

        # loads a saved circlular mask for writing
        if use_mask is True:
            path_to_dir = os.path.abspath(os.path.dirname(__file__))
            path_to_mask = os.path.join(path_to_dir, 'photo_assets/masks/circle_mask.jpg')
            self.mask = cv2.imread(path_to_mask)

        else:
            self.mask = mask

        self.ref = ref
        self.hitbox_type = hitbox_type

        if border is True and self.hitbox_type == 'circle':
            self.border = shapes.Circle(color=b_color,
                                        thickness=b_thickness,
                                        coord_format='cwh',
                                        update_format='cwh',
                                        )

        elif border is True and self.hitbox_type == 'rectangle':
            self.border = shapes.Rectangle(color=b_color,
                                           thickness=b_thickness,
                                           coord_format='cwh',
                                           update_format='cwh',
                                           )
        else:
            self.border = None

    @property
    def coord_format(self):
        return self._coord_format

    @coord_format.setter
    def coord_format(self, new):
        if new != 'cwh':
            raise ValueError("ImageAsset can not have its coord_format value changed from 'cwh'")

    @property
    def image(self):
        return self._image

    @image.setter
    def image(self, new_image):
        # Todo ImageAsset - need to change the frame update to be able to not resize when resize is set
        """
        1) if there isn't an frame saved, it will save the frame
            - if resize_to is set, then it will resize the frame
            = otherwise it will set resize
        2) if there's an frame saved it will resize the new frame to that size
        3) if copy_updates is True, it will copy it. otherwise it will save the reference
            (this only occurs if there isn't a resize
        4) if we don't want a resize on a new frame, set self. resize = None before adding the frame

        Args:
            new_image: frame or frame portion
        Returns:
            N/A
        """
        if self._image is None:
            self._image = self.resize_image(new_image)
            return

        if (new_image.shape == self._image.shape) is True:
            _image = new_image
        else:
            _image = self.resize_image(new_image)

        if self.copy_updates is True:
            self._image[:, :, :] = _image
        else:
            self._image = _image

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = new_coords
        self._resize_to = self._coords[2:]

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
        return self.coords[2] // 2

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

            if self._image is None:
                w, h = new_size
                self._image = np.zeros(3 * w * h, dtype='uint8').reshape((h, w, 3))

            else:
                self._image = self.resize_image(self._image)

    def resize_image(self, new_image):
        """

        :param new_image:
        :return:
        returns frame it's the same size as the one saved
        """
        if (new_image is None) or (self._image is None) or (new_image.shape[:2] == self._image.shape[:2]):
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

    def add_image_from_file(self, path_to_images, file=None):
        """
        loads an frame from file
        Args:
            path_to_images: path to images. if it is relative, there needs to be a ./ or ../ in the path
            file: must always be used as __file__

        Returns: self

        """
        abs_path = cvtools.abs_path_relative_to_calling_file(path_to_images, file=file)
        files = os.listdir(abs_path)
        image_file = min(files, key=len)

        self.image = cv2.imread(os.path.join(abs_path, image_file))
        self.resize_to = self.image.shape[:2][::-1]

        if len(files) > 1:
            mask_file = max(files, key=len)
            self.mask = cv2.imread(os.path.join(abs_path, mask_file))

        return self

    def write(self, frame, image=None, coords=None, ref=None, in_format='cwh', resize=True):
        """

        Args:
            frame: cv2 camera frame
            image: if frame is not None, will write/resize self.frame,
            coords:
            ref:
            in_format:
            resize:

        Returns:

        """
        _coords = self.coords if coords is None else coords
        _image = self.image if image is None else image
        _ref = self.ref if ref is None else ref

        if resize is True:
            _image = self.resize_image(_image)

        # the coords stuff isn't totally right here\
        # it won't update / resize with coords adn it will be thrown off if they are used to write
        # TODO: double check the imageasset write function
        r, t, l, b = coordtools.translate_box_coords(_coords,
                                                     in_format=in_format,
                                                     out_format='rtlb',
                                                     ref=_ref,
                                                     dim=frame
                                                     )

        dr = dt = dl = db = 0
        h_f, w_f, _ = frame.shape
        h_i, w_i = self.coords[2:]

        bx, by = (l - r) // 2, (b - t) // 2
        bw, bh = h_i, w_i

        # make sure that we aren't writing outside the bounds of the frame
        if l < 0:
            dl = -l
            l = 0

        if t < 0:
            dt = -t
            t = 0

        if r >= w_f:
            dr = r - w_f + 1
            r = w_f

        if b >= h_f:
            db = b - h_f + 1
            b = h_f

        # TODO: fix the issue with images resizing differently due to rounding / conversion from cwh format
        frame_portion = frame[t:b + 1, l:r + 1]
        # image_portion = _image[dt: h_i - db, dl: w_i - dr]
        image_portion = _image[dt: h_i - db + 1, dl: w_i - dr + 1]

        mismatch = False
        if frame_portion.shape != image_portion.shape:  # somethign happens here with the resizing that causes lots of errors
            # this just makes sure there any shape mismatches
            x_dim = min(frame_portion.shape[1], image_portion.shape[1])
            y_dim = min(frame_portion.shape[0], image_portion.shape[0])
            frame_portion = frame_portion[:y_dim, :x_dim]
            image_portion = image_portion[:y_dim, :x_dim]
            mismatch = True

        if self.mask is not None:
            # resize mask
            _mask = self.mask[dt: h_i - db + 1, dl: w_i - dr + 1]
            # check for mismatches
            if mismatch is True:
                _mask = _mask[:y_dim, :x_dim]
            frame_portion[_mask] = image_portion[_mask]
        else:
            frame_portion[:, :, :] = image_portion

        if self.border is not None:
            self.border.write(frame, coords=self.coords, ref=self.ref)

    def center_width_height(self):
        return self.coords


def open_image(path_to_file, file=None):
    if file is not None:
        path_to_dir = os.path.dirname(__file__)
        path = os.path.abspath(os.path.join(path_to_dir, path_to_file))
    else:
        path = path_to_file
    return cv2.imread(path)
