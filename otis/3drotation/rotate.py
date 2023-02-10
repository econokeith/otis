import itertools
import time


import numpy as np
from otis.helpers.timers import TimedCycle, SmartSleeper


def spiral_sphere_coordinates(radius, c_spirals, n_points, center=(0,0,0), order=(0,1,2),dtype=int):
    grid = np.linspace(0, np.pi, n_points)
    out = np.zeros((n_points, 3), dtype=float) + center
    sin_theta = np.sin(grid)
    cos_theta = np.cos(grid)
    c_sin_theta = np.sin(c_spirals * grid)
    c_cos_theta = np.cos(c_spirals * grid)
    out[:, 0] += radius * sin_theta * c_cos_theta
    out[:, 1] += radius * sin_theta * c_sin_theta
    out[:, 2] += radius * cos_theta
    return out[:, list(order)].astype(dtype)

def get_rotation_matrix(x=0, y=0, z=0):
    cos_x = np.cos(x)
    sin_x = np.sin(x)
    cos_y = np.cos(y)
    sin_y = np.sin(y)
    cos_z = np.cos(z)
    sin_z = np.sin(z)

    R_x = np.array([[cos_x, -sin_x, 0],
                    [sin_x, cos_x, 0],
                    [0, 0, 1]])

    R_y = np.array([[cos_y, 0, sin_y],
                    [0,1,0],
                    [-sin_y, 0, cos_y]])

    R_z = np.array([[1, 0, 0],
                    [0, cos_z, -sin_z],
                   [0, sin_z, cos_z]])

    return np.linalg.multi_dot([R_z, R_y, R_x])

def rotate_points(points, center, R):
    _points = points - center
    return np.dot(_points, R) + center


if __name__ == '__main__':

    RECORD = False
    import cv2
    import os
    from otis.helpers.timers import TimeElapsedBool

    frame_center = np.array([540, 540, 0], int)
    # sphere = spiral_sphere_coordinates(400, 300, 500, center=frame_center)

    frame = np.zeros((1080, 1080, 3),'uint8')
    background_cycler = TimedCycle(max_i=20, cycle_t=1.3, updown=True)


    x_grid = np.linspace(0, 2*np.pi, 100)
    y_grid = np.linspace(0, 2 * np.pi, 100)
    z_grid = np.linspace(0, 2 * np.pi, 100)

    x_cycle = itertools.cycle(list(x_grid))
    y_cycle = itertools.cycle(list(y_grid))
    z_cycle = itertools.cycle(list(z_grid))
    sphere = spiral_sphere_coordinates(400, 300, 500, center=frame_center)
    r_grid = np.linspace(.9, 1.1, 500)
    r_cycle = np.append(r_grid, r_grid[::-1])
    r_cycle = itertools.cycle(list(r_cycle))

    c_cycle = list(np.linspace(10, 200, 600))
    c_cycle = itertools.cycle(c_cycle + c_cycle[::-1])
    c_cycle = itertools.cycle(c_cycle)
    cycler = list(np.linspace(0, 1, 500))
    cycler = itertools.cycle(cycler + cycler[::-1])

    C0 = 200
    P0 = 500


    file_name = '/home/keith/Dropbox/otis_films/3d Rotations/rotating_sphere2.mp4'
    HIDE = True

    if RECORD is True:
        recorder = cv2.VideoWriter(file_name,
                                   cv2.VideoWriter_fourcc(*'mp4v'),
                                   30,
                                   (720, 720)
                                   )

    stop_timer = TimeElapsedBool(60)
    sleeper = SmartSleeper(1/30)
    while True:
        frame[:, :, :] = background_cycler()

        a_x = next(x_cycle)
        a_y = next(y_cycle)
        a_z = next(z_cycle)
        r_new = next(r_cycle)
        c_new = next(c_cycle)
        CC = next(cycler)

        sphere = spiral_sphere_coordinates(400, c_new, 500, center=frame_center)
        _sphere = (sphere - frame_center)
        # # _sphere = (sphere - frame_center)*r_new
        R = get_rotation_matrix(0, 0, np.pi/3.5)
        _sphere = (np.dot(_sphere, R)  + frame_center).astype(int)

        # for point in _sphere:
        #     if point[2] > 0:
        #         cv2.circle(frame, point[:2], 2, (0, 0, 255), -1)

        for i in range(len(sphere)-1):
            p0 = _sphere[i]
            p1 = _sphere[i + 1]
            if p0[2] > 0 or p1[2] > 0 or HIDE is False:
                cv2.line(frame, p0[:2], p1[:2], (0, 255, 0), 1, lineType=cv2.LINE_AA)
                cv2.circle(frame, p0[:2], 2, (0, 0, 255), -1)
                cv2.circle(frame, p1[:2], 2, (0, 0, 255), -1)

        if RECORD is True:
            recorder.write(cv2.resize(frame, (720, 720)))

        cv2.imshow('', frame)
        xx = cv2.waitKey(1) & 0xFF
        if xx == ord('q'):
            break

        if stop_timer() is True:
            break

        sleeper()

    cv2.destroyAllWindows()
    if RECORD:
        recorder.release()

