import copy
import abc
from collections import defaultdict
import numpy as np
from otis.overlay import bases, shapes, textwriters, assets
from otis.helpers import coordtools, timers, colortools, maths


class BoundingAsset(bases.AssetHolderMixin, bases.AssetWriter):

    def __init__(self,
                 asset,
                 name=None,
                 name_tagger=None,
                 show_name=True,
                 show_self=True,
                 time_to_inactive=1,
                 color='r',
                 moving_average = None,
                 scale = 1,
                 ):
        super().__init__()
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
        self._time_to_inactive_0 = .2 # how long it takes to for a box to go inactive after not being observed if not yet active
        self._time_to_inactive_1 = time_to_inactive # same but longer cause it's for active boxes
        self.time_since_last_observed = timers.TimeSinceFirst().start()
        self.time_since_active = timers.TimeSinceFirst()
        self.i_am_new = True
        self._is_active = False # becomes active if updates >= min_updates until active
        self._updates_since_inactive = 0 # number of updates
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

        if moving_average is not None:
            self.moving_average = BoxMovingAverage(*moving_average,
                                                   in_format=self.asset.update_format,
                                                   out_format=self.asset.update_format,
                                                   scale=scale
                                                   )
        else:
            self.moving_average = None

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
            self.time_since_active.reset(True)
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
        if self.moving_average is not None:
            self.asset.coords = self.moving_average.update_coords(new_coords)
        else:
            self.asset.coords = new_coords

        if self.is_active is False and self.time_since_last_observed() > self.time_to_inactive:
            self._updates_since_inactive = 1
        elif self.is_active is False:
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
                 base_asset = None,
                 moving_average=None,
                 scale=1
                 ):


        self.manager = manager
        self.shared = manager.shared
        self.args = manager.pargs
        self.capture = self.manager.capture
        self.threshold = threshold
        self.color_cycle = colortools.ColorCycle()

        self.bbox_coords = np.array(self.shared.bbox_coords)

        if base_asset is None:
            self.base_asset = shapes.Circle(center=(0,0),
                                            radius=100,
                                            color=None,
                                            lock_dimensions=False,
                                            update_format='trbl',
                                            )
        else:
            self.base_asset = base_asset

        self.box_fun = lambda: BoundingAsset(self.base_asset,
                                             color=self.color_cycle(),
                                             show_name=True,
                                             moving_average = moving_average,
                                             scale=scale,
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
        self.active_names = []

    @property
    def primary_target(self):
        return self._primary_target

    @primary_target.setter
    def primary_target(self, new_target):
        if new_target != self.primary_target:
            self._primary_target = new_target
            self.time_for_new_primary = timers.TimeElapsedBool(np.random.randint(*self.primary_timer_range))

    @property
    def primary_box(self):
        if self.primary_target is not None:
            return self.bbox_hash[self.primary_target]
        else:
            return None

    def make_new_bounder(self, name=None):
        new_asset = copy.deepcopy(self.base_asset)
        new_asset.name = name
        new_asset.color = self.color_cycle

    def update_boxes(self):

        shared = self.shared
        # update scene data if new data from cv_process
        if shared.new_overlay.value:
            self.n_faces = self.shared.n_observed_faces.value
            self.bbox_coords[:,:] = shared.bbox_coords
            observed_names = [self.name_tracker[name] for name in shared.observed_names[:self.n_faces]]

        # update boxes and print unknowns because we are only using one box to print all unknowns
            self.observed_names = []
            for i, name in enumerate(observed_names):
                if name != 'unknown' and name != '':
                    box = self.bbox_hash[name]
                    box.name = name
                    box.coords = self.bbox_coords[i]
                    self.observed_names.append(name)


        self.active_names = []
        self.n_boxes_active = 0

        for box in self.bbox_hash.values():
            if box.is_active is True:
                self.n_boxes_active += 1
                self.active_names.append(box.name)
                # if box.name != 'Keith':
                #     print(box.name, 1000*box.time_since_last_observed()//1, box.is_active, box._updates_since_inactive)

        self.shared.n_boxes_active.value = self.n_boxes_active

    def write(self, frame):

        for name in self.active_names:
            self.bbox_hash[name].write(frame)

    def update_primary(self):
        # print all actives - there is only 1 unknown box so it would only print one unknown we didn't do the last step
        active_names = self.active_names

        if self.n_boxes_active == 0:
            self.primary_target == None

        elif self.n_boxes_active == 1:
            self.primary_target = active_names[0]

        elif self.primary_target not in self.active_names:
            names = np.array(self.active_names)
            if active_names.count('unknown') > 1:
                names = names[(names != 'unknown')]
            self.primary_target = names[np.random.choice(len(names))]

        elif self.time_for_new_primary() is True:
            names = np.array(self.active_names)
            names = names[(names != self.primary_target)]

            if active_names.count('unknown') > 1:
                names = names[(names != 'unknown')]

            self.primary_target = names[np.random.choice(len(names))]

        self.update_servo()


    def update_servo(self):
        if self.args.servo is True:

            if self.n_boxes_active > 0:
                servo_target = self.bbox_hash[self.primary_target].center

            else:
                servo_target = self.args.video_center

            self.shared.servo_target[:] = servo_target

    def loop(self, frame):
        self.update_boxes()
        self.update_primary()
        self.write(frame)


class BoxMovingAverage:

    def __init__(self, x_ma=None, y_ma=None, h_ma=None, w_ma=None, in_format='cwh', out_format=None, scale=1):

        self.identity_fun = lambda x: x
        # set the moving averages
        if x_ma is not None:
            self.x_ma =  maths.MovingAverage(x_ma)
        else:
            self.x_ma = self.identity_fun

        if y_ma is not None:
            self.y_ma = maths.MovingAverage(y_ma)
        else:
            self.y_ma = self.identity_fun

        if w_ma is not None:
            self.w_ma = maths.MovingAverage(w_ma)
        else:
            self.w_ma = self.identity_fun

        if h_ma is not None:
            self.h_ma = maths.MovingAverage(h_ma)
        else:
            self.h_ma = self.identity_fun

        self.in_format = in_format
        if out_format is not None:
            self.out_format = out_format
        else:
            self.out_format = self.in_format

        self.scale = scale

    def update_coords(self, coords):
        _coords = coordtools.translate_box_coords(coords, in_format=self.in_format, out_format='cwh')
        _coords = list(_coords)
        _coords[3] *= self.scale
        _coords[2] *= self.scale
        moving_averages = [self.x_ma, self.y_ma, self.w_ma, self.h_ma]
        new_coords = []
        for c, ma in zip(_coords, moving_averages):
            new_coords.append(ma(c))

        return coordtools.translate_box_coords(new_coords, in_format='cwh', out_format=self.out_format)
