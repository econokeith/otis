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
                     (0, sin_x, cos_x)))

if __name__=='__main__':

    frame = np.zeros((500, 500, 3), dtype='uint8')
    pi_grid = np.linspace(0, 2 * np.pi, 100)
    pi_cycle = cycle(pi_grid)

    circle_points = np.zeros((100, 3), dtype=int)
    circle_points[:, 0] = 200 * np.sin(pi_grid)
    circle_points[:, 1] = 200 * np.cos(pi_grid)


    while True:
        frame[:, :, :] = 0
        angle = pi_cycle.__next__()
        _circle_points = np.dot(circle_points, find_Rx(angle)).astype(int)
        _circle_points = np.dot(_circle_points, find_Ry(angle)).astype(int)

        for point in _circle_points:
            cv2.circle(frame, point[:2] + np.array([250, 250]), 2, (255, 0, 0), thickness=-1)

        time.sleep(1 / 10)
        print(_circle_points[20])

        cv2.imshow("", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()