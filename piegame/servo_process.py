import signal
import sys

import cv2
import numpy as np

from otis.helpers import multitools as mtools, timers as timers
from _piardservo.container import ServoContainer
from _piardservo.microcontrollers import RPiWifi
from _piardservo.pid import PIDController


def target(shared_data_object, args):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    if args.servo is False:
        sys.exit()

    rpi = RPiWifi(address='192.168.1.28', pins=(22, 17))
    Servos = ServoContainer(n=2, microcontroller=rpi).connect()

    Servos[0].value = -.1
    Servos[1].value = -.5

    xPID = PIDController(.001, 0, .00001)
    yPID = PIDController(.001, 0, .00001)

    video_center = args.video_center

    update_limiter = timers.CallFrequencyLimiter(1 / 5)
    target = np.array(video_center)
    last_coords = np.array(shared_data_object.bbox_coords[0,:])

    while True:
        if shared_data_object.n_faces.value > 0:
            break

    while True:
        #make copies in order to avoid updates in the middle of a loop
        names = list(np.array(shared.names[:shared.n_faces.value]))
        primary = shared.primary_target.value

        if primary in names:
            p_index = list(names).index(primary)
        else:
            p_index = 0

        #copy
        new_coords = np.array(shared.bbox_coords[p_index,:])

        if update_limiter() and np.all(new_coords != last_coords):
            t, r, b, l = shared.bbox_coords[p_index,:]

            #if center of the screen, don't adjust the camera
            if t <= video_center[0] <= b and r <= video_center[0] <= l:
                error = 0
            else:
                target[0], target[1] = (r+l)//2, (b+t)//2
                error = target - video_center
                Servos[0].value += -xPID.update(error[0], sleep=0)
                Servos[1].value += yPID.update(error[1], sleep=0)


            last_coords = np.array(new_coords)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    Servos.close()
