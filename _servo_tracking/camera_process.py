import queue
import signal
import sys
import bisect

from typing import Tuple, Union

import cv2
import numpy as np

from otis import helpers
from otis.camera import ThreadedCameraPlayer
from otis.helpers import multitools, cvtools, coordtools, colortools, timers
from otis.overlay import scenes, imageassets, assetholders, textwriters, shapes

RADIUS_SCALE = 1.2
COLUMNS = 8
ROWS = 8



def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)

    ####################################### SETUP #####################################################################

    manager = scenes.SceneManager(shared, pargs, file=__file__)
    capture = manager.capture  # for convenience


    capture1 = ThreadedCameraPlayer(4, flip=False, max_fps=30, c_dim='720p', f_dim=(720, 720))

    fps_writer = textwriters.InfoWriter(text_fun=lambda x: f'fps = {x}', coords=(50,50))
    fps_average = helpers.maths.MovingAverage(10)
    fps_timer = timers.TimeSinceLast(True)

    bbox = assetholders.BoundingAsset(asset=shapes.ServoFaceTracker(radius_scale=RADIUS_SCALE),
                                      color='g',
                                      name_tag_border=False,
                                      update_format='ltwh',
                                      moving_average=(3, 3, 10, 10)
                                      )

    screen_grid = ScreenGrid(pargs.f_dim, COLUMNS, ROWS)

    ########################################## setup for intro screen #################################################
    show_info=True

    while True:

        ############################### ##graphics ####################################################################

        success, frame = capture.read()
        if not success:
            continue

        success1, frame1 = capture1.read()
        if not success1:
            continue

        shared.frame[:] = frame  # latest frame copied to shared frame

        if shared.n_observed_faces.value > 0:
            bbox.coords = shared.bbox_coords[0]
            frame_center_distance = helpers.maths.linear_distance(bbox.center, pargs.frame_center)
            shared.servo_target[:] = bbox.center

            if frame_center_distance > bbox.radius * RADIUS_SCALE:
                screen_grid.find_sector(bbox.center, colorize=(frame, 0, 150))
                screen_grid.write(frame)

            bbox.write(frame)
        if show_info is True:
            fps_writer.write(frame, int(fps_average(fps_timer())))
        # Flip the frame horizontally for a selfie-view display.
        frame[770:1070, 770:1070] = cv2.resize(frame1, (300, 300))

        capture.show()
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
            shared.new_keyboard_input.value = False           # probably shoulda just been a variable with a lock
            shared.key_input_received[:] = False
            shared.keyboard_input.value = 255

    # exit and destroy frames, etc
    capture.stop()
    sys.exit()


#######################################################################################################################
########################   Extra ad hoc Object Managers                   #############################################
#######################################################################################################################

def mediapipe_box_abs(detection, image):
    image_height, image_width = image.shape[:2]
    box = detection.location_data.relative_bounding_box
    xmin = int(box.xmin * image_width)
    ymin = int(box.ymin * image_height)
    h = int(box.height * image_height)
    w = int(box.width * image_width)
    return xmin, ymin, w, h

class ScreenGrid:

    def __init__(self,
                 dim: Tuple[int, int]= (1920, 1080),
                 columns: int = 8,
                 rows: int = 8,
                 color: Union[str, Union[Tuple[int, int, int]]] = 'grey',
                 thickness: int = 1,
                 x_bounds: Union[None, Tuple[int, int]]=None,
                 y_bounds: Union[None,  Tuple[int, int]] = None,
                 ):
        """

        Args:
            dim:
            columns:
            rows:
            color:
            thickness:
            x_bounds:
            y_bounds:
        """

        self.dim = dim
        self.columns = columns
        self.rows = rows
        self.color = colortools.color_function(color)
        self.thickness = thickness
        self.x_start = 0 if x_bounds is None else x_bounds[0]
        self.x_stop = self.dim[0] if x_bounds is None else x_bounds[1]
        self.y_start = 0 if y_bounds is None else y_bounds[0]
        self.y_stop = self.dim[1] if y_bounds is None else y_bounds[1]

        self.x_grid = np.linspace(self.x_start, self.x_stop,  self.columns, dtype=int)
        self.y_grid = np.linspace(self.y_start, self.y_stop, self.rows, dtype=int)

        self.grid_line = shapes.Line(color=self.color, thickness=self.thickness)

    def write(self, frame):
        for x in self.x_grid[1:-1]:
            coords = (x, self.y_grid[0], x, self.y_grid[-1])
            self.grid_line.write(frame, coords=coords)

        for y in self.y_grid[1:-1]:
            coords = (self.x_grid[0], y, self.x_grid[-1], y)
            self.grid_line.write(frame, coords=coords)

    def find_sector(self, point: Tuple[int, int], colorize: Union[None, Tuple[np.ndarray, int, int]] =None):
        x_idx = bisect.bisect_left(self.x_grid, point[0])
        y_idx = bisect.bisect_left(self.y_grid, point[1])

        if colorize is not None:
            frame, pixel_idx, value = colorize
            x0, x1 = self.x_grid[x_idx-1], self.x_grid[x_idx]
            y0, y1 = self.y_grid[y_idx-1], self.y_grid[y_idx]
            colortools.colorize_frame(frame[y0:y1+1, x0:x1+1], pixel_idx, value)

        return x_idx, x_idx + 1, y_idx, y_idx + 1