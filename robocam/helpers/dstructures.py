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


