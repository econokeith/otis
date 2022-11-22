import copy
import abc
from collections import defaultdict

import numpy as np

from otis.overlay import bases, shapes, textwriters, assets

from otis.helpers import coordtools, timers, colortools


class BoundingAsset(bases.AssetHolderMixin):

    def __init__(self,
                 asset,
                 name=None,
                 name_tagger=None,
                 show_name=True,
                 show_self=True,
                 time_to_inactive=1,
                 color='r'
                 ):
        """
        Bounding asset functionality to shape assets for use in displaying bounding objects
        Args:
            color:
            name:
            name_tagger:
            show_name:
            show_self:
            coord_format:
            thickness:
            ltype:
        """

        self.asset = copy.deepcopy(asset)
        self.asset.color = color
        self.last_coords = self.coords.copy()
        self.show_name = show_name
        self.show_self = show_self
        self.name = name
        self.time_to_inactive = time_to_inactive
        self.time_since_last_observed = timers.TimeSinceLast()

        # setup NameTag object
        if name_tagger is None:
            self.name_tag = textwriters.NameTag(name=name,
                                                attached_to=self)
        else:
            assert isinstance(name_tagger, textwriters.NameTag)
            if self.name_tag.attached_to is not None:
                self.name_tag.attached_to = None
            self.name_tag = copy.deepcopy(name_tagger)
            self.name_tag.attached_to = self

    @property
    def is_active(self):
        #todo: will boundingobject.is_active cause problems later
        if self.time_since_last_observed() < self.time_to_inactive:
            return True
        else:
            return False

    @property
    def coords(self):
        return self.asset.coords

    @coords.setter
    def coords(self, new_coords):
        self.asset.coords = new_coords
        self.time_since_last_observed()

    def write(self, frame):
        if self.show_self is True:
            self.asset.write(frame)

        if self.show_name is True:
            self.name_tag.write(frame)

class BoundingManager:

    def __init__(self, manager, threshold=.1):

        self.manager = manager
        self.shared = manager.shared
        self.args = manager.pargs
        self.capture = self.manager.capture
        self.threshold = threshold
        self.color_cycle = colortools.ColorCycle()

        self.bbox_coords = np.array(self.shared.bbox_coords)

        self.base_asset = shapes.Rectangle(coords=(80, 0, 0, 80),
                                           color=None,
                                           lock_dimensions=True
                                           )

        self.box_fun = lambda: BoundingAsset(self.base_asset,
                                             color=self.color_cycle()
                                             )

        self.bbox_hash = defaultdict(self.box_fun)

        self.is_updated = True
        self.flash_event = False

        self.frame = np.zeros((self.args.dim[1], self.args.dim[0], 3), dtype='uint8')


    def make_new_bounder(self, name=None):
        new_asset = copy.deepcopy(self.base_asset)
        new_asset.name = name
        new_asset.color = self.color_cycle

    def loop(self, frame):

        shared = self.shared
        bbox_hash = self.bbox_hash
        tracker = self.manager.name_tracker
        # cache this stuff to avoid overwrites in the middle
        # only update
        if shared.new_overlay.value:

            bbox_coords = shared.bbox_coords.copy()
            n_faces = self.shared.n_faces.value
            self.names = [tracker[name] for name in shared.names[:n_faces]]

            for i, name in enumerate(self.names):
                box = bbox_hash[name]
                box.name = name
                box.coords = bbox_coords[i]

            for box in bbox_hash.values():
                if box.is_active is True:
                    box.write(frame)


