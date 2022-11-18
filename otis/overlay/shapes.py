import abc

import cv2

import otis.helpers.coordtools
from otis.helpers import shapefunctions, coordtools
from otis.overlay import bases

class ShapeObject(metaclass=abc.ABCMeta):
    pass


class CircleType(ShapeObject, metaclass=abc.ABCMeta):
    pass


class RectangleType(ShapeObject, metaclass=abc.ABCMeta):
    pass


class LineType(ShapeObject, metaclass=abc.ABCMeta):
    pass


class Circle(bases.Writer, CircleType):
    shape = "circle"

    def __init__(self,
                 center,
                 radius,
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,
                 ):
        super().__init__()
        self.center = center
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref


    def write(self, frame, position=None):
        _center = self.center if position is None else position
        shapefunctions.draw_circle(frame,
                                   _center,
                                   self.radius,
                                   color=self.color,
                                   thickness=self.thickness,
                                   ltype=self.ltype,
                                   ref=self.ref
                                   )


class Rectangle(bases.Writer, RectangleType):
    shape = "rectangle"

    def __init__(self,
                 coords=(100, 100, 30, 30),
                 coord_format='rtlb',
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,
                 dim=None,
                 ):
        super().__init__()

        self.coord_format = coord_format
        self._coords = coordtools.translate_box_coords(coords,
                                                       in_format=coord_format,
                                                       ref=ref,
                                                       dim=dim
                                                       )
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref
        self.dim = dim

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords = coordtools.translate_box_coords(new_coords,
                                                       in_format=self.coord_format,
                                                       ref=self.ref,
                                                       dim=self.dim
                                                       )

    def write(self, frame, coords=None):
        if coords is not None: self.coords = coords
        shapefunctions.draw_rectangle(frame,
                                      self.coords,
                                      color=self.color,
                                      thickness=self.thickness,
                                      ltype=self.ltype,
                                      coord_format='rtlb'
                                      )


class Line(bases.Writer, LineType):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,
                 ltype = None,
                 wtype='ep'  # line type
                 ):

        super().__init__()
        self.color = color
        self.thickness = thickness
        self.reference = None
        self.wtype = wtype
        self.ltype = ltype

    def write(self, frame, *line_data, ref=None, wtype=None, color=None, thickness=None, ltype=None):

        _thickness = self.thickness if thickness is None else thickness
        _color = self.color if color is None else color
        _wtype = self.wtype if wtype is None else wtype
        _ltype = self.ltype if ltype is None else ltype

        if _wtype == 'pal':
            shapefunctions.draw_pal_line(frame, *line_data, color=_color, thickness=_thickness, ref=ref)
        elif _wtype == 'cal':
            shapefunctions.draw_cal_line(frame, *line_data, color=_color, thickness=_thickness, ref=ref)
        else:
            point0 = otis.helpers.coordtools.abs_point(*line_data[0], ref, frame.shape[:2])
            point1 = otis.helpers.coordtools.abs_point(*line_data[1], ref, frame.shape[:2])

            cv2.line(frame, point0, point1, _color, _thickness, _ltype)


class TransparentBackground(bases.Writer, RectangleType):

    def __init__(self, top_right, bottom_left, transparency=.25, ref=None):
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.transparency = transparency
        self.ref = ref

    def write(self, frame):
        shapefunctions.write_transparent_background(frame,
                                                    right_top=self.top_right,
                                                    left_bottom=self.bottom_left,
                                                    transparency=self.transparency,
                                                    ref=self.ref
                                                    )
