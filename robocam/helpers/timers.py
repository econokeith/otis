from typing import Any

import abc

class FreqEnforce:

    def __init__(self, wait=1/30):

        self.wait = wait
        self.tick = None

    def wait(self, wait=None):
        wait = wait if wait is not None else self.wait
        if self.tick is None:
            self.tick = time.time()
        else:
            tock = time.time()
            if tock - self.tick < self.wait:
                time.sleep(self._wait_in_seconds - tock + tick)
            self.tick = tock

class CallTimer:

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



class BoolTimer(abc.ABC):

    @abc.abstractmethod
    def __init__(self):
        pass

    @abc.abstractmethod
    def __call__(self) -> bool: 
        return True

class RepeaterBool(BoolTimer):

    def __init__(self, wait=1/3):
        """

        :param wait: float in seconds
        """
        self.wait = wait
        self._tick = None

    def __call__(self):

        if self._tick is None:
            self._tick = time.time()
            return True

        elif time.time() - self._tick >= self.wait:
            self._tick = time.time()
            return True

        else:
            return False

class Blinker(BoolTimer):

    def __init__(self, timer = [.5, .5]):
        """

        :type timer: list [time_on, time_off]
        """
        self.timer = timer
        self.on = False
        self._tick = 0

    def __call__(self):

        if self.on is True:
            if time.time() - self._tick > self.timer[0]:
                self._tick = time.time()
                self.on = False

            return True

        else:
            if time.time() - self._tick > self.timer[1]:
                self._tick = time.time()
                self.on = True
            return False