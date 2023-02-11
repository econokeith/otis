import itertools
import time
import numpy as np
from otis.helpers.timers import TimedCycle, SmartSleeper
from otis.rotations.rotationtools import get_rotation_matrix


class RigidBody3D:

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
            self.original = np.copy(points).astype(int)
            self._points = np.copy(points).astype(int)

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

    def rotate_by(self, x=0, y=0, z=0):
        self._x += x
        self._y += y
        self._z += z

        self._R = get_rotation_matrix(self._x, self._y, self._z)
        self._points = self.original - self.origin
        self._points = (np.dot(self._points, self._R) + self.origin).astype(int)
        return self._points

