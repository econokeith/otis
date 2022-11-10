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

from robocam.overlay import motion as move
from robocam.overlay import textwriters as writers
from robocam.overlay import imageassets as imga


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

    fps_limiter = timers.SmartSleeper(1. / MAX_FPS)
    fps_timer = timers.TimeSinceLast(); fps_timer()
    pie_render_timer = timers.TimeSinceLast()

    pie_render_writer = writers.TextWriter((10, 80))
    n_writer = writers.TextWriter((10, 120), ltype=1)
    n_writer.text_fun = lambda t: f'{t} pies'

    abs_dir = os.path.dirname((os.path.abspath(__file__)))
    pie_folder = os.path.join(abs_dir, '../robocam/overlay/photo_asset_files/pie_asset')
    Pie0 = imga.ImageAsset(pie_folder)

    def pie_maker_fun():
        # random initial velocity
        m = np.random.randint(*BALL_V_MAGNI_BOUNDS)
        a = np.random.randint(*BALL_V_ANGLE_BOUNDS)/ 180 * np.pi
        v = np.array([np.cos(a) * m, -np.sin(a) * m])
        # put circle in a mover
        move.AssetMover(Pie0, 85,
                       STARTING_LOCATION,
                       v,
                       (0, DX - 1), (0, DY - 1),
                       border_collision=BORDER,
                       ups=MAX_FPS
                       )
    # for controlling the frequency of new balls
    new_circle_timer = timers.CallHzLimiter()
    bf = BALL_FREQUENCY

    capture = camera.CameraPlayer(0,
                                  max_fps=MAX_FPS,
                                  dim=DIMENSIONS
                                  )
    time.sleep(2)
    #TODO make RECORD a natural part of CameraObject
    if RECORD is True:
        recorder = cv2.VideoWriter('pies.avi',
                                   cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                   MAX_FPS,
                                   DIMENSIONS)


    while True:
        # reset color
        capture.read()

        if BORDER is False:
            # get rid of movers that are out of bounds if False
            move.AssetMover.remove_fin()
        # shoot a new ball
        dt = np.random.randn(1) * (bf[1] - bf[0]) + bf[0]
        if new_circle_timer(dt) is True and move.AssetMover.n() < MAX_BALLS:
            pie_maker_fun()  # balls
            # kill off the oldest ball
            # if move.AssetMover.n() > MAX_BALLS:
            #     move.AssetMover.movers.pop(0)
            print(move.AssetMover.n())

        if COLLISIONS is True:
            # start calculating collisions
            move.AssetMover.check_collisions()
        # move with new velocities and write on frame
        move.AssetMover.move_all()
        pie_render_timer()
        move.AssetMover.write_all(capture.frame)

        # fps_limiter()
        # cv2.imshow('test', frame)
        capture.show()
        # write_output
        if RECORD is True:
            recorder.write(capture.frame.astype('uint8'))

        if cv2waitkey(1):
            break

    capture.stop()
    if RECORD is True:
        recorder.release()
        print('video_recorded')
    sys.exit()