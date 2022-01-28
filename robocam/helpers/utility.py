import numpy as np

def iter_none(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None

FRAME_HASH = {}
FRAME_HASH['c'] = lambda s: (int(s[1] / 2), int(s[0] / 2))
FRAME_HASH['tl'] = lambda s: (0, 0)
FRAME_HASH['bl'] = lambda s: (0, s[0])
FRAME_HASH['l'] = lambda s: (0, int(s[0] / 2))
FRAME_HASH['r'] = lambda s: (s[1], int(s[0] / 2))
FRAME_HASH['t'] = lambda s: (int(s[1]/2), 0)
FRAME_HASH['b'] = lambda s: (int(s[1]/2), s[0])

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
    elif dim is not None and reference in FRAME_HASH.keys():
        _ref = FRAME_HASH[reference](dim)
        return int(relative_point[0] + _ref[0]), int(_ref[1] - relative_point[1])

    else:
        return int(relative_point[0] + reference[0]), int(reference[1] - relative_point[1])



    # def line_from_end_points(self, point_0, point_1, ref=None):
    #     a_point_0 = self._to_absolute_point(point_0, ref=ref)
    #     a_point_1 = self._to_absolute_point(point_1, ref=ref)
    #     return a_point_0, a_point_1

def line_from_point_angle_length(point, angle, length, ref=None):
    """
    get ends point from point angle length
    :param point:
    :param angle:
    :param length:
    :param ref:
    :return:
    """
    a_point = abs_point(point, ref)
    point_1 =[0,0]
    point_1[0] = int(a_point[0] + np.cos(angle*2*np.pi/360) * length)
    point_1[1] = int(a_point[0] - np.sin(angle*2*np.pi/360) * length)
    return a_point, point_1

def line_from_center_angle_length(center, angle, length, ref=None):
    a_center = abs_point(center, ref)
    add_x = np.cos(angle*2*np.pi/360) * length/2
    sub_y = -np.sin(angle*2*np.pi/360) * length/2
    point_0 = int(a_center[0] + add_x), int(a_center[1] + sub_y)
    point_1 = int(a_center[0] - add_x), int(a_center[1] - sub_y)
    return point_0, point_1

def linear_distance(p0, p1):
    return np.sqrt((p0[0]-p1[0])**2+(p0[1]-p1[1])**2)