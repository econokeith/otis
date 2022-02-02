import cv2
import numpy as np

import robocam.overlay.colortools as ctools
import robocam.overlay.writer_base as base
from robocam.overlay.cv2shapes import Line
from robocam.overlay import cv2shapes as shapes
from robocam.overlay import textwriters
from robocam.overlay.textwriters import TextWriter


class BoundingBox(base.Writer):

    name_writer: TextWriter

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 thickness=2,  # line type
                 ):

        super().__init__()
        self.coords = np.zeros(4, dtype='uint8')
        self.color = color
        self.thickness = thickness
        self.name_writer = textwriters.TextWriter(scale=.75, ltype=1)
        self.name = ""
        self.show_name = True

    @property
    def center(self):
        t, r, b, l = self.coords
        return int((r+l)/2), int((t+b)/2)

    @property
    def diagonal(self):
        return np.sqrt(self.height**2 + self.width**2)

    @property
    def height(self):
        return self.coords[2] - self.coords[0]

    @property
    def width(self):
        return self.coords[1]-self.coords[3]

    def distance_from_center(self, point):
        """
        :param point:
        :return: distance between center and point
        """
        c = self.center
        return np.sqrt((c[0]-point[0])**2 + (c[1]-point[1])**2)


    def write(self, frame, name=None):
        t, r, b, l = self.coords
        cv2.rectangle(frame, (l, t), (r, b), self.color, self.thickness)

        if self.show_name is True or name is not None:
            _name = self.name if name is None else name
            self.name_writer.write(frame, position=(0, 20), text=_name, ref=(l, t))
            shapes.draw_line(frame,(0,0), (0, 15),self.color, 1,  ref=(l+15, t))


class BoundingCircle(BoundingBox):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,
                 bbox_coords = True
                 ):

        super().__init__(color=color, thickness=thickness)
        if bbox_coords is True:
            self.coords = np.zeros(4, dtype='uint8')
        else:
            self.coords = np.zeros(3, dtype='uint16')

        self.bbox_coords = bbox_coords

    @property
    def center(self):
        if self.bbox_coords is True:
            return super().center
        else:
            return self.coords[:2]

    @property
    def radius(self):
        if self.bbox_coords is True:
            return self.diagonal/2
        else:
            return self.coords[2]

    def write(self, frame):
        shapes.draw_circle(frame, self.center, self.radius, self.color, self.thickness)


class CrossHair(BoundingCircle):


    def __init__(self, *args, radius=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if radius is None:
            self.constant_size = False
            self._radius = 0
        else:
            self.constant_size = True
            self._radius = radius

        self.line_writer = shapes.Line(color='b', thickness=self.thickness, wtype='cal')

    @property
    def radius(self):
        if self.constant_size is True:
            return self._radius
        else:
            return super().radius

    @radius.setter
    def radius(self, new_radius):
        self._radius= new_radius
        self.constant_size = True

    def write(self, frame):
        center = self.center
        radius = self.radius
        r75 = radius*.75

        self.line_writer.write(frame, (0, r75), 0, radius*.2, ref=center, thickness=2)
        self.line_writer.write(frame, (0, -r75), 0, radius * .2, ref=center, thickness=2)
        self.line_writer.write(frame, (r75, 0), 90, radius * .2,  ref=center, thickness=2)
        self.line_writer.write(frame, (-r75, 0), 90, radius * .2, ref=center, thickness=2)
        #
        # shapes.draw_cal_line(frame, center, 90, radius*2.2, color='g', thickness=2)
        # shapes.draw_cal_line(frame, center, 0, radius*2.2, color='g', thickness=2)

        shapes.draw_circle(frame, center, radius, self.color, self.thickness)
        shapes.draw_circle(frame, center, radius/2, 'b', self.thickness/2)

        self.line_writer.write(frame, center, 90, radius*2.2, wtype='cal', thickness=1)
        self.line_writer.write(frame, center, 0, radius*2.2, wtype='cal',thickness=1)

        shapes.draw_circle(frame, center, 3, 'g', -1)
