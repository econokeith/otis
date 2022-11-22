import signal
import sys

import cv2
import numpy as np

from otis.helpers import multitools as mtools, timers as timers
from _piardservo.container import ServoContainer
from _piardservo.microcontrollers import RPiWifi
from _piardservo.pid import PIDController

MAX_SERVO_UPDATES_PER_SECOND = 10
X_PID_VALUES = (.0001, .000001, .00001)
Y_PID_VALUES = (.0001, .000001, .00001)

def target(shared_data_object, args):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    if args.servo is False:
        sys.exit()

    rpi = RPiWifi(address='192.168.1.28', pins=(22, 17))
    Servos = ServoContainer(n=2, microcontroller=rpi).connect()

    Servos[0].value = -.1
    Servos[1].value = -.5

    xPID = PIDController(*X_PID_VALUES)
    yPID = PIDController(*Y_PID_VALUES)

    update_limiter = timers.CallFrequencyLimiter(1 / MAX_SERVO_UPDATES_PER_SECOND)

    target = np.asarray(shared_data_object.target)
    video_center = np.array(args.video_center)
    error = np.zeros(2, dtype=int)
    target[:] = args.video_center

    while True:
        if shared_data_object.n_faces.value > 0:
            break

    while True:

        if update_limiter():

            error[:] = target - video_center
            Servos[0].value += xPID.update(error[0], sleep=0)
            Servos[1].value += yPID.update(error[1], sleep=0)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    Servos.close()
