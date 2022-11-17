"""
Writer is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical Writer/subclass
objects
"""
import copy
from robocam.helpers import colortools
from robocam.helpers import cvtools
# TODO: adding the functionality with abs_point to base
class Writer:

    @classmethod
    def make_list(cls, n_writers, *args, **kwargs):
        return [cls(*args, **kwargs) for _ in range(n_writers)]

    def __init__(self, *args, **kwargs):
        """
        Writer is basically just a fancy mixin to add the class method
        cls().make_list which instantiates a list of identical Writer/subclass
        objects
        """

        self._color = (0,0,0)

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

