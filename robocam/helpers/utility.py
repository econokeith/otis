def iter_none(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None


def abs_point(reference, relative_point):
    """
    returns the absolute pixel location when given a cartesian relative point to the
    reference that is considered the origin
    :param reference:origin
    :param relative_point: relative location
    :return: tuple
    """
    return int(relative_point[0]+reference[0]), int(reference[1]-relative_point[1])

