import signal
import sys
import time
import os
from collections import defaultdict
from queue import Queue

import numpy as np

from robocam import camera
from robocam.helpers import multitools as mtools, utilities as utils, timers, cvtools, colortools as ctools
from robocam.overlay import screenevents as events, textwriters as writers, assets, groups, motion, shapefunctions

MAX_FPS = 30

RECORD = False
RECORD_SCALE = .25
OUTPUT_SCALE = 1

pie_path = 'photo_asset_files/pie_asset'
face_path = 'faces'

MA = 30

def target(shared, pargs):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

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


    info_group = InfoGroup((10, 40), shared, pargs)




    while True:

        check, frame = capture.read()
        shared.frame[:] = frame  # latest frame to shared frame
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


class BouncyScene:

    def __init__(self, manager, shared, args):
        self.manager = manager
        self.shared = shared
        self.args = args
        self.capture = self.manager.capture

        self.stop_timer = timers.SinceFirstBool(3)

        self.color_cycle = ctools.ColorCycle()

        self.screen_flash = events.ColorFlash(max_ups=args.max_fps,
                                              cycle_t=.5,
                                              direction=-1
                                              )
        self.screen_flash.reset()

        self.bbox_coords = np.array(shared.bbox_coords)

        self.box_fun = lambda: assets.BoundingBox(color=self.color_cycle())
        self.bbox_hash = defaultdict(self.box_fun)

        self.is_updated = True
        self.flash_event = False

        self.frame = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')
        self.names = []

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
                box.write(frame)


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


