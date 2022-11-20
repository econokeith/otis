import signal
import sys
from collections import defaultdict
import numpy as np

import otis.helpers.cvtools
import otis.helpers.maths
from otis import camera
from otis.helpers import multitools, timers, cvtools, colortools, shapefunctions
from otis.overlay import screenevents, textwriters, assets, writergroups, motion

MAX_FPS = 30
DIMENSIONS = DX, DY = (1920, 1080)
RECORD = False
RECORD_SCALE = .25
OUTPUT_SCALE = 1.5

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
GAME_TIME = 30
# pie_path= '/home/keith/Projects/otis/otis/overlay/photo_assets/pie_asset'
pie_path = 'photo_asset_files/pie_asset'
face_path = 'faces'

MA = 30

NUMBER_OF_PLAYERS = 2

PLAYER_NAMES = ["Keith", "David"]

STOP_AFTER_GAME = False


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)

    capture = camera.ThreadedCameraPlayer(0,
                                          max_fps=pargs.max_fps,
                                          dim=pargs.dim,
                                          flip=True,
                                          record=RECORD,
                                          record_to='pie.avi',
                                          output_scale=OUTPUT_SCALE,
                                          record_scale=RECORD_SCALE
                                          ).start()

    manager = SceneManager(shared, pargs, capture=capture)
    bouncy_scene = BouncyScene(manager, shared, pargs)

    info_group = InfoGroup((10, 40), shared, pargs)

    count_down = screenevents.CountDown(pargs.dim, 3)

    while True:
        count_down.loop(show=False)
        capture.show(count_down.frame)

        if count_down.finished is True:
            break

        if otis.helpers.cvtools.cv2waitkey(1) is True:
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

        if otis.helpers.cvtools.cv2waitkey() is True:
            break

    capture.stop()
    sys.exit()


#######################################################################################################################
#######################################################################################################################
#######################################################################################################################
class SceneManager:

    def __init__(self, shared, pargs, capture=None):

        self.shared = shared
        self.pargs = pargs
        self.name_tracker = cvtools.NameTracker(pargs.PATH_TO_FACES)
        self.capture = capture
        self.scene_number = 0


class BouncyScene:

    def __init__(self, manager, shared, args):
        self.manager = manager
        self.shared = shared
        self.args = args
        self.capture = self.manager.capture
        self.stop_timer = timers.SinceFirstBool(3)
        self.color_cycle = colortools.ColorCycle()

        self.bouncy_pies = motion.BouncingAssetManager(asset_fun=args.PATH_TO_PIES,
                                                       max_fps=args.max_fps,
                                                       dim=args.dim,
                                                       max_balls=MAX_BALLS,
                                                       collisions=COLLISIONS,
                                                       scale = PIE_SCALE,
                                                       )

        self.collision_detector = motion.CollisionDetector(COLLISION_OVERLAP)
        self.screen_flash = screenevents.ColorFlash(max_ups=args.max_fps,
                                                    cycle_t=.5,
                                                    direction=-1
                                                    )
        self.screen_flash.reset()
        self.score_keeper = ScoreKeeper((10, 200),
                                        manager,
                                        color='g',
                                        game_time=GAME_TIME,
                                        scale=2,
                                        players=PLAYER_NAMES,
                                        )

        self.bbox_coords = np.array(shared.bbox_coords)
        self.box_fun = lambda: assets.BoundingCircle(which_radius='inside_min',
                                                     color=self.color_cycle()
                                                     )
        self.bbox_hash = defaultdict(self.box_fun)
        self.is_updated = True
        self.flash_event = False
        self.frame = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')
        self.names = []

    def loop(self, frame):
        shared = self.shared
        bbox_hash = self.bbox_hash
        tracker = self.manager.name_tracker

        if shared.new_overlay.value:

            bbox_coords = shared.bbox_coords.copy()
            n_faces = self.shared.n_faces.value
            self.names = [tracker[name] for name in shared.names[:n_faces]]

            for i, name in enumerate(self.names):
                box = bbox_hash[name]
                box.name = name
                box.coords = bbox_coords[i]
                box.write(frame)

        if self.flash_event is True: # todo, the first call of ScreenFlash isn't doing anything
            self.screen_flash.loop(frame)
            if self.screen_flash.complete:
                self.screen_flash.reset()
                self.flash_event = False

        if self.score_keeper.timer_finished is False:

            self.bouncy_pies.move(frame)

            for i, pie in enumerate(self.bouncy_pies.movers):

                for name in self.names:

                    if self.collision_detector.check(bbox_hash[name], pie) is True:
                        self.score_keeper.score[name] += 1
                        pie.finished = True
                        pie.remove_fin()

                        if self.flash_event is False:
                            self.flash_event = True

        self.score_keeper.write(frame)

        if self.score_keeper.timer_finished is True and self.stop_timer() is True:
            return True

        return False


class InfoGroup(writergroups.AssetGroup):

    def __init__(self, position, shared, args):
        super().__init__(position)
        self.scale = 1
        self.color = 'w'
        self.shared = shared
        self.args = args

        fps_writer = textwriters.TimerWriter(title="screen fps",
                                             timer_type='last',
                                             position=(0, 0),
                                             roundw=0,
                                             per_second=True,
                                             moving_average=MA,
                                             scale=self.scale,
                                             color=self.color,
                                             )

        self.model_ma = otis.helpers.maths.MovingAverage(MA)

        ma_text_fun = lambda: f'model updates per second : {int(1 / self.model_ma.update(shared.m_time.value))}'
        model_writer = textwriters.InfoWriter(text_fun=ma_text_fun,
                                              position=(0, -30),
                                              scale=self.scale,
                                              color=self.color,
                                              )

        self.add([model_writer, fps_writer])


class ScoreKeeper(writergroups.AssetGroup):

    def __init__(self,
                 position,
                 manager,
                 game_time=20,
                 players = ('Keith'),
                 v_spacing = 70,
                 *args,
                 **kwargs
                 ):

        super().__init__(position, *args, **kwargs)
        self.manager = manager
        self.shared = manager.shared
        self.args = manager.pargs
        self.score = defaultdict(lambda: 0)
        self.game_time = game_time
        self.players = players
        self.v_spacing = v_spacing

        self.time_writer = textwriters.TimerWriter(title="Time",
                                                   timer_type='countdown',
                                                   position=(10, -v_spacing),
                                                   roundw=0,
                                                   per_second=True,
                                                   moving_average=MA,
                                                   scale=self.scale,
                                                   color=self.color,
                                                   count_from=game_time,
                                                   )
        # make the score textwriters
        score_writers = []
        score_text_fun = lambda name: f'{name} : {self.score[name]}'

        for i, name in enumerate(self.players):
            score_writer = textwriters.InfoWriter(text_fun= score_text_fun,
                                                  position=(10, -v_spacing*2-v_spacing*i),
                                                  scale=self.scale,
                                                  color=self.color,
                                                  )
            score_writers.append(score_writer)

        self.add([self.time_writer])
        self.add(score_writers)


    def write(self, frame):
        # shapefunctions.write_transparent_background(frame,
        #                                             (200, 0),
        #                                             (0, -250),
        #                                             ref=self.position,
        #                                             transparency=.9
        #                                             )

        self.assets[0].write(frame)
        for name, asset in zip(self.players, self.assets[1:]):
            asset.write(frame, name)

    @property
    def timer_finished(self):
        return self.time_writer.timer_finished
