import time
import abc


class Timer(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        """
        abstract base class for all Timers. 
        All are called via the __call__ method
        """
        pass

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        """
        all call methods should allow for overriding args in

        """
        return True


class SmartSleeper(Timer):

    def __init__(self, wait=1 / 30):
        """
        if time since last call is less than wait, sleeps for the difference. 
        """
        self.wait = wait
        self.tick = None

    def __call__(self, wait=None):
        _wait = wait if wait is not None else self.wait
        if self.tick is None:
            self.tick = time.time()
        else:
            if time.time() - self.tick < _wait:
                time.sleep(_wait - time.time() + self.tick)
            self.tick = time.time()


class TimeSinceLast(Timer):

    def __init__(self):
        """
        returns the time elapsed since the last time it was called
        """
        self._tick = time.time()

    def __call__(self):
        tock = time.time()
        out: float = tock - self._tick
        self._tick = tock
        return out


class TimeSinceFirst(Timer):

    def __init__(self, chop=False, round=False):
        """
        returns the time elapsed since the first call
        """
        self._tick = None
        self.chop = chop
        self.round = round


    def __call__(self):
        if self._tick is None:
            self._tick = time.time()
            return 0
        elif isinstance(self.round, int):
            return round(time.time() - self._tick, self.round)
        elif self.chop is True:
            return int(time.time() - self._tick)
        else:
            return time.time() - self._tick


class FunctionTimer(Timer):

    def __init__(self, function):
        """

        :param function: uncalled function
        """
        self.function = function
        self._time = 0

    @property
    def time(self):
        return self._time

    def __call__(self, *args, **kwargs):
        tick = time.time()
        out = self.function(*args, **kwargs)
        self._time = time.time() - tick
        return out


class BoolTimer(Timer):
    """
    return True if time since first call > wait else False
    """
    def __init__(self, wait=1):
        self.wait = wait
        self._tick = 0

    def __call__(self):
        if self._tick == 0:
            self._tick = time.time()
            return False
        elif time.time() - self._tick < self.wait:
            return False
        else:
            return True

    def reset(self):
        self._tick = 0


class CallHzLimiter(Timer):

    def __init__(self, wait=1 / 3):
        """
        returns true wait is over else returns False
        :param wait: float in seconds
        """
        self.wait = wait
        self._tick = 0

    def __call__(self, wait=None):
        wait = self.wait if wait is None else wait

        if time.time() - self._tick >= wait:
            self._tick = time.time()
            return True
        else:
            return False


class Blinker(Timer):

    def __init__(self, cycle=.5):
        """
        returns True during on_time and False during off_time
        :type cycle: if list : time_on, time_off = cycle
                     if double : time_on = time_off = cycle
        """
        self.cycle = cycle
        self.on = False
        self._tick = 0

    @property
    def cycle(self):
        return self._cycle

    @cycle.setter
    def cycle(self, new_cycle):
        if isinstance(new_cycle, (int, float)):
            self._cycle = [new_cycle] * 2
        else:
            self._cycle = new_cycle

    def __call__(self):

        if self.on is True:
            if time.time() - self._tick > self._cycle[0]:
                self._tick = time.time()
                self.on = False

            return True
        else:
            if time.time() - self._tick > self._cycle[1]:
                self._tick = time.time()
                self.on = True

            return False
