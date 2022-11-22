import numpy as np

__FRAME_HASH = {}
__FRAME_HASH['c'] = lambda s: (int(s[1] / 2), int(s[0] / 2))
__FRAME_HASH['lt'] = lambda s: (0, 0)
__FRAME_HASH['lb'] = lambda s: (0, s[0])
__FRAME_HASH['rb'] = lambda s: (s[1], s[0])
__FRAME_HASH['rt'] = lambda s: (s[1], 0)
__FRAME_HASH['l'] = lambda s: (0, int(s[0] / 2))
__FRAME_HASH['r'] = lambda s: (s[1], int(s[0] / 2))
__FRAME_HASH['t'] = lambda s: (int(s[1] / 2), 0)
__FRAME_HASH['b'] = lambda s: (int(s[1] / 2), s[0])
__FRAME_HASH['cl'] = lambda s: (0, int(s[0] / 2))
__FRAME_HASH['cr'] = lambda s: (s[1], int(s[0] / 2))
__FRAME_HASH['ct'] = lambda s: (int(s[1] / 2), 0)
__FRAME_HASH['cb'] = lambda s: (int(s[1] / 2), s[0])

# todo: clean up the dim variable to make it consistent between np.shape and regular dims. basically need to switch
def abs_point(relative_point,
              reference=None,
              dim=None
              ):

    """
    returns the absolute pixel location when given a cartesian relative point to there
    reference that is considered the origin
    :param reference: origin (x, y)
    :param relative_point: relative location actual location (x, y)
    :param dim: the dimension of the frame. only necessary when using string valued reference
    :return:  (x, y)
    """
    if reference is None:
        return int(relative_point[0]), int(relative_point[1])

    if not isinstance(reference, str):
        ref = reference

    elif isinstance(reference, str) and isinstance(dim, np.ndarray):
        _dim = dim.shape
        ref = __FRAME_HASH[reference](_dim)

    elif isinstance(reference, str) and dim is not None:
        ref = __FRAME_HASH[reference](dim[::-1]) # this is because of how the FRAME HASH FUNCTIONS are set up

    else:
        raise ValueError("abs_point will not accept string reference without dimensions of frame")

    return int(relative_point[0] + ref[0]), int(ref[1] - relative_point[1])

def bbox_to_center(bbox_coords):
    t, r, b, l = bbox_coords
    return int((r + l) / 2), int((t + b) / 2)

def translate_box_coords(coords,
                         in_format ='rtlb',
                         out_format ='rtlb',
                         ref=None,
                         dim=None):
    """

    :param coords:
    :param in_format: 'rtbl', 'ltbr', 'ltwh', 'cwh', 'lbwh', 'tblr'
    :param out_format: 'rtbl', 'ltbr', 'tblr'
    :return:
    """

    abs_point_used = False

    if in_format == out_format and ref is None:
        return coords

    if in_format == 'rtlb':
        r, t, l, b = coords

    elif in_format == 'lbrt':
        l, b, r, t, = coords

    elif in_format == 'ltrb':
        l, t, r, b = coords

    elif in_format == 'tblr':
        t, b, l, r = coords

    elif in_format == 'rblt':
        r, b, l, t = coords

    elif in_format == 'trbl':
        t, r, b, l = coords

    elif in_format == 'cwh':
        cx, cy, w, h = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        t = cy- h//2
        b = cy+ h//2
        l = cx - w//2
        r = cx + w//2

    elif in_format == 'ltwh':
        l, t, w, h = coords
        l, t = abs_point((l,t), ref, dim)
        abs_point_used = True
        b = t+h
        r = l+w

    elif in_format == 'lbwh':
        l, b, w, h = coords
        l, b = abs_point((l,b), ref, dim)
        abs_point_used = True
        t = b - h
        r = l + w

    elif in_format == 'rtwh':
        r, t, w, h = coords
        r, t = abs_point((r,t), ref, dim)
        abs_point_used = True
        l = r-w
        b = t+h

    elif in_format == 'rbwh':
        r, b, w, h = coords
        r, b = abs_point((r,b), ref, dim)
        abs_point_used = True
        l = r-w
        t = b-h

    elif in_format == 'ctwh':
        cx, cy, w, h = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        r = cx - w//2
        l = cx + w//2
        t = cy
        b = cy + h

    elif in_format == 'cbwh':
        cx, cy, w, h = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        r = cx - w//2
        l = cx + w//2
        t = cy - h
        b = cy

    elif in_format == 'crwh':
        cx, cy, w, h = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        r = cx
        l = cx + w
        t = cy - h//2
        b = cy + h//2

    elif in_format == 'clwh':
        cx, cy, w, h = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        r = cx - h
        l = cx
        t = cy - h//2
        b = cy + h//2

    elif in_format == 'cirle':
        cx, cy, r, _ = coords
        cx, cy = abs_point((cx, cy), ref, dim)
        abs_point_used = True
        t = cy- r//2
        b = cy+ r//2
        l = cx - r//2
        r = cx + r//2

    else:
        raise ValueError("invalid coord format")

    if abs_point_used is False:
        r, t = abs_point((r, t), ref, dim)
        l, b = abs_point((l, b), ref, dim)

    if  out_format == 'ltrb':
        return l, t, r, b

    elif out_format == 'tblr':
        return t, b, l, r

    elif out_format == 'lbrt':
        return l, b, r, t

    elif out_format == 'trbl':
        return t, r, b, l

    elif out_format == 'cwh':
        cx = (l+r)//2
        cy = (t+b)//2
        h = (b-t)
        w = (l-r)
        return cx, cy, h, w

    else:
        return r, t, l, b


def find_center_radius_from_box_coords(box_coords,
                                       radius_type='inner', #can be 'inner', 'outer', 'avg', 'diag'
                                       box_format='circle',
                                       ref=None,
                                       dim=None
                                       ):
    """

    Args:
        box_coords:
        radius_type: can be 'inner', 'outer', 'avg', 'diag'
        box_format:
        ref:
        dim:

    Returns:
        (cx, cy, radius, radius)

    """
    if len(box_coords) == 3 or box_format == 'circle':
        return *box_coords, box_coords[2]

    cx, cy, w, h = translate_box_coords(box_coords,
                                        in_format=box_format,
                                        out_format='cwh',
                                        ref=ref,
                                        dim=dim
                                        )

    if radius_type == 'inner':
        radius = min(w, h)//2
    elif radius_type == 'outer':
        radius = max(w, h)//2
    elif radius_type == 'diag':
        radius = np.sqrt(w**2 + h**2)
    else:
        radius = (w+h)//2

    return cx, cy, radius, radius


