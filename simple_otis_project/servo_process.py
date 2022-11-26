import signal
import sys

import cv2
import numpy as np

from otis.helpers import multitools as mtools, timers as timers
from _piardservo.container import ServoContainer
from _piardservo.microcontrollers import RPiWifi
from _piardservo.pid import PIDController

MAX_SERVO_UPDATES_PER_SECOND = 10
# X_PID_VALUES = (.0001, .000000001, .00000001)
# Y_PID_VALUES = (.0001, .000000001, .00000001)
X_PID_VALUES = (1e-4, 1e-10, 2e-7)
Y_PID_VALUES = (5e-5 ,1e-10, 2e-7)
MINIMUM_MOVE_SIZE_PIXELS = 20
SERVO_START = np.array((-.06, -.72))
KEYBOARD_MOVE_INCREMENT = -.01
STEPS_TO_RESET = 2

def target(shared_data_object, args):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    if args.servo is False:
        sys.exit()

    rpi = RPiWifi(address='192.168.1.28', pins=(22, 17))
    Servos = ServoContainer(n=2, microcontroller=rpi).connect()


    Servos[0].value,  Servos[1].value = SERVO_START


    xPID = PIDController(*X_PID_VALUES)
    yPID = PIDController(*Y_PID_VALUES)

    update_limiter = timers.CallFrequencyLimiter(1 / MAX_SERVO_UPDATES_PER_SECOND)

    # target = np.asarray(shared_data_object.servo_target)
    video_center = np.array(args.video_center)
    # error = np.zeros(2, dtype=int)W
    # target[:] = args.video_center
    SERVO_TRACKING = True
    ACTIVE_TARGET = False
    reset_counter = 0
    reset_complete = True
    while True:
        if shared_data_object.n_observed_faces.value > 0:
            break

    while True:

        if shared_data_object.n_boxes_active.value == 0:
            if reset_complete is False:
                Servos[0].value, Servos[1].value = SERVO_START
                reset_complete = True

            # if ACTIVE_TARGET is True:
            #     ACTIVE_TARGET = False
            #     reset_complete = False
            #     reset_counter = 0
            #     error = Servos.values() - SERVO_START
            #     step_size = error / STEPS_TO_RESET
            #
            #
            # elif reset_complete is False:
            #     for i, servo in enumerate(Servos):
            #         servo.value += step_size[i]
            #     reset_counter += 1
            #     if reset_counter > STEPS_TO_RESET:
            #         reset_complete = True
            #
            # else:
            #     reset_counter = 0

        elif update_limiter() is True and SERVO_TRACKING is True:
            reset_complete = False
            target = np.array(shared_data_object.servo_target)
            error = target - video_center

            if np.abs(error[0]) > MINIMUM_MOVE_SIZE_PIXELS:
                Servos[0].value += xPID.update(error[0], sleep=0)

            if np.abs(error[1]) > MINIMUM_MOVE_SIZE_PIXELS:
                Servos[1].value += yPID.update(error[1], sleep=0)

        shared_data_object.servo_position[0] = round(Servos[0].value, 2)
        shared_data_object.servo_position[1] = round(Servos[1].value, 2)

        key_board_input = shared_data_object.keyboard_input.value
        if key_board_input == ord('q'):
            break

        elif key_board_input == ord('e'):
            SERVO_TRACKING = not SERVO_TRACKING

        elif key_board_input == ord('a'):
            Servos[0].value += KEYBOARD_MOVE_INCREMENT
            SERVO_TRACKING = False

        elif key_board_input == ord('d'):
            Servos[0].value -= KEYBOARD_MOVE_INCREMENT
            SERVO_TRACKING = False

        elif key_board_input == ord('w'):
            Servos[1].value += KEYBOARD_MOVE_INCREMENT
            SERVO_TRACKING = False

        elif key_board_input == ord('s'):
            Servos[1].value -= KEYBOARD_MOVE_INCREMENT
            SERVO_TRACKING = False

        else:
            pass

    Servos.close()
    sys.exit()
