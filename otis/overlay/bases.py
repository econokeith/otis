"""
AssetWriter is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical AssetWriter/subclass
objects
"""
import abc
import copy
from otis.helpers import colortools
from otis.helpers import cvtools
# TODO: adding the functionality with abs_point to base
class AssetWriter:

    @classmethod
    def make_list(cls, n_writers, *args, **kwargs):
        return [cls(*args, **kwargs) for _ in range(n_writers)]

    def __init__(self,*args, **kwargs,
                 # color='r',
                 # thickness=1,
                 # ltype=None,
                 # ref = None,
                 # dim = None
                 ):
        """
        AssetWriter is basically just a fancy mixin to add the class method
        cls().make_list which instantiates a list of identical AssetWriter/subclass
        objects
        """

        self._color = (0,0,0)
        # self.thickness = thickness
        # self.ltype = ltype
        # self.ref = ref
        # self.dim = dim

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



if __name__ == '__main__':
    print(cvtools.get_current_dir(__file__))
    print(cvtools.abs_path_relative_to_calling_file('../examples/balls.py'))


class ShapeObject(metaclass=abc.ABCMeta):
    pass


class CircleType(ShapeObject, metaclass=abc.ABCMeta):
    pass


class RectangleType(ShapeObject, metaclass=abc.ABCMeta):
    pass


class LineType(ShapeObject, metaclass=abc.ABCMeta):
    pass
