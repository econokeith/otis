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

# todo: clean up the dim variable to make it consistent between np.shape and regular dims
def abs_point(relative_point, reference=None, dim=None):

    """
    returns the absolute pixel location when given a cartesian relative point to there
    reference that is considered the origin
    :param reference:origin (x, y)
    :param relative_point: relative location actual location
    :return:  (x, y)
    """
    if reference is None:
        return int(relative_point[0]), int(relative_point[1])

    if isinstance(reference, str) and dim is not None:
        ref = _FRAME_HASH[reference](dim)
    elif isinstance(reference, str) and dim is None:
        raise ValueError("abs_point will not accept string reference without dimensions of frame")
    else:
        ref = reference

    return int(relative_point[0] + ref[0]), int(ref[1] - relative_point[1])


def bbox_to_center(bbox_coords):
    t, r, b, l = bbox_coords
    return int((r + l) / 2), int((t + b) / 2)
