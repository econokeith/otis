import itertools
import time
import numpy as np
import cv2

from otis.helpers.timers import TimedCycle, SmartSleeper, TimeElapsedBool
from otis.helpers.colortools import color_function
from otis.rotations.rotationtools import get_rotation_matrix, spiral_sphere_coordinates

class RigidBody3D:

    def __init__(self,
                 points=None,
                 origin=(0, 0, 0),
                 x_range=(0, 2 * np.pi),
                 y_range=(0, 2 * np.pi),
                 z_range=(0, 2 * np.pi),
                 periods=(0, 0, 0),
                 go_back=(False, False, False),
                 fps=30,
                 ltype=cv2.LINE_AA,
                 e_color='g',
                 n_color='r',
                 n_radius=1,
                 n_thickness=1,
                 e_thickness=1,
                 ):

        if points is not None:
            self.original = np.copy(points).astype(int)
            self._points = np.copy(points).astype(int)

        self._origin = np.array(origin)
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

        self.ltype = ltype

        self.e_color = color_function(e_color)
        self.n_color = color_function(n_color)

        self.n_radius = int(n_radius)

        self.e_thickness = e_thickness
        self.n_thickness = n_thickness

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

    @property
    def origin(self):
        return self._origin

    @origin.setter
    def origin(self, new_origin):
        self._points -= self.origin - new_origin
        self._origin = new_origin

    def update_original(self):
        self.original = self._points.copy()

    def resize(self, scale):
        self._points = ((self._points - self._origin) * scale ).astype(int)+ self._origin


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

    def rotate_by_R(self, R):
        self._R = R
        self._points = self.original - self.origin
        self._points = (np.dot(self._points, self._R) + self.origin).astype(int)

        return self._points

class SpiralSphere(RigidBody3D):

    def __init__(self,
                 radius,
                 c_spirals,
                 n_points,
                 origin=(0, 0, 0),
                 order=(0,1,2),
                 hide=False,

                 **kwargs
                 ):

        self._n_radius = n_points
        self._c_spirals = c_spirals
        self._n_points = n_points

        sphere = spiral_sphere_coordinates(radius,
                                           c_spirals,
                                           n_points,
                                           center=origin,
                                           order=order
                                           )

        super().__init__(points=sphere,
                         origin=origin,
                         **kwargs
                         )

        self.hide = hide


    def write(self, frame):
        _sphere = self.points
        for i in range(self.n - 1):
            p0 = _sphere[i]
            p1 = _sphere[i + 1]

            if p0[2] > 0 or p1[2] > 0 or self.hide is False:
                cv2.line(frame, p0[:2], p1[:2], self.e_color,
                         self.e_thickness, lineType=self.ltype)

                if (p0[2] > 0 or self.hide is False) and self.n_radius > 0:

                    cv2.circle(frame,
                               p0[:2],
                               self.n_radius,
                               self.n_color,
                               self.n_thickness,
                               lineType=self.ltype
                               )

                if (p0[1] > 0 or self.hide is False) and self.n_radius > 0:

                    cv2.circle(frame, p1[:2],
                               self.n_radius,
                               self.n_color,
                               self.n_thickness,
                               lineType=self.ltype
                               )

if __name__=='__main__':

    DIM = (1080, 1080)
    frame = np.zeros((*DIM[::-1], 3), 'uint8')
    frame_center = np.array([DIM[0] // 2, DIM[1] // 2, 0], int)

    sphere = SpiralSphere(400, 15, 300,
                          origin=(540, 540, 0),
                          periods=(0, 1, 0),
                          hide=False
                          )

    stop_timer = TimeElapsedBool(60)
    sleeper = SmartSleeper(1 / 30)

    while True:
        frame[:, :, :] = 0
        sphere.periodic_rotate()
        sphere.resize(.5)
        sphere.write(frame)
        cv2.imshow('', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        sleeper(1/30)

    cv2.destroyAllWindows()
