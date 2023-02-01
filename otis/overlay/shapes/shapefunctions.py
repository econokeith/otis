import cv2

import otis.helpers.coordtools as coordtools
import otis.helpers.maths
from otis.overlay.textwriters import texttools
from otis.helpers import dstructures, colortools


def draw_circle(frame, center, radius, color='r', thickness=1, ltype=None, ref=None):
    _color = colortools.color_function(color)

    _center = coordtools.absolute_point(center, ref, dim=frame)

    cv2.circle(frame, _center, int(radius), _color, int(thickness), ltype)


def draw_rectangle(frame,
                   coords,
                   color='r',
                   thickness=1,
                   ltype=None,
                   ref=None,
                   coord_format='rtlb'
                   ):
    """

    Args:
        frame:
        coords:
        color:
        thickness:
        ltype:
        ref:
        coord_format:

    Returns:

    """

    r, t, l, b = coordtools.translate_box_coords(coords, coord_format, 'rtlb', ref, frame)
    _color = colortools.color_function(color)
    cv2.rectangle(frame, (l, t), (r, b), _color, thickness, ltype)


def draw_line(frame,
              pt1,
              pt2,
              color='r',
              thickness=1,
              ltype=None,
              ref=None,
              ):
    """
    draw a text
    :param frame:
    :param pt1:
    :param pt2:
    :param color:
    :param thickness:
    :param ref:
    :return:
    """
    _color = colortools.color_function(color)
    _pt1 = coordtools.absolute_point(pt1, ref, frame)
    _pt2 = coordtools.absolute_point(pt2, ref, frame)
    cv2.line(frame, _pt1, _pt2, _color, thickness, ltype)

def draw_line(frame, point0, point1, color='r', thickness=1, ltype=None, ref=None):
    """

    Args:
        frame:
        point0:
        point1:
        color:
        thickness:
        ltype:
        ref:

    Returns:

    """
    _color = colortools.color_function(color)
    _point0 = coordtools.absolute_point(point0, ref, frame)
    _point1 = coordtools.absolute_point(point1, ref, frame)
    cv2.line(frame, _point0, _point1, _color, thickness, ltype)

def draw_arrow(frame, point0, point1, color='r', thickness=1, ltype=None, tipLength=None, ref=None):
    """

    Args:
        frame:
        point0:
        point1:
        color:
        thickness:
        ltype:
        ref:

    Returns:

    """
    _color = colortools.color_function(color)
    _point0 = coordtools.absolute_point(point0, ref, frame)
    _point1 = coordtools.absolute_point(point1, ref, frame)
    cv2.arrowedLine(frame, _point0, _point1, _color, thickness, ltype, tipLength=tipLength)

def draw_cal_line(frame, center, angle, length, color='r', thickness=1, ltype=None, ref=None):
    """
    draw a text from the center angle and length
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
    _pt0, _pt1 = otis.helpers.maths.line_center_angle_length_to_point_point(center, angle, length, ref=ref, dim=frame)
    cv2.line(frame, _pt0, _pt1, _color, thickness, ltype)


def draw_pal_line(frame, point, angle, length, color='r', thickness=1, ltype=None, ref=None):
    """
    draw a text from point angle and length
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
    _pt0, _pt1 = otis.helpers.maths.line_point_angle_length_to_point_point(point, angle, length, ref=ref, dim=frame)
    cv2.line(frame, _pt0, _pt1, _color, thickness, ltype)

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
               lb_origin=False
               ):

    _color = colortools.color_function(color)
    _pos = coordtools.absolute_point(pos, ref, frame)
    _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
    _pos = texttools.find_justified_start(text, _pos, _font, scale, ltype, jtype)

    cv2.putText(frame,
                text,
                _pos,
                _font,
                scale,
                _color,
                thickness,
                ltype,
                lb_origin)

def write_bordered_text(frame,
                        text,
                        pos=(10, 50),
                        font=None,
                        color='b',
                        scale=1,
                        ltype=1,
                        ref=None,
                        jtype='l',
                        lb_origin=True,
                        v_space=10,
                        h_space=10,
                        b_color='r',
                        b_ltype=1,
                        b_thickness=1,
                        ):

    _color = colortools.color_function(color)
    _bcolor = colortools.color_function(b_color)
    _pos = otis.helpers.coordtools.absolute_point(pos, ref, frame)
    _font = cv2.FONT_HERSHEY_DUPLEX if font is None else font
    _pos = otis.helpers.texttools.find_justified_start(text, _pos, _font, scale, ltype, jtype)

    w, h = cv2.getTextSize(text, _font, scale, ltype)[0]

    l = _pos[0] - h_space
    r = l + w + 2 * h_space
    b = _pos[1] + v_space
    t = b - h - 2 * v_space

    cv2.rectangle(frame, (l, t), (r, b), _bcolor, b_ltype, b_thickness)

    write_text(frame,
               text,
               pos=_pos,
               font=_font,
               color=_color,
               scale=scale,
               ltype=ltype,
               ref=ref,
               jtype=jtype,
               lb_origin=lb_origin
               )

def write_transparent_background(frame,
                                 coords,
                                 coord_format='rtlb',
                                 transparency=.25,
                                 ref=None
                                 ):

    r, t, l, b = coordtools.translate_box_coords(coords, coord_format, 'rtlb', ref, frame)
    portion = frame[t:b, l:r]
    # grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY) * transparency
    # portion[:, :, 0] = portion[:, :, 1] = portion[:, :, 2] = grey.astype('uint8')
    colortools.frame_portion_to_grey(portion)


def copy_frame_portion_to(frame,
                          source_coords,  # r, t, l, b
                          destination_coords,
                          source_format='rtlb',
                          destination_format='rtlb',
                          source_ref=None,
                          destination_ref=None,
                          ):

    rf, tf, lf, bf = coordtools.translate_box_coords(source_coords,
                                                     in_format=source_format,
                                                     out_format='rtlb',
                                                     ref=source_ref,
                                                     dim=frame
                                                     )

    rt, tt, lt, bt = coordtools.translate_box_coords(destination_coords,
                                                     in_format=destination_format,
                                                     ref=destination_ref,
                                                     dim=frame
                                                     )

    source_frame = frame[tf:bf, lf:rf]
    destination_frame = frame[tt:bt, lt:rt]
    destination_frame[:] = cv2.resize(source_frame, destination_frame.shape[:2][::-1])


def copy_image_to_frame(frame,
                        image,
                        destination_coords,
                        coord_format='rtlb',
                        ref=None,
                        ):

    rt, tt, lt, bt = coordtools.translate_box_coords(destination_coords,
                                                     in_format=coord_format,
                                                     ref=ref,
                                                     out_format='rtlb',
                                                     dim=frame
                                                     )

    frame_to = frame[tt:bt, lt:rt]
    frame_to[:] = cv2.resize(image, frame_to.shape[:2][::-1])
