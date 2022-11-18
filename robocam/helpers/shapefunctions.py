import cv2

import robocam.helpers.coordtools
import robocam.helpers.maths
import robocam.helpers.texttools
from robocam.helpers import dstructures, colortools

def draw_circle(frame, center, radius, color='r', thickness=1, ltype=None, ref=None):
    _color = colortools.color_function(color)

    c = robocam.helpers.coordtools.abs_point(center, ref, dim=frame.shape)
    r = int(radius)
    t = int(thickness)

    cv2.circle(frame, c, r, _color, t, ltype)


def draw_rectangle(frame, rt_point, lb_point, color='r', thickness=1, ltype=None, ref=None):
    _color = colortools.color_function(color)
    r, t = robocam.helpers.coordtools.abs_point(rt_point, ref, dim=frame.shape)
    l, b = robocam.helpers.coordtools.abs_point(lb_point, ref, dim=frame.shape)
    cv2.rectangle(frame, (l, t), (r, b), _color, thickness, ltype)


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
    _color = colortools.color_function(color)
    _pt1 = robocam.helpers.coordtools.abs_point(pt1, ref, frame.shape)
    _pt2 = robocam.helpers.coordtools.abs_point(pt2, ref, frame.shape)
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
    _color = colortools.color_function(color)
    _pt0, _pt1 = robocam.helpers.maths.line_from_center_angle_length(center, angle, length, ref=ref, dim=frame.shape)
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
    _color = colortools.color_function(color)
    _pt0, _pt1 = robocam.helpers.maths.line_from_point_angle_length(point, angle, length, ref=ref, dim=frame.shape)
    cv2.line(frame, _pt0, _pt1, _color, thickness)


# todo combine with bordered

def write_text(frame,
               text,
               pos=(10, 50),
               font=None,
               color='b',
               scale=1,
               ltype=1,
               ref=None,
               jtype='l',
               thickness=1,
               bl=False
               ):
    _color = colortools.color_function(color)
    _pos = robocam.helpers.coordtools.abs_point(pos, ref, frame.shape)
    _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
    _pos = robocam.helpers.texttools.find_justified_start(text, _pos, _font, scale, ltype, jtype)

    cv2.putText(frame,
                text,
                _pos,
                _font,
                scale,
                _color,
                thickness,
                ltype,
                bl)


def write_bordered_text(frame,
                        text,
                        pos=(10, 50),
                        font=None,
                        color='b',
                        bcolor='r',  # background color
                        scale=1,
                        btype=-1,  # -1 means filled
                        ltype=2,
                        ref=None,
                        border=10,
                        jtype='l'):
    _color = colortools.color_function(color)
    _bcolor = colortools.color_function(bcolor)
    _pos = robocam.helpers.coordtools.abs_point(pos, ref, frame.shape)
    _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
    _pos = robocam.helpers.texttools.find_justified_start(text, _pos, _font, scale, ltype, jtype)

    w, h = cv2.getTextSize(text, _font, scale, ltype)[0]

    l = _pos[0] - border
    r = l + w + 2 * border
    b = _pos[1] + border
    t = b - h - 2 * border

    cv2.rectangle(frame, (l, t), (r, b), _bcolor, btype)
    write_text(frame, text, pos=_pos, font=_font, color=_color, scale=scale, ltype=ltype, ref=ref, jtype='l')


def write_transparent_background(frame, right_top, left_bottom, transparency=.25, ref=None):
    h, w, _ = frame.shape

    r, t = robocam.helpers.coordtools.abs_point(right_top, ref, dim=frame.shape)
    l, b = robocam.helpers.coordtools.abs_point(left_bottom, ref, dim=frame.shape)

    portion = frame[t:b, l:r]

    grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY) * transparency
    portion[:, :, 0] = portion[:, :, 1] = portion[:, :, 2] = grey.astype('uint8')
    colortools.frame_portion_to_grey(portion)


def write_copy_box(frame,
                   copy_from_location,  #
                   copy_to_location,
                   ):
    rf, tf, lf, bf = copy_from_location
    rt, tt, lt, bt = copy_to_location

    to_size = lt - rt, bt - tt

    copy_image = cv2.resize(frame[tf:bf, lf:rf], to_size, interpolation=cv2.INTER_LINEAR)

    frame[tt:bt, lt:rt] = copy_image


