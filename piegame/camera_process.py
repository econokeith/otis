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


def target(shared, args):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    MAX_FPS = 30
    DIMENSIONS = DX, DY = (1920, 1080)
    RECORD = False
    RECORD_SCALE = .5
    MAX_BALLS = 2
    BALL_FREQUENCY = [3, 3]
    #RADIUS_BOUNDS = [5, 30]
    BALL_V_ANGLE_BOUNDS = [10, 80]
    BALL_V_MAGNI_BOUNDS = [300, 1000]
    STARTING_LOCATION = [200, DY - 200]
    #NEG_MASS = False
    COLLISIONS = False
    BORDER = True
    MAX_FPS = 60
    DIMENSIONS = (1920, 1080)
    pie_path = './photo_asset_files/pie_asset'

    capture = camera.CameraPlayer(0,
                                  max_fps=MAX_FPS,
                                  dim=DIMENSIONS
                                  )

    bouncy_pies = motion.BouncingAssetManager(asset_fun = pie_path,
                                               max_fps=60,
                                               dim=DIMENSIONS
                                               )

    time.sleep(1)

    collision_detector = motion.CollisionDetector(.1)
    screen_flash = events.ColorFlash()

    circle = shapes.Circle((0,0),
                           80,
                           ref='c',
                           dim=DIMENSIONS,
                           thickness=2)
    flash_event = False

    while True:
        capture.read()

        if flash_event is True:
            screen_flash.loop(capture.frame)
            if screen_flash.complete:
                print(screen_flash.complete)
                screen_flash.reset()
                flash_event = False

        bouncy_pies.move(capture.frame)
        circle.write(capture.frame)
        capture.show()

        if cv2waitkey(1):
            break

        for i, pie in enumerate(bouncy_pies.movers):
            collision_q = collision_detector.check(circle, pie)
            print(collision_q)
            if collision_detector.check(circle, pie) is True and flash_event is False:
                print(collision_q)
                flash_event = True
                break

    capture.stop()
    sys.exit()