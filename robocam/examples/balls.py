"""
PUT PIES ON EVERYONE'S FACES
"""

import multiprocessing as multi
import signal
import ctypes
import sys
import time
import argparse
import os
import copy
from itertools import cycle

import cv2
import numpy as np

import robocam.camera as camera
from robocam.helpers import timers
from robocam.helpers.utilities import cv2waitkey

from robocam.overlay import motion as move
from robocam.overlay import cv2shapes as shapes
from robocam.overlay import textwriters as writers
from robocam.overlay import assets as assets
from robocam.overlay import colortools as ctools
from robocam.overlay import groups

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
    DIMENSIONS = DX, DY = (1080, 720)
    RECORD = False
    MAX_BALLS = 50
    BALL_FREQUENCY = [.25, .75]
    RADIUS_BOUNDS = [5, 30]
    BALL_V_ANGLE_BOUNDS = [10, 80]
    BALL_V_MAGNI_BOUNDS = [100, 1000]
    STARTING_LOCATION = [50, DY - 50]
    NEG_MASS = False
    COLLISIONS = True
    BORDER = True
    #define color cycle
    colors = list(ctools.COLOR_HASH.keys())
    colors.remove('b')
    color_cycle = cycle(colors)
    #make frame
    frame = np.zeros((*DIMENSIONS[::-1], 3), dtype='uint8')
    #record
    if RECORD is True:
        recorder = cv2.VideoWriter('balls.avi',
                                   cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                   MAX_FPS,
                                   DIMENSIONS)
    #set up timers
    fps_limiter = timers.SmartSleeper(1. / MAX_FPS)
    fps_timer = timers.TimeSinceLast(); fps_timer()
    collision_timer = timers.TimeSinceLast()
    #set up writers
    fps_writer = writers.TextWriter((10, 40), ltype=1)
    fps_writer.text_fun = lambda: f'fps = {int(1 / fps_timer())}'

    collision_writer = writers.TextWriter((10, 80), ltype=1)
    collision_writer.text_fun = lambda t: f'comp time = {int(t * 1000)} ms'

    n_writer = writers.TextWriter((10, 120), ltype=1)
    n_writer.text_fun = lambda t: f'{t} balls'
    # circle fun makes moving circle objects things
    def circle_fun():
        # make the circle
        circle = shapes.Circle((0, 0),
                                np.random.randint(*RADIUS_BOUNDS),
                                color=next(color_cycle),
                                thickness=-1)
        # random initial velocity
        m = np.random.randint(*BALL_V_MAGNI_BOUNDS)
        a = np.random.randint(*BALL_V_ANGLE_BOUNDS)
        v = np.array([np.cos(a / 180 * np.pi) * m, -np.sin(a / 180 * np.pi) * m])
        # put circle in a mover
        circle_mover = move.AssetMover(circle, circle.radius,
                                       STARTING_LOCATION,
                                       v,
                                       (0, DX - 1), (0, DY - 1),
                                       border_collision=BORDER,
                                       ups=MAX_FPS
                                       )
        # make mass vary negatively with radius
        if NEG_MASS is True:
            circle_mover.mass = RADIUS_BOUNDS[1]+10 - circle.radius
    # for controlling the frequency of new balls
    new_circle_timer = timers.CallHzLimiter()
    bf = BALL_FREQUENCY
    # the WHILE loop
    while True:
        #reset color
        frame[:, :, :] = 0

        if BORDER is False:
            #get rid of movers that are out of bounds if False
            living_movers = []
            for mover in move.AssetMover.movers:
                if mover.finished is False:
                    living_movers.append(mover)
            move.AssetMover.movers = living_movers
        #shoot a new ball
        dt = np.random.randn(1) * (bf[1] - bf[0]) + bf[0]
        if new_circle_timer(dt) is True:
            circle_fun() # balls
            #kill off the oldest ball
            if len(move.AssetMover.movers) > MAX_BALLS:
                move.AssetMover.movers.pop(0)

        if COLLISIONS is True:
            collision_timer()  # start calculating collisions
            for i, circle1 in enumerate(move.AssetMover.movers):
                for circle2 in move.AssetMover.movers[i + 1:]:
                    circle1.collide(circle2)
                    move.remove_overlap(circle1, circle2)
            ct = collision_timer() # finish
        #move with new velocities and write on frame
        for circle in move.AssetMover.movers:
            circle.move()
            circle.write(frame)
        # write extra data
        if COLLISIONS is True:
            collision_writer.write_fun(frame, ct)

        n_writer.write_fun(frame, len(move.AssetMover.movers))
        fps_writer.write_fun(frame)
        # wait to show until it's been 1/MAX_DPS
        fps_limiter()
        cv2.imshow('test', frame)
        # out.write(frame)

        if cv2waitkey(1):
            break

    cv2.destroyAllWindows()
    if RECORD is True:
        recorder.release()

if __name__=="__main__":
    main()