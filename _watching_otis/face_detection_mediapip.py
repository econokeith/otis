import cv2
import mediapipe as mp
import numpy as np
import bisect
from typing import Union, Tuple, List

from otis import helpers
from otis.camera import CameraPlayer, ThreadedCameraPlayer
from otis.overlay import assetholders, shapes
from otis.overlay.textwriters import textwriters
from otis.helpers import colortools, timers

from _piardservo.container import ServoContainer
from _piardservo.microcontrollers import RPiWifi
from _piardservo.pid import PIDController


mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
f_dim = (1080, 1080)

SERVO_TRACKING = True
UPDATE_FACTOR = 4
MAX_SERVO_UPDATES_PER_SECOND = 5 * UPDATE_FACTOR

# _X_PID_VALUES = (2e-4/4, 1e-10, 2e-7/4)
# Y_PID_VALUES = (5e-5/4,1e-10, 2e-7/4)
X_PID_VALUES = (2e-4/UPDATE_FACTOR, 1e-10, 1e-7/UPDATE_FACTOR)
Y_PID_VALUES = (2e-4/UPDATE_FACTOR, 1e-10, 1e-7/UPDATE_FACTOR)

MINIMUM_MOVE_SIZE_PIXELS = 5
SERVO_START = np.array((-.06, -.72))/2
KEYBOARD_MOVE_INCREMENT = -.01
STEPS_TO_RESET = 2
SERVO_ADDRESS = '192.168.1.115'
SERVO_PINS = (17, 22)

RADIUS_SCALE = 1.2


def main():
    capture = ThreadedCameraPlayer(c_dim='1080p',
                                   f_dim=(1080, 1080),
                                   start=True,
                                   max_fps=30
                                   )
    ####################################################################################
    face_detection = mp_face_detection.FaceDetection(model_selection=1,
                                                     min_detection_confidence=.75
                                                     )

    bbox = assetholders.BoundingAsset(asset=shapes.ServoFaceTracker(radius_scale=RADIUS_SCALE),
                                      color='g',
                                      name_tag_border=False,
                                      update_format='ltwh',
                                      moving_average=(3, 3, 10, 10)
                                      )

    screen_grid = ScreenGrid(f_dim, 8, 8)
    frame_center = np.array((f_dim[0]//2, f_dim[1]//2))
    #######################################################################################

    rpi = RPiWifi(address=SERVO_ADDRESS, pins=SERVO_PINS)
    Servos = ServoContainer(n=2,
                            microcontroller=rpi,
                            min_pulse_width=600,
                            max_pulse_width=2400).connect()

    Servos[0].value, Servos[1].value = SERVO_START

    xPID = PIDController(*X_PID_VALUES)
    yPID = PIDController(*Y_PID_VALUES)

    update_limiter = timers.CallFrequencyLimiter(1 / MAX_SERVO_UPDATES_PER_SECOND)
    fps_writer = textwriters.InfoWriter(text_fun=lambda x: f'fps = {x}', coords=(50,50))
    fps_average = helpers.maths.MovingAverage(10)
    fps_timer = timers.TimeSinceLast(True)

    while True:
        success, frame = capture.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue


        results = face_detection.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        if results.detections:
            bbox.coords = mediapipe_box_abs(results.detections[0], frame)

            frame_center_distance = helpers.maths.linear_distance(bbox.center, frame_center)

            if frame_center_distance > bbox.radius * RADIUS_SCALE:
                screen_grid.find_sector(bbox.center, colorize=(frame, 0, 150))
                screen_grid.write(frame)

            bbox.write(frame)

            if update_limiter() is True and SERVO_TRACKING is True:
                error = bbox.center - frame_center
                Servos[0].value += xPID.update(error[0], sleep=0)
                Servos[1].value += yPID.update(error[1], sleep=0)


        fps_writer.write(frame, int(fps_average(fps_timer())))
        # Flip the frame horizontally for a selfie-view display.
        capture.show()
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break



    capture.stop()
    Servos.close()


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



if __name__ == '__main__':
    main()

