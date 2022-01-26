"""
Writer is basically just a fancy mixin to add the class method
cls().make_list which instantiates a list of identical Writer/subclass
objects
"""
import copy

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
        pass

    def copy(self):
        return copy.deepcopy(self)