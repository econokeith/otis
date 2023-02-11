import itertools
import time
import numpy as np
from otis.helpers.timers import TimedCycle, SmartSleeper


# https://en.wikipedia.org/wiki/Spiral
def spiral_sphere_coordinates(radius,
                              c_spirals,
                              n_points,
                              center=(0, 0, 0),
                              order=(0, 1, 2),
                              dtype=int
                              ):

    grid = np.linspace(0, np.pi, n_points)
    _center = np.array(center)[list(order)]
    out = np.zeros((n_points, 3), dtype=float)
    sin_theta = np.sin(grid)
    cos_theta = np.cos(grid)
    c_sin_theta = np.sin(c_spirals * grid)
    c_cos_theta = np.cos(c_spirals * grid)
    out[:, 0] = radius * sin_theta * c_cos_theta + _center[0]
    out[:, 1] = radius * cos_theta + _center[1]
    out[:, 2] = radius * sin_theta * c_sin_theta + _center[2]

    return (out[:, list(order)]).astype(dtype)

def get_rotation_matrix(x=0, y=0, z=0):
    cos_x = np.cos(x)
    sin_x = np.sin(x)
    cos_y = np.cos(y)
    sin_y = np.sin(y)
    cos_z = np.cos(z)
    sin_z = np.sin(z)

    R_z = np.array([[cos_z, -sin_z, 0],
                    [sin_z, cos_z, 0],
                    [0, 0, 1]])

    R_y = np.array([[cos_y, 0, sin_y],
                    [0, 1, 0],
                    [-sin_y, 0, cos_y]])

    R_x = np.array([[1, 0, 0],
                    [0, cos_x, -sin_x],
                    [0, sin_x, cos_x]])

    # R_z = np.array([[cos_z, 0, sin_z],
    #                 [0,1,0],
    #                 [-sin_z, 0, cos_z]])
    #
    # R_y = np.array([[1, 0, 0],
    #                 [0, cos_y, -sin_y],
    #                [0, sin_y, cos_y]])

    return np.linalg.multi_dot([R_z, R_y, R_x])


def rotate_points(points, center, R):
    _points = points - center
    return np.dot(_points, R) + center


class Rotator3D:

    def __init__(self,
                 points=None,
                 origin=(0, 0, 0),
                 x_range=(0, 2 * np.pi),
                 y_range=(0, 2 * np.pi),
                 z_range=(0, 2 * np.pi),
                 periods=(0, 0, 0),
                 go_back=(False, False, False),
                 fps=30
                 ):

        if points is not None:
            self.original = np.copy(points)
            self._points = np.copy(points)

        self.origin = np.array(origin)
        self._x = 0
        self._y = 0
        self._z = 0
        self._R = np.empty((3, 3))
        self.x_range = x_range
        self.y_range = y_range
        self.z_range = z_range
        self.periods = periods
        self.fps = fps
        self.go_back = go_back

        self.d_angles = [0] * 3
        for i, period in enumerate(self.periods):
            if period != 0:
                self.d_angles[i] = 2 * np.pi / period / self.fps

    @property
    def n(self):
        return self.original.shape[0]

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, new_points):
        self.original = np.copy(new_points)
        self._points = np.copy(new_points)

    def rotate_to(self, x=None, y=None, z=None):

        self._x = x if x is not None else self._x
        self._y = y if y is not None else self._y
        self._z = z if z is not None else self._z

        self._R = get_rotation_matrix(self._x, self._y, self._z)
        self._points = self.original - self.origin
        self._points = (np.dot(self._points, self._R) + self.origin).astype(int)
        return self._points

    def periodic_rotate(self):
        self._x += self.d_angles[0]
        self._y += self.d_angles[1]
        self._z += self.d_angles[2]
        self.rotate_to()
        return self._points


if __name__ == '__main__':
    import cv2
    from otis.helpers.timers import TimeElapsedBool

    DIM = (1080, 1080)
    frame = np.zeros((*DIM[::-1], 3), 'uint8')
    frame_center = np.array([DIM[0] // 2, DIM[1] // 2, 0], int)
    # _sphere = spiral_sphere_coordinates(400, 20, 500, center= (540, 0, 540) , order=(1, 2, 0))
    sphere = spiral_sphere_coordinates(400, 100, 2000, center=(540, 540, 0))
    rotator = Rotator3D(sphere, frame_center, periods=(10, 3, 9))
    HIDE = True

    # axis = np.array([
    #     [540, 0, 0], [540, 1080, 0],
    #     [0, 540, 0], [1080, 540, 0],
    #     [540,540, 540], [540,540,-540]
    # ], int)
    long_line = 100000

    axis = np.array([
        [540, -long_line, 0], [540, long_line, 0],
        [-long_line, 540, 0], [long_line, 540, 0],
        [540, 540, long_line], [540, 540, -long_line]
    ], int)

    stop_timer = TimeElapsedBool(60)
    sleeper = SmartSleeper(1 / 30)

    while True:
        frame[:, :, :] = 0
        _sphere = rotator.periodic_rotate()
        _axis = rotate_points(axis, frame_center, rotator._R).astype(int)

        cv2.line(frame, _axis[0, :2], _axis[1, :2], (255, 0, 0), 3, lineType=cv2.LINE_AA)
        cv2.line(frame, _axis[2, :2], _axis[3, :2], (255, 0, 0), 3, lineType=cv2.LINE_AA)
        cv2.line(frame, _axis[4, :2], _axis[5, :2], (255, 0, 0), 3, lineType=cv2.LINE_AA)

        for i in range(_sphere.shape[0] - 1):
            p0 = _sphere[i]
            p1 = _sphere[i + 1]
            if p0[2] > 0 or p1[2] > 0 or HIDE is False:
                cv2.line(frame, p0[:2], p1[:2], (0, 255, 0), 1, lineType=cv2.LINE_AA)
                if p0[2] > 0:
                    cv2.circle(frame, p0[:2], 1, (0, 0, 255), -1)
                if p0[1] > 0:
                    cv2.circle(frame, p1[:2], 1, (0, 0, 255), -1)

        cv2.imshow('', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        sleeper(1 / 30)

    cv2.destroyAllWindows()
