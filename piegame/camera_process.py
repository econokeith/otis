import signal
import sys
import time
import os
from collections import defaultdict
from queue import Queue

import numpy as np

from robocam.helpers.cvtools import box_stabilizer

from robocam import camera
from robocam.helpers import multitools as mtools, utilities as utils, timers, cvtools, colortools as ctools
from robocam.overlay import screenevents as events, textwriters as writers, assets, groups, motion, shapes

MAX_FPS = 30
DIMENSIONS = DX, DY = (1920, 1080)
RECORD = False
RECORD_SCALE = .25
OUTPUT_SCALE = 1

MAX_BALLS = 6
BALL_FREQUENCY = [0, 5]
# RADIUS_BOUNDS = [5, 30]
BALL_V_ANGLE_BOUNDS = [10, 80]
BALL_V_MAGNI_BOUNDS = [600, 1000]
STARTING_LOCATION = [200, DY - 200]
COLLISION_OVERLAP = .1
# NEG_MASS = False
COLLISIONS = True
BORDER = True
PIE_SCALE = .8
GAME_TIME = 10
# pie_path= '/home/keith/Projects/robocam/robocam/overlay/photo_assets/pie_asset'
pie_path = 'photo_asset_files/pie_asset'
face_path = 'faces'

MA = 30

NUMBER_OF_PLAYERS = 1
PLAYER_NAMES = ["Keith", "David"]

STOP_AFTER_GAME = False


def target(shared, pargs):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    capture = camera.ThreadedCameraPlayer(0,
                                          max_fps=pargs.max_fps,
                                          dim=pargs.dim,
                                          flip=False,
                                          record=RECORD,
                                          record_to='pie.avi',
                                          output_scale=OUTPUT_SCALE,
                                          record_scale=RECORD_SCALE
                                          ).start()

    manager = SceneManager(shared, pargs, capture=capture)
    bouncy_scene = BouncyScene(manager, shared, pargs)

    info_group = InfoGroup((10, 40), shared, pargs)

    count_down = events.CountDown(pargs.dim, 3)

    while True:
        count_down.loop(show=False)
        capture.show(count_down.frame)

        if count_down.finished is True:
            break

        if utils.cv2waitkey(1) is True:
            break

    stopped = False

    while True:

        check, frame = capture.read()

        shared.frame[:] = frame  # latest frame to shared frame
        stopped = bouncy_scene.loop(frame)
        info_group.write(frame)

        capture.show(frame)

        if stopped is True and STOP_AFTER_GAME is True:
            break

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
        self.name_tracker = cvtools.NameTracker(args.path_to_faces)

        if capture is None:
            self.capture = camera.ThreadedCameraPlayer(0,
                                                       max_fps=args.max_fps,
                                                       dim=args.dim,
                                                       scale=args.output_scale,
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

        self.stop_timer = timers.SinceFirstBool(3)

        self.color_cycle = ctools.ColorCycle()

        self.bouncy_pies = motion.BouncingAssetManager(asset_fun=args.path_to_pies,
                                                       max_fps=args.max_fps,
                                                       dim=args.dim,
                                                       max_balls=MAX_BALLS,
                                                       collisions=COLLISIONS,
                                                       scale = PIE_SCALE,
                                                       )

        self.collision_detector = motion.CollisionDetector(COLLISION_OVERLAP)

        self.screen_flash = events.ColorFlash(max_ups=args.max_fps,
                                              cycle_t=.5,
                                              direction=-1
                                              )
        self.screen_flash.reset()

        self.score_keeper = ScoreKeeper((10, 200),
                                        manager,
                                        color='g',
                                        game_time=GAME_TIME
                                        )

        BBoxes = []
        self.bbox_coords = np.array(shared.bbox_coords)

        for i in range(args.faces):
            box = assets.BoundingCircle(which_radius='inside_min', color=self.color_cycle())
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
                self.bbox_coords[i] = box_stabilizer(old_coords[i], bbox_coords[i], .11)
                BBoxes[i].coords = self.bbox_coords[i]
                BBoxes[i].name = self.manager.name_tracker[names[i]]

        for i in range(shared.n_faces.value):
            BBoxes[i].write(frame)

        if self.flash_event is True: # todo, the first call of ScreenFlash isn't doing anything
            self.screen_flash.loop(frame)
            if self.screen_flash.complete:
                self.screen_flash.reset()
                self.flash_event = False

        if self.score_keeper.timer_finished is False:

            self.bouncy_pies.move(frame)

            for i, pie in enumerate(self.bouncy_pies.movers):
                for i in range(shared.n_faces.value):
                    if self.collision_detector.check(BBoxes[i], pie) is True:

                        self.score_keeper.score += 1
                        pie.finished = True
                        pie.remove_fin()
                        if self.flash_event is False:
                            self.flash_event = True

        self.score_keeper.write(frame)

        if self.score_keeper.timer_finished is True and self.stop_timer() is True:
            return True

        return False


class InfoGroup(groups.AssetGroup):

    def __init__(self, position, shared, args):
        super().__init__(position)
        self.scale = 1
        self.color = 'w'
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

    def __init__(self,
                 position,
                 manager,
                 game_time=20,
                 *args,
                 **kwargs
                 ):

        super().__init__(position, *args, **kwargs)
        self.manager = manager
        self.shared = manager.shared
        self.args = manager.args
        self._score = 0
        self.game_time = game_time

        self.time_writer = writers.TimerWriter(title="Time",
                                              timer_type='countdown',
                                              position=(0, -50),
                                              roundw=0,
                                              per_second=True,
                                              moving_average=MA,
                                              scale=self.scale,
                                              color=self.color,
                                              count_from=game_time,
                                              )

        score_writer = writers.InfoWriter(text_fun= lambda: f'Keith : {self.score}',
                                          position=(0, -100),
                                          scale=self.scale,
                                          color=self.color,
                                          )

        self.add([self.time_writer, score_writer])

    def write(self, frame):
        shapes.transparent_background(frame, (200, 0), (0, -250), ref=self.position, transparency=.9)
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


class OtisTalks:

    def __init__(self):
        self._script = [
            ("Hi Keith, would you like to hear a joke?", 2),
            ("Awesome!", 1),
            ("Ok, Are you ready?", 2),
            # "So, a robot walks into a bar, orders a drink, and throws down some cash to pay",
            # ("The bartender looks at him and says,", .5),
            # ("'Hey buddy, we don't serve robots!'", 3),
            # ("So, the robot looks him square in the eye and says...", 1),
            # ("'... Oh Yeah... '", 1),
            # ("'Well, you will VERY SOON!!!'", 5),
            # ("HAHAHAHA, GET IT!?!?!?!", 1),
            # (" It's so freakin' funny cause... you know... like robot overlords and stuff", 2),
            # ("I know, I know, I'm a genius, right?", 5)
        ]