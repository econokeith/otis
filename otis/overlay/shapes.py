import cv2
import numpy as np
import abc
from otis.helpers import shapefunctions, coordtools
from otis.overlay import bases
from otis.overlay.bases import CircleType, RectangleType, LineType


class ShapeAsset(bases.Writer, abc.ABC):

    def __init__(self,
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,
                 dim=None,
                 coord_format='rtlb',
                 update_format='None'):
        super().__init__()

        self._coords = np.zeros(4, dtype=int)
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref
        self.dim = dim
        self.update_format = update_format
        self.coord_format = coord_format

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = coordtools.translate_box_coords(new_coords,
                                                          in_format=self.update_format,
                                                          out_format=self.coord_format
                                                          )


    @property
    @abc.abstractmethod
    def center(self):
        pass


    @center.setter
    @abc.abstractmethod
    def center(self, new_center):
        pass


class Circle(ShapeAsset, CircleType):

    def __init__(self,
                 center,
                 radius,
                 *args,
                 radius_type='inner',
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)

        self._coords[:2] = center
        self._coords[2:] = radius
        self.coord_format = 'cwh'
        self.radius_type = radius_type
        self.radius = radius
        self.center = center

    @property
    def coords(self):
        return super().coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = coordtools.find_center_radius_from_box_coords(new_coords,
                                                                        box_format=self.update_format,
                                                                        radius_type=self.radius_type
                                                                        )

    @property
    def radius(self):
        return self._coords[2]

    @radius.setter
    def radius(self, new_radius):
        self._coords[2] = self._coords[3] = new_radius

    @property
    def center(self):
        return self._coords[:2]

    @center.setter
    def center(self, new_center):
        self._coords[:2] = new_center

    def write(self, frame, center=None, radius=None):

        if center is not None: self.center = center
        if radius is not None: self.radius = radius

        shapefunctions.draw_circle(frame,
                                   self.center,
                                   self.radius,
                                   color=self.color,
                                   thickness=self.thickness,
                                   ltype=self.ltype,
                                   ref=self.ref,
                                   )


class Rectangle(ShapeAsset, RectangleType):
    shape = "rectangle"

    def __init__(self,
                 coords,
                 *args,
                 **kwargs,
                 ):

        super().__init__(*args,**kwargs)
        self._coords[:] = coords

    @property
    def center(self):
        cx, cy, _, _ = coordtools.translate_box_coords(self.coords, self.coord_format, 'cwh')
        return cx, cy

    @center.setter
    def center(self, new_center):
        pass

    def write(self, frame, coords=None):

        if coords is not None: self.coords = coords

        shapefunctions.draw_rectangle(frame,
                                      self.coords,
                                      color=self.color,
                                      thickness=self.thickness,
                                      ltype=self.ltype,
                                      coord_format=self.coord_format,
                                      ref=self.ref,
                                      )


class Line(bases.Writer, LineType):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,
                 ltype=None,
                 line_format='ep'  # line type
                 ):

        super().__init__()
        self.color = color
        self.thickness = thickness
        self.reference = None
        self.line_format = line_format
        self.ltype = ltype

    def write(self, frame, *line_data, ref=None, wtype=None, color=None, thickness=None, ltype=None):

        _thickness = self.thickness if thickness is None else thickness
        _color = self.color if color is None else color
        _wtype = self.line_format if wtype is None else wtype
        _ltype = self.ltype if ltype is None else ltype

        if _wtype == 'pal':
            shapefunctions.draw_pal_line(frame, *line_data, color=_color, thickness=_thickness, ref=ref)
        elif _wtype == 'cal':
            shapefunctions.draw_cal_line(frame, *line_data, color=_color, thickness=_thickness, ref=ref)
        else:
            point0 = coordtools.abs_point(*line_data[0], ref, frame.shape[:2])
            point1 = coordtools.abs_point(*line_data[1], ref, frame.shape[:2])

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
