"""
AssetWriter is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical AssetWriter/subclass
objects
"""
import abc
import copy
from otis.helpers import colortools
from otis.helpers import cvtools
# TODO: Consider adding the functionality with abs_point to base
class AssetWriter:

    @classmethod
    def make_list(cls, n_writers, *args, **kwargs):
        return [cls(*args, **kwargs) for _ in range(n_writers)]

    def __init__(self,*args, **kwargs,
                 # color='r',
                 # thickness=1,
                 # ltype=None,
                 # ref = None,
                 # c_dim = None
                 ):
        """
        AssetWriter is basically just a fancy mixin to add the class method
        cls().make_list which instantiates a list of identical AssetWriter/subclass
        objects. It also defines mass and velocity for the purposes of collision tracking
        """
        self.velocity = (0, 0)
        self.mass = None
        self._color = (0,0,0)
        # self.thickness = thickness
        # self.ltype = ltype
        # self.ref = ref
        # self.c_dim = c_dim

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, new_color):
        if isinstance(new_color, str):
            self._color = colortools.COLOR_HASH[new_color]
        else:
            self._color = new_color

    def copy(self, make_list_of =None):
        if make_list_of is None:
            return copy.deepcopy(self)
        else:
            list_of_copies = [self]
            for _ in range(make_list_of-1):
                list_of_copies.append(self.copy())
            return list_of_copies


class ShapeObject(metaclass=abc.ABCMeta):
    _asset_shape = None

    @classmethod
    @property
    def asset_shape(cls):
        return cls._asset_shape


class CircleType(ShapeObject, metaclass=abc.ABCMeta):
    _asset_shape = 'circle'
    pass


class RectangleType(ShapeObject, metaclass=abc.ABCMeta):
    _asset_shape = 'rectangle'
    pass


class LineType(ShapeObject, metaclass=abc.ABCMeta):
    _asset_shape = 'text'
    pass


class AssetHolderMixin:
    """
    mixin to access asset properties from an asset holder
    """

    @property
    def asset_shape(self):
        return self.asset.asset_shape

    @property
    def coords(self):
        return self.asset._coords

    @coords.setter
    def coords(self, new_coords):
        self.asset._coords = new_coords

    @property
    def center(self):
        return self.asset.center

    @center.setter
    def center(self, new_center):
        self.asset.center = new_center

    @property
    def collisions(self):
        return self.asset.collisions

    @collisions.setter
    def collisions(self, new_col):
        self.asset.collisions = new_col

    @property
    def color(self):
        return self.asset.color

    @color.setter
    def color(self, new_color):
        self.asset.color = new_color

    @property
    def radius(self):
        return self.asset.radius

    @property
    def height(self):
        return self.asset.height

    @property
    def width(self):
        return self.asset.width

    @property
    def coord_format(self):
        return self.asset.coord_format

    @coord_format.setter
    def coord_format(self, new_format):
        self.asset.coord_format = new_format

    def center_width_height(self):
        return self.asset.center_width_height()


if __name__ == '__main__':

    print(cvtools.get_current_dir(__file__))
    print(cvtools.abs_path_relative_to_calling_file('photo_assets'))
    print(cvtools.test_fun())


