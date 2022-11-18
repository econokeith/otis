import signal
import sys
from collections import defaultdict

import numpy as np

import otis.helpers.cvtools
import otis.helpers.maths
from otis import camera
from otis.helpers import multitools, timers, cvtools, colortools
from otis.overlay import screenevents as events, textwriters, assets, groups

MAX_FPS = 30

RECORD = False
RECORD_SCALE = .25
OUTPUT_SCALE = 1

pie_path = 'photo_asset_files/pie_asset'
face_path = 'faces'

MA = 30

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
    boxes = Boxes(manager, shared, pargs)

    info_group = InfoGroup((10, 40), shared, pargs)




    while True:

        check, frame = capture.read()
        shared.frame[:] = frame  # latest frame to shared frame
        boxes.loop(frame)
        info_group.write(frame)
        capture.show(frame)

        if otis.helpers.cvtools.cv2waitkey() is True:
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
        self.name_tracker = cvtools.NameTracker(args.PATH_TO_FACES)

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


class Boxes:

    def __init__(self, manager):
        self.manager = manager
        self.shared = manager.shared
        self.args = manager.args
        self.capture = self.manager.capture



        self.color_cycle = colortools.ColorCycle()

        self.screen_flash.reset()

        self.bbox_coords = np.array(self.shared.bbox_coords)

        self.box_fun = lambda: assets.BoundingBox(color=self.color_cycle())
        self.bbox_hash = defaultdict(self.box_fun)

        self.is_updated = True
        self.flash_event = False

        self.frame = np.zeros((self.args.dim[1], self.args.dim[0], 3), dtype='uint8')
        self.names = []

    def loop(self):
        frame = self.capture.frame
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
                box.write(frame)


class InfoGroup(groups.AssetGroup):

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


