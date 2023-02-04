import signal
import sys

import cv2
import numpy as np

from otis.helpers import multitools as mtools, timers as timers
from _piardservo.container import ServoContainer
from _piardservo.microcontrollers import RPiWifi
from _piardservo.pid import PIDController


_UPDATE_FACTOR = 4
_MAX_SERVO_UPDATES_PER_SECOND = 5 * _UPDATE_FACTOR

_X_PID_VALUES = (2e-4 / _UPDATE_FACTOR, 1e-10, 1e-7 / _UPDATE_FACTOR)
Y_PID_VALUES = (2e-4 / _UPDATE_FACTOR, 1e-10, 1e-7 / _UPDATE_FACTOR)

MINIMUM_MOVE_SIZE_PIXELS = 5
SERVO_START = np.array((-.2, -.3))
KEYBOARD_MOVE_INCREMENT = -.01
STEPS_TO_RESET = 2
SERVO_ADDRESS = '192.168.1.115'
SERVO_PINS = (17, 22)


def target(shared_data_object, pargs):
    SERVO_TRACKING = True
    # signal.signal(signal.SIGTERM, close_gracefully)
    # signal.signal(signal.SIGINT, close_gracefully)


    shared = shared_data_object

    if pargs.servo is False:
        sys.exit()

    rpi = RPiWifi(address=SERVO_ADDRESS,
                  pins=SERVO_PINS
                  )

    try:
        Servos = ServoContainer(n=2,
                                microcontroller=rpi,
                                min_pulse_width=600,
                                max_pulse_width=2400).connect()
    except OSError:
        print(f'OSERROR: Unable to connect {Servos.host}:{Servos.port}')
        sys.exit(0)

    def close_gracefully(sig, frame):
        print('[INFO] Closing Servo Connection and Existing...')
        Servos.close()
        sys.exit(0)

    signal.signal(signal.SIGTERM, close_gracefully)
    signal.signal(signal.SIGINT, close_gracefully)

    Servos[0].value,  Servos[1].value = SERVO_START

    xPID = PIDController(*_X_PID_VALUES)
    yPID = PIDController(*Y_PID_VALUES)

    update_limiter = timers.SmartSleeper(1 / _MAX_SERVO_UPDATES_PER_SECOND)

    while True:
        if SERVO_TRACKING is True and shared.n_observed_faces.value > 0:

            target = np.array(shared.servo_target)
            error = target - pargs.frame_center

            Servos[0].value += xPID.update(error[0], sleep=0)
            Servos[1].value += yPID.update(error[1], sleep=0)

        if shared.new_keyboard_input.value is True:
            key_board_input = shared.keyboard_input.value

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

            shared.key_input_received[2] = True

        shared.servo_tracking.value = SERVO_TRACKING
        update_limiter()

    Servos.close()
    sys.exit()
