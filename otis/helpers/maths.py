from queue import Queue

import numpy as np

from otis.helpers.coordtools import abs_point


def line_from_point_angle_length(point, angle, length, ref=None, dim=None):
    """
    get ends point from point angle length
    :param point:
    :param angle:
    :param length:
    :param ref:
    :return:
    """
    a_point = abs_point(point, ref, dim)
    point_1 =[0,0]
    point_1[0] = int(a_point[0] + np.cos(angle*2*np.pi/360) * length)
    point_1[1] = int(a_point[0] - np.sin(angle*2*np.pi/360) * length)
    return a_point, point_1


def line_from_center_angle_length(center, angle, length, ref=None, dim=None):
    a_center = abs_point(center, ref, dim)
    add_x = np.cos(angle*2*np.pi/360) * length/2
    sub_y = -np.sin(angle*2*np.pi/360) * length/2
    point_0 = int(a_center[0] + add_x), int(a_center[1] + sub_y)
    point_1 = int(a_center[0] - add_x), int(a_center[1] - sub_y)
    return point_0, point_1


class MovingAverage:

    def __init__(self, n):
        self.n = n
        self.data = Queue()
        for _ in range(self.n):
            self.data.put(0)
        self.ma = 0

    def __call__(self, x=None):
        return self.ma

    def update(self, x):

        _x = x / self.n
        self.ma = self.ma + _x - self.data.get()
        self.data.put(_x)
        return self.ma


def linear_distance(p0, p1):
    return np.sqrt((p0[0]-p1[0])**2+(p0[1]-p1[1])**2)
