import time
import abc


class Timer(abc.ABC):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def __call__(self):
        return True


class SmartSleep(Timer):

    def __init__(self, wait=1/30):

        self.wait = wait
        self.tick = None

    def __call__(self, wait=None):
        wait = wait if wait is not None else self.wait
        if self.tick is None:
            self.tick = time.time()
        else:
            if time.time() - self.tick < wait:
                time.sleep(wait - time.time() + self.tick)
            self.tick = time.time()


class LastCallTimer(Timer):

    def __init__(self):
        """
        returns the since the last time it was called
        """
        self._tick = time.time()

    def __call__(self):

        tock = time.time()
        out = tock - self._tick
        self._tick = tock
        return out


class BoolTimer(Timer):

    def __init__(self, wait=1/3):
        """

        :param wait: float in seconds
        """
        self.wait = wait
        self._tick = 0

    def __call__(self):

        if time.time() - self._tick >= self.wait:
            self._tick = time.time()
            return True
        else:
            return False


class Blinker(Timer):

    def __init__(self, cycle=.5):
        """
        :type cycle: list [time_on, time_off]
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
            self._cycle = [new_cycle]*2
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
