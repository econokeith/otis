import signal
import sys
import time
import os
from collections import defaultdict
from queue import Queue

import numpy as np

from robocam.helpers.cvtools import box_stabilizer

from robocam import camera
from robocam.helpers import multitools as mtools, utilities as utils, timers
from robocam.overlay import screenevents as events, textwriters as writers, assets, groups, motion, shapes

MAX_FPS = 30
DIMENSIONS = DX, DY = (1920, 1080)
RECORD = False
RECORD_SCALE = .5
MAX_BALLS = 4
BALL_FREQUENCY = [3, 3]
# RADIUS_BOUNDS = [5, 30]
BALL_V_ANGLE_BOUNDS = [10, 80]
BALL_V_MAGNI_BOUNDS = [300, 1000]
STARTING_LOCATION = [200, DY - 200]
# NEG_MASS = False
COLLISIONS = True
BORDER = True
# pie_path= '/home/keith/Projects/robocam/robocam/overlay/photo_assets/pie_asset'
pie_path = 'photo_asset_files/pie_asset'
face_path = 'faces'

MA = 30

NUMBER_OF_PLAYERS = 1
PLAYER_NAMES = ["Keith"]


def target(shared, args):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    capture = camera.ThreadedCameraPlayer(0,
                                          max_fps=args.max_fps,
                                          dim=args.dim,
                                          flip=False,
                                          record=RECORD
                                          ).start()

    manager = SceneManager(shared, args, capture=capture)
    bouncy_scene = BouncyScene(manager, shared, args)

    info_group = InfoGroup((10, 40), shared, args)
    #score_keeper = ScoreKeeper((10, 200), shared, args)

    while True:

        capture.read()

        shared.frame[:] = frame = capture.frame  # latest frame to shared frame
        bouncy_scene.loop(frame)
        info_group.write(frame)

        capture.show(frame)

        if utils.cv2waitkey() is True:
            break

    capture.stop()
    sys.exit()


#######################################################################################################################
#######################################################################################################################
#######################################################################################################################

class SceneManager:

    def __init__(self, shared, args, capture=None):

        self.shared = shared
        self.args = args
        self.name_tracker = NameTracker()

        if capture is None:
            self.capture = camera.ThreadedCameraPlayer(0,
                                                       max_fps=args.max_fps,
                                                       dim=args.dim,
                                                       scale=args.scale,
                                                       flip=True

                                                       ).start()
        else:
            self.capture = capture

        self.scene_number = 0


class BouncyScene:

    def __init__(self, manager, shared, args):
        self.manager = manager
        self.shared = shared
        self.args = args
        self.capture = self.manager.capture

        self.bouncy_pies = motion.BouncingAssetManager(asset_fun=pie_path,
                                                       max_fps=args.max_fps,
                                                       dim=args.dim,
                                                       max_balls=MAX_BALLS,
                                                       collisions=COLLISIONS
                                                       )

        time.sleep(3)

        self.collision_detector = motion.CollisionDetector(.3)
        self.screen_flash = events.ColorFlash(max_ups=args.max_fps,
                                              cycle_t=.5,
                                              direction=-1)

        self.score_keeper = ScoreKeeper((10, 200), shared, args)



        BBoxes = []
        self.bbox_coords = np.array(shared.bbox_coords)

        for i in range(args.faces):
            box = assets.BoundingCircle(which_radius='inside_min')
            box.coords = self.bbox_coords[i, :]  # reference a line in teh shared array
            BBoxes.append(box)

        self.BBoxes = BBoxes
        self.is_updated = True
        self.flash_event = False
        self.frame = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')

    def loop(self, frame):

        shared = self.shared
        BBoxes = self.BBoxes

        # cache this stuff to avoid overwrites in the middle
        # only update
        if shared.new_overlay.value:
            old_coords = self.bbox_coords
            bbox_coords = np.array(shared.bbox_coords)
            names = np.array(shared.names)

            for i in range(shared.n_faces.value):
                self.bbox_coords[i] = box_stabilizer(old_coords[i], bbox_coords[i], .1)
                BBoxes[i].coords = self.bbox_coords[i]
                BBoxes[i].name = self.manager.name_tracker[names[i]]

        for i in range(shared.n_faces.value):
            BBoxes[i].write(frame)

        if self.flash_event is True:
            self.screen_flash.loop(frame)
            if self.screen_flash.complete:
                self.screen_flash.reset()
                self.flash_event = False

        if self.score_keeper.timer_finished is False:

            self.bouncy_pies.move(frame)

            for i, pie in enumerate(self.bouncy_pies.movers):
                for i in range(shared.n_faces.value):
                    if self.collision_detector.check(BBoxes[i], pie) is True and self.flash_event is False:
                        self.flash_event = True
                        self.score_keeper.score += 1
                        break

        self.score_keeper.write(frame)


class InfoGroup(groups.AssetGroup):

    def __init__(self, position, shared, args):
        super().__init__(position)
        self.scale = .75
        self.color = 'g'
        self.shared = shared
        self.args = args

        fps_writer = writers.TimerWriter(title="screen fps",
                                         timer_type='last',
                                         position=(0, 0),
                                         roundw=0,
                                         per_second=True,
                                         moving_average=MA,
                                         scale=self.scale,
                                         color=self.color,
                                         )

        self.model_ma = utils.MovingAverage(MA)

        ma_text_fun = lambda: f'model updates per second : {int(1 / self.model_ma.update(shared.m_time.value))}'
        model_writer = writers.InfoWriter(text_fun=ma_text_fun,
                                          position=(0, -30),
                                          scale=self.scale,
                                          color=self.color,
                                          )

        self.add([model_writer, fps_writer])


class ScoreKeeper(groups.AssetGroup):

    def __init__(self, position, shared, args):
        super().__init__(position)
        self.scale = 1.25
        self.color = 'w'
        self.shared = shared
        self.args = args
        self._score = 0


        self.time_writer = writers.TimerWriter(title="Time",
                                              timer_type='countdown',
                                              position=(0, -50),
                                              roundw=0,
                                              per_second=True,
                                              moving_average=MA,
                                              scale=self.scale,
                                              color=self.color,
                                              count_from=20,
                                              )

        score_writer = writers.InfoWriter(text_fun= lambda: f'Keith : {self.score}',
                                          position=(0, -100),
                                          scale=self.scale,
                                          color=self.color,
                                          )

        self.add([self.time_writer, score_writer])

    def write(self, frame):
        shapes.transparent_background(frame, (200, 0), (0, -250), ref=self.position, transparency=.5)
        super().write(frame)

    @property
    def timer_finished(self):
        return self.time_writer.timer_finished

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, new_score):
        if not self.timer_finished:
            self._score = new_score


class NameTracker:

    def __init__(self):

        self._last_seen_timers = []
        self.known_names = []
        self.n_known = 0
        self.loads_names()
        self.indices_of_observed = []
        self.unknown_count = 0
        self.name_for_unknowns = "unknown"
        self.primary = 0
        self.hello_queue = Queue()

        # help keep from having random 1 frame bad calls triggering hellos
        # someone must show up in 5 frames in 1 second to get a hello
        _bad_hello_function = lambda: [timers.TimeSinceFirst().start(), 0]
        self._bad_hello_dict = defaultdict(_bad_hello_function)

    def loads_names(self):
        # this  might have to change
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        face_folder = os.path.join(abs_dir, 'photo_assets/faces')
        face_files = os.listdir(face_folder)

        for file in face_files:
            name = ""
            for char in file:
                if char.isdigit() or char in ('.', '-'):
                    break
                else:
                    name += char

            # if name isn't new, add it to the list.
            if name not in self.known_names:
                self.known_names.append(name)
                self._last_seen_timers.append(timers.TimeSinceLast())
            # append name
            # set timers for each know
        self.n_known = len(self.known_names)

    def __getitem__(self, i):

        if i < self.n_known:
            # if it's a new known person
            if i not in self.indices_of_observed:
                timer, count = self._bad_hello_dict[i]
                print(timer(), count)

                ## todo: this should not be hardcoded
                if timer() <= 1.5 and count > 10:
                    self.indices_of_observed.append(i)
                    hello = f'Hello {self.known_names[i]}, welcome!'
                    self._last_seen_timers[i]()  # replace this soon
                    self.hello_queue.put((i, hello))
                    # reset timer so it can be used for other things
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

                elif timer() <= 1.5:
                    # count they were seen
                    self._bad_hello_dict[i][1] += 1

                else:
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

            return self.known_names[i]

        else:
            name = f'Person {i - self.n_known + 1}'
            if i not in self.indices_of_observed:
                # self.indices_of_observed.append(i)
                # self.unknown_count += 1
                hello = f'Hello {name}, do we know each other!'

            return ""
