import cv2
import numpy as np
import abc
from otis.helpers import shapefunctions, coordtools
from otis.overlay import bases
from otis.overlay.bases import CircleType, RectangleType, LineType


class ShapeAsset(bases.AssetWriter, abc.ABC):


    def __init__(self,
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,
                 dim=None,
                 coord_format='rtlb',
                 update_format=None,
                 collisions = False,
                 ):

        super().__init__()

        self._coords = np.zeros(4, dtype=int)
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.ref = ref
        self.dim = dim
        self.coord_format = coord_format
        self.update_format = coord_format if update_format is None else update_format
        self.collisions = collisions

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
    def center(self):
        pass

    @center.setter
    def center(self, new_center):
        pass

    def center_width_height(self):
        return coordtools.translate_box_coords(self._coords, self.coord_format, 'cwh')


class Circle(ShapeAsset, CircleType):
    shape = 'circle'
    def __init__(self,
                 center,
                 radius,
                 radius_type='inner',
                 **kwargs
                 ):
        """

        Args:
            center:
            radius:
            *args:
            radius_type:
            **kwargs:
        """
        ShapeAsset.__init__(self, **kwargs)

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

    def write(self, frame, center=None, radius=None, color=None, ref=None, save=False):
        """
        :type frame: np.array
        """
        _center = self.center if center is None else center
        _radius = self.radius if radius is None else radius
        _color = self.color if color is None else color
        _ref = self.ref if ref is None else ref

        if save is True:
            self.center = _center
            self.radius = _radius
            self.color = _color
            self.ref = _ref

        shapefunctions.draw_circle(frame,
                                   _center,
                                   _radius,
                                   color=_color,
                                   thickness=self.thickness,
                                   ltype=self.ltype,
                                   ref=_ref,
                                   )


# todo: need to think of a way to efficiently update center and find height/width

class Rectangle(ShapeAsset, RectangleType):
    shape = "rectangle"

    def __init__(self,
                 coords=(0,0,0,0),
                 **kwargs,
                 ):

        ShapeAsset.__init__(self, **kwargs)
        self._coords[:] = coords

    @property
    def center(self):
        cx, cy, _, _ = coordtools.translate_box_coords(self.coords,
                                                       in_format=self.coord_format,
                                                       out_format='cwh'
                                                       )
        return cx, cy

    @center.setter
    def center(self, new_center):
        # find the center, width, and height
        cy, cx, w, h = coordtools.translate_box_coords(self.coords,
                                                       in_format=self.coord_format,
                                                       out_format='cwh'
                                                       )
        cy_new, cx_new = new_center
        # change the center and then convert back to appropriate format
        self._coords[:] = coordtools.translate_box_coords((cx_new, cy_new, w, h),
                                                          in_format='cwh',
                                                          out_format=self.coord_format
                                                          )

    def write(self, frame, coords=None, color=None, ref=None, save=False):
        """
        :type frame: np.array
        """

        _coords = self.coords if coords is None else coords
        _color = self.color if color is None else color
        _ref = self.ref if ref is None else ref

        if save is True:

            self.coords = _coords
            self.color = _color
            self.ref = _ref

        shapefunctions.draw_rectangle(frame,
                                      _coords,
                                      color=_color,
                                      thickness=self.thickness,
                                      ltype=self.ltype,
                                      coord_format=self.coord_format,
                                      ref=_ref,
                                      )

class Line(bases.AssetWriter, LineType):

    def __init__(self,
                 coords = (0, 0, 0, 0),
                 color = 'r',
                 thickness=2,
                 ltype=None,
                 coord_format='points',# points (x1, y1, x2, y2), 'pal': (x1, y1, angle, length), 'cal' center angle length
                 ref=None,
                 dim=None
                 ):

        super().__init__()

        self._coords = np.array(coords)
        self.color = color
        self.thickness = thickness
        self.ltype = ltype
        self.coord_format = coord_format
        self.ref = ref
        self.dim = dim

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = new_coords

    def write(self, frame, coords=None, color=None, ref=None, save=False):

        _coords = self.coords if coords is None else coords
        _color = self.color if color is None else color
        _ref = self.ref if ref is None else ref

        if save is True:

            self.coords = _coords
            self.color = _color
            self.ref = _ref

        # depending on the line coord format, choose a different drawing function
        if self.coord_format == 'pal':
            shapefunctions.draw_pal_line(frame, _coords[:2], _coords[2], _coords[3],
                                         color=_color, thickness=self.thickness, ltype=self.ltype, ref=_ref)
        elif self.coord_format == 'cal':
            shapefunctions.draw_cal_line(frame, _coords[:2], _coords[2], _coords[3],
                                         color=_color, thickness=self.thickness, ltype=self.ltype, ref=_ref)
        else:
            point0 = coordtools.abs_point(_coords[:2], ref, frame)
            point1 = coordtools.abs_point(_coords[2:], ref, frame)

            cv2.line(frame, point0, point1, _color, self.thickness, self.ltype)


class TransparentBackground(RectangleType):

    def __init__(self,
                 coords=(0, 0, 0, 0),
                 transparency=.25,
                 coord_format= 'rtlb',
                 ref=None):

        super().__init__()
        self.coords = coords
        self.transparency = transparency
        self.coord_format = coord_format
        self.ref = ref

    def write(self, frame):
        shapefunctions.write_transparent_background(frame,
                                                    coords=self.coords,
                                                    coord_format=self.coord_format,
                                                    transparency=self.transparency,
                                                    ref=self.ref
                                                    )
