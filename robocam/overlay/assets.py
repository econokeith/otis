import argparse
import ctypes

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.textwriters as writers
import robocam.overlay.writer_base as base
import robocam.helpers.utility as utis


class Line(base.Writer):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,  # line type
                 ):

        super().__init__()
        self.color = color
        self.thickness = thickness
        self.reference = None

    def write(self, frame, *args, ref=None, wtype='eps'):

        if wtype == 'pal':
            point0, point1 = self._from_point_angle_length(*args, ref=ref)
        elif wtype == 'cal':
            point0, point1 = self._from_center_angle_length(*args, ref=ref)
        else:
            point0, point1 = self._from_end_points(*args, ref=ref)

        cv2.line(frame, point0, point1, self.color, self.thickness)


    def _from_end_points(self, point_0, point_1, ref=None):
        a_point_0 = self._to_absolute_point(point_0, ref=ref)
        a_point_1 = self._to_absolute_point(point_1, ref=ref)
        return a_point_0, a_point_1

    def _from_point_angle_length(self, point, angle, length, ref=None):
        a_point = self._to_absolute_point(point, ref=ref)
        point_1 =[0,0]
        point_1[0] = int(a_point[0] + np.cos(angle*2*np.pi/360) * length)
        point_1[1] = int(a_point[0] - np.sin(angle*2*np.pi/360) * length)
        return a_point, point_1

    def _from_center_angle_length(self, center, angle, length, ref=None):
        a_center = self._to_absolute_point(center, ref=ref)
        add_x = np.cos(angle*2*np.pi/360) * length/2
        sub_y = -np.sin(angle*2*np.pi/360) * length/2
        point_0 = int(a_center[0] + add_x), int(a_center[1] + sub_y)
        point_1 = int(a_center[0] - add_x), int(a_center[1] - sub_y)
        return point_0, point_1

    def _to_absolute_point(self, point, ref=None):
        if ref is not None:
            _point = utis.abs_point(ref, point)

        elif self.reference is not None:
            _point = utis.abs_point(self.reference, point)

        else:
            _point = int(point[0]), int(point[1])

        return _point


class BoundingBox(base.Writer):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 thickness=2,  # line type
                 ):
        super().__init__()
        self.coords = np.zeros(4, dtype='uint8')
        self.color = color
        self.thickness = thickness

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


    def write(self, frame):
        t, r, b, l = self.coords
        cv2.rectangle(frame, (l, t), (r, b), self.color, self.thickness)

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
        cv2.circle(frame, self.center, int(self.radius), self.color, self.thickness)


class CrossHair(BoundingCircle):

    def __init__(self, *args, radius=None, **kwargs):
        super().__init__(*args, **kwargs)
        if radius is None:
            self.constant_size = False
            self._radius = 0
        else:
            self.constant_size = True
            self._radius = radius

        self.line_writer = Line(color='b', thickness=int(self.thickness/2))

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

        cv2.circle(frame, center, radius, self.color, self.thickness)
        cv2.circle(frame, center, int(radius/2), ctools.color_hash['b'], int(self.thickness/2))
        cv2.circle(frame, center, 3, ctools.color_hash['g'], -1)
        self.line_writer.write(frame, center, 90, radius*2.2, wtype='cal')
        self.line_writer.write(frame, center, 0, radius*2.2, wtype='cal')
        self.line_writer.write(frame, (0, r75), 0, radius*.2, wtype='cal', ref=center)
        self.line_writer.write(frame, (0, -r75), 0, radius * .2, wtype='cal', ref=center)
        self.line_writer.write(frame, (r75, 0), 90, radius * .2, wtype='cal', ref=center)
        self.line_writer.write(frame, (-r75, 0), 90, radius * .2, wtype='cal', ref=center)








