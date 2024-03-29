import signal
import sys

import cv2
import numpy as np

from otis import helpers
from otis.camera import ThreadedCameraPlayer
from otis.helpers import multitools, timers, colortools
from otis.overlay import scenes, assetholders, textwriters, shapes
from otis.overlay.screeneffects import ScreenGrid

RADIUS_SCALE = 1.2
COLUMNS = 8
ROWS = 8
RUN_DURATION = 120
WINDOW_OFFSET = 20
FRAME_1_SIZE = 350, 350

def target(shared, pargs):

    ####################################### SETUP #####################################################################

    capture0 = ThreadedCameraPlayer(0,
                                    max_fps=pargs.max_fps,
                                    c_dim=pargs.c_dim,
                                    flip=True,
                                    record=pargs.record,
                                    record_to=pargs.record_to,
                                    f_dim=pargs.f_dim,
                                    ).start()

    capture1 = ThreadedCameraPlayer(4,
                                    flip=False,
                                    max_fps=30,
                                    c_dim='720p',
                                    f_dim=(720, 720)
                                    )

    def close_gracefully(sig, frame):


        capture0.stop()
        capture1.stop()
        print('[info] Camera(s) Closed')
        sys.exit()

    signal.signal(signal.SIGTERM, close_gracefully)
    signal.signal(signal.SIGINT, close_gracefully)

    fps_writer = textwriters.InfoWriter(text_fun=lambda x: f'fps = {x}', coords=(50, 50))
    fps_average = helpers.maths.MovingAverage(10)
    fps_timer = timers.TimeSinceLast(True)

    bbox = assetholders.BoundingAsset(asset=shapes.ServoFaceTracker(radius_scale=RADIUS_SCALE),
                                      name_tag_border=False,
                                      update_format='ltwh',
                                      moving_average=(3, 3, 10, 10)
                                      )

    screen_grid = ScreenGrid(pargs.f_dim, COLUMNS, ROWS)

    blinker = timers.Blinker(cycle_time=.2)
    stop_timer = timers.TimeElapsedBool(RUN_DURATION) # since mediapipe breaks key inputs, i have to set a hard timer
                                                      # for stops, otherwise the other processes don't quit

    ########################################## setup for intro screen #################################################
    show_info = False
    TIMER_BEGIN = False

    while True:

        ############################### ##graphics ####################################################################

        success, frame0 = capture0.read()
        if not success:
            continue

        success1, frame1 = capture1.read()
        if not success1:
            continue

        if TIMER_BEGIN is False:
            TIMER_BEGIN = True
            stop_timer()

        shared.frame[:] = frame0  # latest frame copied to shared frame

        if shared.n_observed_faces.value > 0:
            bbox.coords = shared.bbox_coords[0]
            frame_center_distance = helpers.maths.linear_distance(bbox.center, pargs.frame_center)
            shared.servo_target[:] = bbox.center

            if frame_center_distance > bbox.radius * RADIUS_SCALE:
                # if blinker():
                #     colortools.colorize_frame(frame0, 2, 50)
                screen_grid.find_sector(bbox.center, colorize=(frame0, 0, 150))
                screen_grid.write(frame0)

            bbox.write(frame0)

        if show_info is True:
            fps_writer.write(frame0, int(fps_average(fps_timer())))

        frame1 = cv2.resize(frame1, FRAME_1_SIZE)
        y_1, x_1, _ = frame1.shape
        dim = pargs.f_dim
        frame0[dim[1] - WINDOW_OFFSET - y_1:dim[1] - WINDOW_OFFSET, dim[0] -
                                                                    WINDOW_OFFSET - x_1:dim[0] - WINDOW_OFFSET] = frame1

        capture0.show()
        ############################ keyboard inputs ###################################################################

        keyboard_input = cv2.waitKey(1) & 0xFF  # only camera process receives the keyboard input

        # could probably have done without the new_keyboard_input and done it around the value of keyboard_input
        if shared.new_keyboard_input.value is False and keyboard_input != 255:  # 255 is the value given for no input

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            # if shared.new_keyboard_input.value is True and shared.key_input_received[0] is False:

            if shared.keyboard_input.value == ord('q'):  # exit / destroy windows on 'q'
                break

            elif shared.keyboard_input.value == ord('1'):  # toggle info data on screen
                show_info = not show_info

            shared.key_input_received[0] = True  # set as received

        if np.count_nonzero(shared.key_input_received) == 3:  # reset once all have processes have received the input
            shared.new_keyboard_input.value = False  # probably shoulda just been a variable with a lock
            shared.key_input_received[:] = False
            shared.keyboard_input.value = 255

        if stop_timer() is True:
            break

    # exit and destroy frames, etc
    shared.keyboard_input.value = ord('q')
    shared.new_keyboard_input.value = True

    capture0.stop()
    capture1.stop()
    sys.exit()


#######################################################################################################################
########################   Extra ad hoc Object Managers                   #############################################
#######################################################################################################################

