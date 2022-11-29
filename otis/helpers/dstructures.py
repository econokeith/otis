class BoundIterator:
    """
    iter type object with
    """
    def __init__(self, iterable=None):
        if iterable is not None:
            self.n = len(iterable)
            self.iterator = iter(iterable)
        else:
            self.n = 0
            self.iterator = None

    @property
    def is_empty(self):
        if self.n <= 0:
            return True
        else:
            return False

    def __call__(self):
        self.n -= 1
        try:
            return next(self.iterator)
        except:
            return None

def iter_none(iterable):
    """
    turns an iterable data structure into an iter where the last .next()
    returns None
    """
    yield from iterable
    yield None


class CounterDict(dict):
    """
    unnecesarily complicated means of making a list of unique observed_names with indexes
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = 0

    def __getitem__(self, key):
        if key not in self.keys():
            super().__setitem__(key, self.counter)
            self.counter += 1

        return super().__getitem__(key)


