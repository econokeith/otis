import signal
import sys

import cv2
import numpy as np


from robocam.helpers import multitools as mtools, timers as timers
from robocam.servos import ArduinoServo, pid as pid


def target(shared_data_object, args):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    if args.servo is False:
        sys.exit()

    shared = shared_data_object
    Servo = ArduinoServo(2, '/dev/ttyACM0' , connect=True, use_micro=True)
    Servo.angles = [70,60]
    Servo.write()

    video_center = args.video_center

    xPID = pid.PIDController(.08, 0, .0000000001)
    yPID = pid.PIDController(.05, 0, .0000000001)
    update_limiter = timers.CallHzLimiter(1 / 5)
    target = np.array(video_center)
    last_coords = np.array(shared.bbox_coords[0,:])

    while True:
        if shared.n_faces.value > 0:
            break

    while True:
        if update_limiter() and np.all(shared.bbox_coords[0,:] != last_coords):
            t, r, b, l = shared.bbox_coords[0,:]
            target[0], target[1] = (r+l)//2, (b+t)//2
            error = target - video_center
            move_x = xPID.update(error[0], sleep=0)
            move_y = yPID.update(error[1], sleep=0)
            Servo.move([-move_x, -move_y])
            last_coords = np.array(shared.bbox_coords[0,:])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    Servo.close()