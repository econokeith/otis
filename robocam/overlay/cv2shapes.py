import cv2
import numpy as np

from robocam.helpers import utilities as utis
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
    _pt1 = utis.abs_point(pt1, ref, frame.shape)
    _pt2 = utis.abs_point(pt2, ref, frame.shape)
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
    _pt0, _pt1 = utis.line_from_center_angle_length(center, angle, length, ref=ref, dim=frame.shape)
    cv2.line(frame, _pt0, _pt1, _color, thickness)


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
    _pt0, _pt1 = utis.line_from_point_angle_length(point, angle, length, ref=ref, dim=frame.shape)
    cv2.line(frame, _pt0, _pt1, _color, thickness)


def write_text(frame, text, pos=(10, 50), font=None, color='b', scale=1, ltype=2, ref=None, jtype='l'):

        _color = ctools.color_function(color)
        _pos = utis.abs_point(pos, ref, frame.shape)
        _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
        _pos = utis.find_justified_start(text, _pos, _font, scale, ltype, jtype)

        cv2.putText(frame,
                    text,
                    _pos,
                    _font, scale, _color, ltype)

def write_bordered_text(frame,
                        text,
                        pos=(10, 50),
                        font=None,
                        color='b',
                        bcolor='r',# background color
                        scale=1,
                        btype=-1, # -1 means filled
                        ltype=2,
                        ref=None,
                        border=10,
                        jtype='l'):

    _color = ctools.color_function(color)
    _bcolor = ctools.color_function(bcolor)
    _pos = utis.abs_point(pos, ref, frame.shape)
    _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
    _pos = utis.find_justified_start(text, _pos, _font, scale, ltype, jtype)

    w, h = cv2.getTextSize(text, _font, scale, ltype)[0]

    l = _pos[0] - border
    r = l + w + 2 * border
    b = _pos[1] + border
    t = b - h - 2 * border

    cv2.rectangle(frame, (l, t), (r, b), _bcolor, btype)
    write_text(frame, text, pos=_pos, font=_font, color=_color,
               scale=scale, ltype=ltype, ref=None, jtype='l')



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
            draw_pal_line(frame, *args, color=_color, thickness=_thickness, ref=ref)
        elif _wtype == 'cal':
            draw_cal_line(frame, *args, color=_color, thickness=_thickness, ref=ref)
        else:
            point0 = utis.abs_point(*args[0], ref, frame.shape[:2])
            point1 = utis.abs_point(*args[1], ref, frame.shape[:2])

            cv2.line(frame, point0, point1, _color, _thickness)



