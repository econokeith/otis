"""
Writer is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical Writer/subclass
objects
"""
import copy
import robocam.overlay.colortools as ctools

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
            self._color = ctools.color_hash[new_color]
        else:
            self._color = new_color

    def copy(self):
        return copy.deepcopy(self)