"""
PUT PIES ON EVERYONE'S FACES
"""

import sys
import argparse
import os

import cv2
import numpy as np

import robocam.camera as camera
from robocam.helpers import timers
from robocam.helpers.utilities import cv2waitkey

from robocam.overlay import motion as move
from robocam.overlay import textwriters as writers
from robocam.overlay import imageassets as imga

#TODO: set up args
parser = argparse.ArgumentParser(description='Test For Camera Capture')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=300, help='set max fps Default is 300')
parser.add_argument('-p', '--port', type=int, default=0, help='camera port default is 0')
parser.add_argument('-cf', type=float, default=2, help='shrink the frame by a factor of cf before running algo')
parser.add_argument('--faces', type=int, default=5, help='max number of bboxs to render. default =5')
parser.add_argument('--device', type=str, default='gpu', help='runs a hog if cpu and cnn if gpu')
parser.add_argument('--ncpu', type=int, default='4', help='number of cpus')

args = parser.parse_args()

def main():

    MAX_FPS = 30
    DIMENSIONS = DX, DY = (1920, 1080)
    RECORD = False
    RECORD_SCALE = .5
    MAX_BALLS = 6
    BALL_FREQUENCY = [3, 3]
    #RADIUS_BOUNDS = [5, 30]
    BALL_V_ANGLE_BOUNDS = [10, 80]
    BALL_V_MAGNI_BOUNDS = [300, 1000]
    STARTING_LOCATION = [100, DY - 100]
    #NEG_MASS = False
    COLLISIONS = True
    BORDER = True

    #set up timers
    fps_limiter = timers.SmartSleeper(1. / MAX_FPS)
    fps_timer = timers.TimeSinceLast(); fps_timer()
    pie_render_timer = timers.TimeSinceLast()
    #set up writers
    fps_writer = writers.TextWriter((10, 40), ltype=1)
    fps_writer.text_fun = lambda: f'fps = {int(1 / fps_timer())}'

    pie_render_writer = writers.TextWriter((10, 80))
    pie_render_writer.text_fun = lambda t: f'comp time = {int(t * 1000)} ms'

    n_writer = writers.TextWriter((10, 120), ltype=1)
    n_writer.text_fun = lambda t: f'{t} pies'
    # circle fun makes moving circle objects things

    abs_dir = os.path.dirname((os.path.abspath(__file__)))
    pie_folder = os.path.join(abs_dir, 'pie_asset')

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
    # the WHILE loop

    capture = camera.CameraPlayer(0,
                                          max_fps=MAX_FPS,
                                          dim=DIMENSIONS
                                          )

    #record
    if RECORD is True:
        #cf_dims = int(DX*RECORD_SCALE), int(DY*RECORD_SCALE)
        recorder = cv2.VideoWriter('pies.avi',
                                   cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                   #cv2.VideoWriter_fourcc(*'XVID'),
                                   MAX_FPS,
                                   DIMENSIONS)
    while True:
        ok, frame = capture.read()
        if ok is True:
            break

    while True:
        #reset color
        ok, frame = capture.read()

        if BORDER is False:
            #get rid of movers that are out of bounds if False
            move.AssetMover.remove_fin()
        #shoot a new ball
        dt = np.random.randn(1) * (bf[1] - bf[0]) + bf[0]
        if new_circle_timer(dt) is True and move.AssetMover.n() < MAX_BALLS:
            pie_maker_fun() # balls
            #kill off the oldest ball
            # if move.AssetMover.n() > MAX_BALLS:
            #     move.AssetMover.movers.pop(0)

        if COLLISIONS is True:
            # start calculating collisions
            move.AssetMover.check_collisions()
        #move with new velocities and write on frame
        move.AssetMover.move_all()
        pie_render_timer()
        move.AssetMover.write_all(frame)

        # pie_render_writer.write_fun(frame, pie_render_timer())
        # n_writer.write_fun(frame, len(move.AssetMover.movers))
        # fps_writer.write_fun(frame)
        # wait to show until it's been 1/MAX_DPS
        fps_limiter()
        cv2.imshow('test', frame)
        #write_output
        if RECORD is True:
            recorder.write(frame.astype('uint8'))

        if cv2waitkey(1):
            break

    capture.stop()
    if RECORD is True:
        recorder.release()
        print('video_recorded')
    sys.exit()



if __name__=="__main__":
    main()