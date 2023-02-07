import time

import numpy as np
import cv2

from itertools import cycle

# period = np.pi/20
#
# cos_x = np.cos(angle)
# sin_x = np.sin(angle)
#
# R_x = np.array(((1, 0, 0),
#                 (0, cos_x, -sin_x),
#                 (0, sin_x, cos_x)))
#
# R_y = np.array(((cos_x, 0, sin_x),
#                 (0, 1, 0),
#                 (-sin_x, 0, cos_x)))
#
# R_z = np.array(
#               ((cos_x, -sin_x, 0),
#                (sin_x, cos_x, 0),
#                (0, 0, 1))
# )
#
# point = np.array([[200, 200, 0]])
# center = np.array([[250, 250, 0]])

def find_Rz(angle):
    cos_x = np.cos(angle)
    sin_x = np.sin(angle)
    return np.array(
              ((cos_x, -sin_x, 0),
               (sin_x, cos_x, 0),
               (0, 0, 1)))

def find_Ry(angle):
    cos_x = np.cos(angle)
    sin_x = np.sin(angle)
    return np.array(((cos_x, 0, sin_x),
                    (0, 1, 0),
                    (-sin_x,0, cos_x)))

def find_Rx(angle):
    cos_x = np.cos(angle)
    sin_x = np.sin(angle)
    return np.array(((1, 0, 0),
                     (0, cos_x, -sin_x),
                     (0, sin_x, cos_x))
                    )

if __name__=='__main__':

    frame = np.zeros((500, 500, 3), dtype='uint8')
    pi_grid = np.linspace(0, 2 * np.pi, 100)
    pi_cycle = cycle(pi_grid)

    z_grid = np.linspace(0, 2 * np.pi, 20)
    z_cycle = cycle(z_grid)

    circle_points = np.zeros((400, 3), dtype=int)
    circle_points[:100, 0] = 200 * np.sin(pi_grid)
    circle_points[:100, 1] = 200 * np.cos(pi_grid)

    circle_points[100:200, 0] = 100 * np.sin(pi_grid)
    circle_points[100:200, 1] = 100 * np.cos(pi_grid)
    circle_points[200:300, 0] = 100 * np.sin(pi_grid)
    circle_points[200:300, 1] = 100 * np.cos(pi_grid)
    circle_points[300:400, 0] = 100 * np.sin(pi_grid)
    circle_points[300:400, 1] = 100 * np.cos(pi_grid)

    circle_points[100:200] += np.array([0, 0, 100])
    circle_points[200:300] += np.array([0, 0, -100])

    white_line_points = np.array([[0,0, 100], [0, 0, -100]])

    while True:
        frame[:, :, :] = 0
        angle = pi_cycle.__next__()
        z_angle = z_cycle.__next__()
        rotation_matrix = np.linalg.multi_dot([find_Rz(z_angle), find_Ry(-angle), find_Rx(angle)])
        _circle_points = np.dot(circle_points, rotation_matrix).astype(int) + np.array([250, 250, 0])
        # cv2.line(frame, _circle_points[0, :2], _circle_points[24, :2], (255, 255, 0), 2)
        # cv2.line(frame, _circle_points[24, :2], _circle_points[49, :2], (255, 255, 0), 2)
        # cv2.line(frame, _circle_points[49, :2], _circle_points[74, :2], (255, 255, 0), 2)
        # cv2.line(frame, _circle_points[74, :2], _circle_points[0, :2], (255, 255, 0), 2)
        _white_line_points = np.dot(white_line_points, rotation_matrix).astype(int)+ np.array([250, 250, 0])

        _THICKNESS = 1

        cv2.line(frame, _white_line_points[0, :2], _white_line_points[1, :2], (0, 0, 255), 2)

        # cv2.line(frame, _circle_points[24, :2], _circle_points[, :2], (255, 255, 0), 1)
        # cv2.line(frame, _circle_points[0, :2], _circle_points[12, :2], (255, 255, 0), 1)
        cv2.line(frame, _circle_points[100, :2], _circle_points[149, :2], (255, 0, 0), _THICKNESS)
        cv2.line(frame, _circle_points[124, :2], _circle_points[173, :2], (255, 0, 0), _THICKNESS)

        cv2.circle(frame, _white_line_points[0, :2], 5, (255, 0, 0), -1)

        cv2.line(frame, _circle_points[0, :2], _circle_points[49, :2], (0, 0, 255), _THICKNESS)
        cv2.line(frame, _circle_points[24, :2], _circle_points[73, :2], (0, 0, 255), _THICKNESS)

        cv2.line(frame, _circle_points[300, :2], _circle_points[349, :2], (0, 255, 0), _THICKNESS)
        cv2.line(frame, _circle_points[324, :2], _circle_points[373, :2], (0, 255, 0), _THICKNESS)

        cv2.circle(frame, (250, 250), 5, (0, 255, 0), -1)

        cv2.line(frame, _circle_points[200, :2], _circle_points[249, :2], (255, 0, 255), _THICKNESS)
        cv2.line(frame, _circle_points[224, :2], _circle_points[273, :2], (255, 0, 255), _THICKNESS)

        cv2.circle(frame, _white_line_points[1, :2], 5, (255, 0, 255), -1)

        for point in _circle_points[:100]:
            cv2.circle(frame, point[:2], 2, (0, 0, 255), thickness=-1)

        for point in _circle_points[100:200]:
            cv2.circle(frame, point[:2], 2, (255, 0, 0), thickness=-1)

        for point in _circle_points[200:300]:
            cv2.circle(frame, point[:2], 2, (255, 0, 255), thickness=-1)

        for point in _circle_points[300:]:
            cv2.circle(frame, point[:2], 2, (0, 255, 0), thickness=-1)

        time.sleep(1 / 30)
        cv2.imshow("", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()