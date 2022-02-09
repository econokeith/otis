"""
overlay groups are made here still working on this one, but i need some way to moving around and controlling multiple
writers at once
"""
import abc
from robocam.helpers import utilities as utils

class OverlayGroup(abc.ABC):

    @abc.abstractmethod
    def __init__(self,
                 position,
                 shared_data_object=None,
                 parser_args=None,
                 overlay_data_hash=None,
                 ref=None):
        """
        base class for overlay groups.

        :param position:
        :param shared_data_object:
        :param overlay_data_hash:
        :param parser_args:
        :param ref:

        subclass inits should have the followoing form

        class SystemsInfoWriter(OverlayGroup):

        def __init__(self,
                    position,
                    shared_data_object,
                    parser_args=None
                    overlay_data_hash=None,
                    ref = None
                    )
            super().__init__(position, shared,..., ref)
            self.writer1 = Writer(..., position=pos1,..., ref=self.position)
            self.writer2 = Writer(..., position=pos2,..., ref=self.position)
            self.writer2.func = lambda: True

        def write(self, frame):
            self.writer1.write(frame)
            self.writer2.write_fun(frame, *args, **kwargs)
            ...
            other stuff
            ...
            etc

        """

        self.shared = shared_data_object
        self.pargs = parser_args
        self.ohash = overlay_data_hash
        self.ref = ref
        self.position = utils.abs_point(position, ref)

    @abc.abstractmethod
    def write(self, frame):
        #put all the writers here
        #and here
        #and here
        pass