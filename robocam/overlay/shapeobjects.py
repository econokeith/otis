import cv2

from robocam.helpers import utilities as utilities
from robocam.overlay import bases, shapefunctions


class Circle(bases.Writer):
    shape = "circle"

    def __init__(self,
                 position,
                 radius,
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,

                 ):

        super().__init__()
        self.position = position
        self.radius = radius
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref


    @property
    def center(self):
        return self.position

    def write(self, frame, position=None):
        _center = self.position if position is None else position
        shapefunctions.draw_circle(frame, _center, self.radius, color=self.color, thickness=self.thickness, ref=self.ref)


class Rectangle(bases.Writer):
    shape = "rectangle"

    def __init__(self,
                 coords = (100, 100, 30, 30),
                 coord_format = 'points',
                   color='r',
                   thickness=1,
                   ltype=None,
                   ref=None
                    ):

        super().__init__()


        self.coord_format = coord_format
        self.coords = self.__translate_coords(coords)
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref

    def __translate_coords(self, coords):

        if self.coord_format == 'points':
            return coords

        elif self.coord_format == 'ltwh':
            l, t, w, h = coords
            b = t+h
            r = l+h

        elif self.coord_format == 'cwh':

            cx, cy, w, h = coords
            t = cy - h/2
            b = t + h
            l = cx - w/2
            r = l + w

        elif self.coord_format == 'lbwh':
            l, b, w, h = coords
            t = b - h
            r = l + w

        else:
            raise ValueError("invalid coord format")

        return t, r, b, l

    def write(self, coords=None):
        _coords = coords if coords is not None else self.coords
        t, r, b, l = self.__translate_coords(_coords)


class Line(bases.Writer):

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
            shapefunctions.draw_pal_line(frame, *args, color=_color, thickness=_thickness, ref=ref)
        elif _wtype == 'cal':
            shapefunctions.draw_cal_line(frame, *args, color=_color, thickness=_thickness, ref=ref)
        else:
            point0 = utilities.abs_point(*args[0], ref, frame.shape[:2])
            point1 = utilities.abs_point(*args[1], ref, frame.shape[:2])

            cv2.line(frame, point0, point1, _color, _thickness)


class TransparentBackground(bases.Writer):

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
