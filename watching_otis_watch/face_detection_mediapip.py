import cv2
import mediapipe as mp
import numpy as np
import bisect
from typing import Union, Tuple, List

from otis import helpers
from otis.camera import CameraPlayer
from otis.overlay import assetholders, shapes
from otis.overlay.textwriters import textwriters
from otis.helpers import colortools


mp_face_detection = mp.solutions.face_detection
mp_drawing = mp.solutions.drawing_utils
f_dim = (1080, 1080)
x_divide = 8
y_divide = 8


def main():
    cap = CameraPlayer(c_dim='1080p',
                       f_dim=(1080, 1080)
                       )

    face_detection = mp_face_detection.FaceDetection(model_selection=1,
                                                     min_detection_confidence=.75
                                                     )

    bbox = assetholders.BoundingAsset(asset=shapes.ServoFaceTracker(),
                                      color='g',
                                      name_tag_border=False,
                                      update_format='ltwh',
                                      moving_average=(10, 10, 10, 10)
                                      )

    screen_grid = ScreenGrid(f_dim, 8, 8)
    frame_center = f_dim[0]//2, f_dim[1]//2


    while True:
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue

        results = face_detection.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        if results.detections:
            bbox.coords = mediapipe_box_abs(results.detections[0], image)
            box_center = bbox.center
            frame_center_distance = helpers.maths.linear_distance(box_center, frame_center)

            if frame_center_distance > bbox.radius:
                screen_grid.find_sector(box_center, colorize=(image, 0, 100))
                screen_grid.write(image)

            bbox.write(image)

        # Flip the image horizontally for a selfie-view display.
        cv2.imshow('MediaPipe Face Detection', image)
        if cv2.waitKey(5) & 0xFF == 27:
            break

    cap.stop()


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

