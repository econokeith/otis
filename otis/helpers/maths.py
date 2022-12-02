from queue import Queue

import numpy as np

from otis.helpers.coordtools import absolute_point


def line_from_point_angle_length(point, angle, length, ref=None, dim=None):
    """
    get ends point from point angle length
    :param point:
    :param angle:
    :param length:
    :param ref:
    :return:
    """
    a_point = absolute_point(point, ref, dim)
    point_1 =[0,0]
    point_1[0] = int(a_point[0] + np.cos(angle*2*np.pi/360) * length)
    point_1[1] = int(a_point[0] - np.sin(angle*2*np.pi/360) * length)
    return a_point, point_1


def line_from_center_angle_length(center, angle, length, ref=None, dim=None):
    a_center = absolute_point(center, ref, dim)
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
        if x is not None:
            self.update(x)
        return self.ma

    def update(self, x):

        _x = x / self.n
        self.ma = self.ma + _x - self.data.get()
        self.data.put(_x)
        return self.ma


def linear_distance(p0, p1):
    return np.sqrt((p0[0]-p1[0])**2+(p0[1]-p1[1])**2)

def collision_two_moving_circles(circle0, circle1):
    pass


def remove_overlap(ball1, ball2):
    x1 = ball1.center
    x2 = ball2.center
    r1 = ball1.radius
    r2 = ball2.radius
    m1 = ball1.mass
    m2 = ball2.mass
    # find sides
    a, b = dx = x2 - x1
    # check distance
    r_sum = r1 + r2
    c = np.hypot(*dx)

    if c < r_sum:
        # separate along text connecting centers
        dc = r_sum - c + 1
        da = a * (c + dc) / c - a
        db = b * (c + dc) / c - b
        x1[0] -= da * m2 / (m1 + m2)
        x2[0] += db * m1 / (m1 + m2)
        x1[1] -= db * m2 / (m1 + m2)
        x2[1] += da * m1 / (m1 + m2)


def remove_overlap_w_no_mass(no_mass, has_mass, buffer=0):
    x1 = no_mass.center
    x2 = has_mass.center
    r1 = no_mass.radius
    r2 = has_mass.radius

    # find sides
    a, b = dx = x2 - x1
    # check distance
    r_sum = r1 + r2 + buffer
    centers_distance = np.hypot(*dx)

    if centers_distance < r1:
        has_mass.is_finished = True

    elif centers_distance < r_sum:
        # separate along text connecting centers
        dc = r_sum - centers_distance + 1
        da = a * (centers_distance + dc) / centers_distance - a
        db = b * (centers_distance + dc) / centers_distance - b

        x2[0] += db
        x2[1] += da
