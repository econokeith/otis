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
        self._name = name
        self._time_to_inactive_0 = .1
        self._time_to_inactive_1 = time_to_inactive
        self.time_since_last_observed = timers.TimeSinceFirst()
        self.time_since_active = timers.TimeSinceFirst()
        self.i_am_new = True
        self._is_active = False
        self._updates_since_inactive = 0
        self._min_updates_until_active = 8

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
    def time_to_inactive(self):
        if self._is_active:
            return self._time_to_inactive_1
        else:
            return self._time_to_inactive_0

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_name):
        self._name = new_name
        self.name_tag.name = new_name

    @property
    def is_active(self):
        if self._is_active is False and self._updates_since_inactive >= self._min_updates_until_active:
            self._is_active = True
            self.time_since_active = timers.TimeSinceFirst().start()

        elif self._is_active is False and self.time_since_last_observed() > self.time_to_inactive:
            self._updates_since_inactive = 0

        elif self._is_active is True and self.time_since_last_observed() > self.time_to_inactive:
            self._is_active = False
            self._updates_since_inactive = 0

        return self._is_active

    @property
    def coords(self):
        return self.asset._coords

    @coords.setter
    def coords(self, new_coords):
        self.asset.coords = new_coords
        time_since = self.time_since_last_observed()
        if time_since > self.time_to_inactive:
            self._updates_since_inactive = 1
        else:
            self._updates_since_inactive += 1
        self.time_since_last_observed.reset(True)


    def write(self, frame):
        if self.show_self is True:
            self.asset.write(frame)

        if self.show_name is True:
            self.name_tag.write(frame)

class BoundingManager:

    def __init__(self,
                 manager,
                 threshold=.1,
                 ):

        self.manager = manager
        self.shared = manager.shared
        self.args = manager.pargs
        self.capture = self.manager.capture
        self.threshold = threshold
        self.color_cycle = colortools.ColorCycle()

        self.bbox_coords = np.array(self.shared.bbox_coords)

        self.base_asset = shapes.Rectangle(coords=(80, 0, 0, 80),
                                           color=None,
                                           lock_dimensions=False,
                                           update_format='trbl'
                                           )

        self.box_fun = lambda: BoundingAsset(self.base_asset,
                                             color=self.color_cycle(),
                                             show_name=True
                                             )

        self.bbox_hash = defaultdict(self.box_fun)

        self.is_updated = True
        self.flash_event = False

        self.frame = np.zeros((self.args.dim[1], self.args.dim[0], 3), dtype='uint8')
        self._primary_target = None
        self.primary_timer_range = [5, 20]
        self.time_for_new_primary = timers.TimeElapsedBool()
        self.n_faces = 0
        self.name_tracker = self.manager.name_tracker

        self.n_boxes_active = 0

        self.n_boxes_active = 0
        self.active_names = []

    @property
    def primary_target(self):
        return self._primary_target

    @primary_target.setter
    def primary_target(self, new_target):
        if new_target != self.primary_target:
            self._primary_target = new_target
            self.time_for_new_primary = timers.TimeElapsedBool(np.random.randint(*self.primary_timer_range))


    def make_new_bounder(self, name=None):
        new_asset = copy.deepcopy(self.base_asset)
        new_asset.name = name
        new_asset.color = self.color_cycle

    def loop(self, frame):

        shared = self.shared

        active_names = []
        # update scene data if new data from cv_process
        if shared.new_overlay.value:
            self.n_faces = self.shared.n_observed_faces.value
            self.bbox_coords = shared.bbox_coords.copy()
            self.names = [self.name_tracker[name] for name in shared.observed_names[:self.n_faces]]

        # update boxes and print unknowns because we are only using one box to print all unknowns
            for i, name in enumerate(self.names):
                box = self.bbox_hash[name]
                box.name = name
                box.coords = self.bbox_coords[i]
                if name == 'unknown':
                    box.write(frame)

        self.n_boxes_active = 0
        self.active_names = []

        # print all actives - there is only 1 unknown box so it would only print one unknown we didn't do the last step
        for box in self.bbox_hash.values():
            if box.is_active is True:
                self.n_boxes_active +=1
                self.active_names.append(box.name)
                box.write(frame)
                active_names.append(box.name)

        if self.n_boxes_active == 0:
            self.primary_target == None

        elif self.n_boxes_active == 1:
            self.primary_target = active_names[0]

        elif self.primary_target not in self.active_names:
            names = np.array(self.active_names)
            if active_names.count('unknown')>1:
                names = names[(names!='unknown')]
            self.primary_target = names[np.random.choice(len(names))]

        elif self.time_for_new_primary() is True:
            names = np.array(self.active_names)
            names = names[(names != self.primary_target)]

            if active_names.count('unknown')>1:
                names = names[(names!='unknown')]

            self.primary_target = names[np.random.choice(len(names))]

        else:
            pass

        self.n_boxes_active = self.n_boxes_active
        self.active_names = self.active_names

        shared.n_boxes_active.value = self.n_boxes_active

        if self.args.servo is True:

            if self.n_boxes_active > 0:
                servo_target = self.bbox_hash[self.primary_target].center

            else:
                servo_target = self.args.video_center

            self.shared.servo_target[:] = servo_target







