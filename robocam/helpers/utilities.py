from queue import Queue

import numpy as np
import cv2

class BoundIterator:
    """
    iter type object with
    """
    def __init__(self, iterable):
        self.n = len(iterable)
        self.iterator = iter(iterable)

    @property
    def is_empty(self):
        if self.n == 0:
            return True
        else:
            return False

    def __call__(self):
        self.n -= 1
        return next(self.iterator)

def iter_none(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None

_FRAME_HASH = {}
_FRAME_HASH['c'] = lambda s: (int(s[1] / 2), int(s[0] / 2))
_FRAME_HASH['tl'] = lambda s: (0, 0)
_FRAME_HASH['bl'] = lambda s: (0, s[0])
_FRAME_HASH['br'] = lambda s: (s[1], s[0])
_FRAME_HASH['tr'] = lambda s: (s[1], 0)
_FRAME_HASH['l'] = lambda s: (0, int(s[0] / 2))
_FRAME_HASH['r'] = lambda s: (s[1], int(s[0] / 2))
_FRAME_HASH['t'] = lambda s: (int(s[1] / 2), 0)
_FRAME_HASH['b'] = lambda s: (int(s[1] / 2), s[0])

#todo: clean up the dim variable to make it consistent between np.shape and regular dims
def abs_point(relative_point, reference=None, dim=None):

    """
    returns the absolute pixel location when given a cartesian relative point to the
    reference that is considered the origin
    :param reference:origin
    :param relative_point: relative location
    :return: tuple
    """
    if reference is None:
        return int(relative_point[0]), int(relative_point[1])

    if isinstance(reference, str):
        ref = _FRAME_HASH[reference](dim)

    else:
        ref = reference

    return int(relative_point[0] + ref[0]), int(ref[1] - relative_point[1])

def find_justified_start(text, pos, font, scale, ltype, jtype='l'):
    assert jtype in ['l', 'c', 'r']

    if jtype == 'l':
        return pos

    w, h = cv2.getTextSize(text, font, scale, ltype)[0]
    if jtype == 'c':
        return (int(pos[0]-w/2), pos[1])
    else:
        return (int(pos[0]-w), pos[1])



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


def cv2waitkey(n=1):
    """
    will return True on keyboard mash of q, Q or esc
    else return False
    :param n: millisecond wait.
    :return: Bool
    """
    if cv2.waitKey(n) & 0xFF in [ord('q'), ord('Q'), 27]:
        return True
    else:
        return False


def resize(frame, scale=.5):
    return cv2.resize(frame, (0, 0), fx=scale, fy=scale)


class CounterDict(dict):
    """
    unnecesarily complicated means of making a list of unique names with indexes
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    def __getitem__(self, key):
        if key not in self.keys():
            super().__setitem__(key, self.counter)
            self.counter += 1

        return super().__getitem__(key)


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