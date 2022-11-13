import signal
import sys
import argparse
import os
import time

import cv2
import numpy as np

import robocam.camera as camera
from robocam.helpers import timers
from robocam.helpers.utilities import cv2waitkey

from robocam.overlay import motion
from robocam.overlay import textwriters as writers
from robocam.overlay import imageassets as imga
from robocam.overlay import shapes


from robocam import camera as camera
from robocam.helpers import multitools as mtools, timers as timers, utilities as utils, colortools as ctools
from robocam.overlay import screenevents as events, textwriters as writers, assets as assets

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
MAX_FPS = 30
DIMENSIONS = (1920, 1080)
pie_path = './photo_asset_files/pie_asset'

def target(shared, args):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    capture = camera.ThreadedCameraPlayer(0,
                                  max_fps=args.max_fps,
                                  dim=args.dim,
                                  ).start()

    manager = SceneManager(shared, args, capture)
    bouncy_scene = BouncyScene(manager, shared, args)

    while True:

        capture.read()
        bouncy_scene.loop(capture.frame)
        capture.show()
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
        if capture is None:
            self.capture = camera.ThreadedCameraPlayer(0,
                                                      max_fps=args.max_fps,
                                                      dim=args.dim,
                                                      ).start()
        else:
            self.capture = capture

        self.scene_number = 0




class BouncyScene:

    def __init__(self, manager, shared, args):
        self.manager = manager
        self.shared = manager.shared
        self.args = manager.args

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

        self.circle = shapes.Circle((990, 540),
                               80,
                               dim=args.dim,
                               thickness=2)
        self.flash_event = False


    def loop(self, frame):

        if self.flash_event is True:
            self.screen_flash.loop(frame)
            if self.screen_flash.complete:
                self.screen_flash.reset()
                self.flash_event = False

        self.bouncy_pies.move(frame)
        self.circle.write(frame)

        for i, pie in enumerate(self.bouncy_pies.movers):

            if self.collision_detector.check(self.circle, pie) is True and self.flash_event is False:
                self.flash_event = True
                break



