import cv2
import numpy as np

from robocam.helpers import utility as utis
from robocam.overlay import writer_base as base
from robocam.overlay import colortools as ctools

def draw_circle(frame, center, radius, color='r', thickness=1, ref=None):

    _color = ctools.color_function(color)

    c = utis.abs_point(center, ref)
    r = int(radius)
    t = int(thickness)

    cv2.circle(frame, c, r, _color, t)


def draw_line(frame, pt1, pt2, color='r', thickness=1, ref=None):
    """
    draw a line
    :param frame:
    :param pt1:
    :param pt2:
    :param color:
    :param thickness:
    :param ref:
    :return:
    """
    _color = ctools.color_function(color)
    _pt1 = utis.abs_point(pt1, ref)
    _pt2 = utis.abs_point(pt2, ref)
    cv2.line(frame, _pt1, _pt2, _color, thickness)


def draw_cal_line(frame, center, angle, length, color='r', thickness=1, ref=None):
    """
    draw a line from the center angle and length
    :param frame:
    :param center:
    :param angle:
    :param length:
    :param color:
    :param thickness:
    :param ref:
    :return:
    """
    _color = ctools.color_function(color)
    _pt0, _pt1 = utis.line_from_center_angle_length(center, angle, length, ref=ref)
    cv2.line(frame, _pt0, _pt0, _color, thickness)


def draw_pal_line(frame, point, angle, length, color='r', thickness=1, ref=None):
    """
    draw a line from point angle and length
    :param frame:
    :param point:
    :param angle:
    :param length:
    :param color:
    :param thickness:
    :param ref:
    :return:
    """
    _color = ctools.color_function(color)
    _pt0, _pt1 = utis.line_from_point_angle_length(point, angle, length, ref=ref)
    cv2.line(frame, _pt0, _pt0, _color, thickness)


def write_text(frame,
               text,
               pos=(10, 50),
               font=None,
               color='b',
               scale=1,
               ltype=2,
               ref=None):
        _color = ctools.color_function(color)
        _pos = utis.abs_point(pos, ref, frame.shape)
        _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font

        cv2.putText(frame,
                    text,
                    _pos,
                    _font, scale, _color, ltype)

class Line(base.Writer):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,
                 wtype='ep'# line type
                 ):

        super().__init__()
        self.color = color
        self.thickness = thickness
        self.reference = None
        self.wtype = wtype

    def write(self, frame, *args, ref=None, wtype=None, color=None, thickness=None):

        _thickness = self.thickness if thickness is None else thickness
        _color = self.color if color is None else color
        _wtype = self.wtype if wtype is None else wtype

        if _wtype == 'pal':
            point0, point1 = self._from_point_angle_length(*args, ref=ref)
        elif _wtype == 'cal':
            point0, point1 = self._from_center_angle_length(*args, ref=ref)
        else:
            point0, point1 = self._from_end_points(*args, ref=ref)

        cv2.line(frame, point0, point1, _color, _thickness)

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
            _point = utis.abs_point(point, ref)

        elif self.reference is not None:
            _point = utis.abs_point(point, self.reference)

        else:
            _point = int(point[0]), int(point[1])

        return _point


