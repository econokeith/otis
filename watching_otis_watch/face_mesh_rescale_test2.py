import cv2
import mediapipe as mp
import math
import numpy as np

from mediapipe.python.solutions.face_mesh_connections import FACEMESH_TESSELATION

from otis import camera
from otis.helpers.colortools import color_function, ColorCycle
from otis.helpers.maths import MovingAverage
from otis.overlay.bases import TextType
from otis.overlay.shapes import Rectangle, Circle

face_oval = frozenset([(10, 338), (338, 297), (297, 332), (332, 284),
                       (284, 251), (251, 389), (389, 356), (356, 454),
                       (454, 323), (323, 361), (361, 288), (288, 397),
                       (397, 365), (365, 379), (379, 378), (378, 400),
                       (400, 377), (377, 152), (152, 148), (148, 176),
                       (176, 149), (149, 150), (150, 136), (136, 172),
                       (172, 58), (58, 132), (132, 93), (93, 234),
                       (234, 127), (127, 162), (162, 21), (21, 54),
                       (54, 103), (103, 67), (67, 109), (109, 10)]
                      )

oval_set = set([])
for point in face_oval:
    oval_set.add(point[0])
    oval_set.add(point[1])

oval_set = frozenset(oval_set)
oval_list = list(oval_set)
oval_len = len(oval_set)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

color_cycle = ColorCycle()

face_drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=0, color=(0, 255, 0))
face_style = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)
_N_FACE_LANDSMARKS = 468
DIM = (1920, 1080)
LINE_THICKNESS = 2
TARGET_WIDTH = 200
radius = 3

def main():
    capture = cv2.VideoCapture(0)
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, DIM[0])
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, DIM[1])
    average_height = MovingAverage(10)
    average_width = MovingAverage(10)

    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                      refine_landmarks=False,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5
                                      )

    x_values = np.empty(_N_FACE_LANDSMARKS, dtype=float)
    y_values = np.empty(_N_FACE_LANDSMARKS, dtype=float)
    xy_pixels = np.empty((_N_FACE_LANDSMARKS, 2), dtype=int)
    square = Rectangle(coords=(1760, 160, 300, 300),
                       coord_format='cwh',
                       color='b',
                       thickness=-1
                       )

    # X_CROSS = (127, 356)
    xc0, xc1 = X_CROSS = (234, 454)
    xc10, xc11 = (93, 323)
    yc0, yc1 = Y_CROSS = (10, 152)

    square_center = np.array((1760, 160), dtype=int)

    circle = Circle(center=square_center,
                    radius=3,
                       color='w',
                       thickness=-1
                    )

    while True:
        success, image = capture.read()

        if not success:
            continue

        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.flip(image, 1)
        face_results = face_mesh.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image.flags.writeable = True


        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                landmarks_list = face_landmarks.landmark
                num_landmarks = len(landmarks_list)
                xy_pixels[:,:] = convert_landmarks_to_pixels(landmarks_list, image)
                # x_bounds = (127, 356)
                # (234, 454)
                # y_bounds = (10, 152)
                square.write(image)
                circle.write(image)

                center_y_line = ((xy_pixels[yc0]+ xy_pixels[yc1])//2).astype(int)
                center_x_line = ((xy_pixels[xc0] + xy_pixels[xc1])//2).astype(int)
                center_x1_line = ((xy_pixels[xc11] + xy_pixels[xc10])//2).astype(int)
                center_center_x = ((center_x1_line+center_x_line)//2).astype(int)

                average_height.update(find_landmark_distance(landmarks_list[yc0], landmarks_list[yc1], image))
                average_width.update(find_landmark_distance(landmarks_list[xc10], landmarks_list[xc11], image))

                avg_w = int(average_height())
                avg_h = int(average_width())
                ratio = avg_h / avg_w

                xy_pixels = (xy_pixels-center_center_x) * TARGET_WIDTH/avg_w + square_center
                xy_pixels = xy_pixels.astype(int)


                # Draws the connections if the start and end landmarks_list are both visible.
                for i, connection in enumerate(FACEMESH_TESSELATION):

                    start_idx = connection[0]
                    end_idx = connection[1]

                    if not (0 <= start_idx < num_landmarks and 0 <= end_idx < num_landmarks):
                        raise ValueError(f'Landmark index is out of range. Invalid connection '
                                         f'from landmark #{start_idx} to landmark #{end_idx}.')


                    cv2.line(image, xy_pixels[start_idx], xy_pixels[end_idx], (0,255,0), 1)

                # for point in oval_set:
                #     cv2.circle(frame, xy_pixels[point], 2, (0,255,0),-1)

            # mp_drawing.draw_landmarks(
            #     frame=frame,
            #     landmark_list=face_landmarks,
            #     connections=mp_face_mesh.FACEMESH_TESSELATION,
            #     landmark_drawing_spec=face_drawing_spec,
            #     connection_drawing_spec=face_style
            # )

        cv2.imshow('face', cv2.resize(image, (0,0),fx=1, fy=1))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()

########################################################################################################################

def convert_landmarks_to_pixels(landmarks_list, image):
    n_landmarks = len(landmarks_list)
    x_values = np.empty(n_landmarks, dtype=float)
    y_values = np.empty(n_landmarks, dtype=float)
    xy_pixels = np.empty((n_landmarks, 2), dtype=int)

    image_height, image_width, _ = image.shape

    for i, landmark in enumerate(landmarks_list):
        x_values[i] = landmark.x
        y_values[i] = landmark.y

    xy_pixels[:,0] = np.minimum(x_values * image_width, image_width - 1).astype(int)
    xy_pixels[:,1] = np.minimum(y_values * image_height, image_height - 1).astype(int)

    return xy_pixels



def find_landmark_distance(lm0, lm1, image):
    image_height, image_width, _ = image.shape
    p0 = np.empty(3, dtype=int)
    p1 = np.empty(3, dtype=int)
    p0[0] = min(int(lm0.x * image_width), image_width - 1)
    p0[1] = min(int(lm0.y * image_height), image_height - 1)
    p0[2] = min(int(lm0.z * image_width), image_width - 1)
    p1[0] = min(int(lm1.x * image_width), image_width - 1)
    p1[1] = min(int(lm1.y * image_height), image_height - 1)
    p1[2] = min(int(lm1.z * image_width), image_width - 1)

    return int(np.linalg.norm(p0-p1))


if __name__=='__main__':
    main()


