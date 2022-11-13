"""
Writer is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical Writer/subclass
objects
"""
import copy
import robocam.helpers.colortools as ctools

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
            self._color = ctools.COLOR_HASH[new_color]
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

