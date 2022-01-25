def iter_none(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None