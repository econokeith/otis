import time
import abc

import numpy as np

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
        mainly used to moderate frame_rate via the camera.show() method

        Args:
            wait: required wait between calls. default = 1/30


        Usage: fps_sleeper = SmartSleeper(wait=1/4)
               while True:
                    ....
                    ....
                    fps_sleeper() <---- ensures all while loops use the same amount of time in this case .25 seconds
                    ....

        """
        self.wait = wait
        self.tick = None
        self.sleep_time = 0.

    def __call__(self, wait=None):
        _wait = wait if wait is not None else self.wait
        if self.tick is None:
            self.tick = time.time()
        else:
            if time.time() - self.tick < _wait: #todo double check the sleep math on SmartSleeper
                self.sleep_time = max(_wait - time.time() + self.tick, 0)
                time.sleep(self.sleep_time)

            self.tick = time.time()


class TimeSinceLast(Timer):

    def __init__(self, freq=False):
        """
        returns the time elapsed since the last time it was called
        Args:
            freq:
        """
        self._tick = time.time()
        self.on = False
        self.finished = False
        self.freq = freq

    def __call__(self):
        if self.on is False:
            self._tick = time.time()
            self.on = True
            return 0

        tock = time.time()
        out: float = tock - self._tick
        self._tick = tock

        if self.freq is False:
            return out
        else:
            try:
                return 1/out
            except:
                return 0


class TimeSinceFirst(Timer):

    def __init__(self, start=False):
        """
        returns the time elapsed since the first call
        """
        if start is False:
            self._tick = None
        else:
            self._tick = time.time()
        self.is_finished = False

    def reset(self, start=False):
        if start is True:
            self._tick = time.time()
        else:
            self._tick = None

    def start(self):
        self()
        return self

    def __call__(self):
        if self._tick is None:
            self._tick = time.time()
            return 0.

        return time.time() - self._tick

class CountDownTimer(TimeSinceFirst):

    def __init__(self, cd_start, start=False):
        """
        counts down to zero then returns zero.
        Args:
            cd_start: length of countdown in seconds
        """
        super().__init__(start=start)
        self.cd_start = cd_start
        self.is_finished = False


    def __call__(self):
        if self.is_finished is True:
            return 0

        t = self.cd_start - super().__call__()

        if t > 0:
            return t

        else:
            self.is_finished = True
            return 0


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


class TimeElapsedBool(TimeSinceFirst):
    """
    return True if time since first call > wait else False
    """
    def __init__(self, wait=1, start=False):
        super().__init__(start=start)
        self.wait = wait

    def __call__(self):
        if super().__call__() > self.wait:
            return True
        else:
            return False


class CallFrequencyLimiter(Timer):

    def __init__(self, wait=1 / 3, freq=False):
        """
        returns true wait is over else returns False
        :param wait: float in seconds
        """
        if freq is False:
            self.wait = wait
        else:
            self.wait = 1/wait
        self._tick = 0
        self.first = True

    def __call__(self, wait=None):

        _wait = self.wait if wait is None else wait
        if time.time() - self._tick >= _wait:
            self._tick = time.time()
            return True
        else:
            return False

class RandomIntervalFrequencyLimiter(CallFrequencyLimiter):

    def __init__(self, wait_range=(0, 1)):

        self.wait_min = wait_range[0]
        self.wait_max = wait_range[1]
        super().__init__(self._next_wait_time(), freq = False)

    def _next_wait_time(self):
        w_min, w_max = self.wait_min, self.wait_max
        return np.random.rand() * (w_max - w_min) + w_min

    def __call__(self, wait=None):
        times_up = super().__call__()
        if times_up is True:
            self.wait = self._next_wait_time()
        return times_up


class Blinker(Timer):

    def __init__(self,
                 cycle_time=.5,
                 duty_cycle=.3,
                 pulse_width=None):
        """
        returns True during on_time and False during off_time
        Args:
            cycle_time: if list/tuple : time_on, time_off = cycle
                        if double : time_on = time_off = cycle
            duty_cycle: percent of time_on for pulse_width. Blinker will only use duty_cycle if pulse_width is not None
                        default = .3
            pulse_width: pulse-width of blink in seconds. if None, Blinker will use cycle time
                         default=None
        """
        """
        
        :type cycle_time: if list/tuple : time_on, time_off = cycle
                          if double : time_on = time_off = cycle
        """

        self.cycle_time = cycle_time
        self.duty_cycle = duty_cycle
        self.pulse_width = pulse_width

        if pulse_width is not None:
            self._cycle = pulse_width*duty_cycle, pulse_width*(1-duty_cycle)

        elif isinstance(cycle_time, (int, float)):

            self._cycle = [cycle_time] * 2

        elif isinstance(cycle_time, (np.ndarray, list, tuple)):

            self._cycle = cycle_time

        else:
            raise ValueError('Blinker unable to find cycle based on inputs given')

        self.on = False
        self._tick = 0

    @property
    def cycle(self):
        return self._cycle

    #todo: update cycle property for timers.Blinker
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

class Cursor(Blinker):

    def __init__(self, cycle_time=.53, char_1='_', char_0=' '):
        """
        returns char_1 if on and char_0 if off
        :param cycle_time: if float, [on_time, off_time] = [cycle, cycle], else on_time, off_time = cycle
        :param char_1:
        :param char_0:
        """
        super().__init__(cycle_time=cycle_time)
        self.char_0 = char_0
        self.char_1 = char_1

    def __call__(self):
        if super().__call__():
            return self.char_1
        else:
            return self.char_0

class TimedCycle(Timer):

    def __init__(self,
                 min_i=0,
                 max_i=255,
                 start=0,  #only matters is repeat is true otherwise defaults to min or max accordingly
                 direction = 1,
                 cycle_t = 1,
                 max_ups = 60,
                 repeat = True,
                 updown = False,
                 end_value = None
                 ):
        """
        Creates a cycle_time of numbers that moves at the same speed regardless of how often it is called. Can either be
        one directional or go up and down.
        Args:
            min_i:
            max_i:
            start:
            direction:
            cycle_t:
            max_ups:
            repeat:
            updown:
            end_value:
        """

        self.min_i = min_i
        self.max_i = max_i
        self._i = start
        self.direction = direction

        if repeat is False and direction == 1:
            self.start = self.min_i
        elif repeat is False and direction == -1:
            self.start = self.max_i
        else:
            self.start = start

        self.max_ups = max_ups
        self.updown = updown
        self.end_value = end_value

        self.length = (max_i - min_i + 1)
        self.cycle_t = cycle_t
        self.speed =  self.length / self.cycle_t
        self.repeat = repeat
        self.complete = False

        self.ups_timer = CallFrequencyLimiter(1 / max_ups)
        self.last_timer = TimeSinceLast()
        self.total_steps_taken = 0
        self.reset() #not sure why but something is causing this

    @property
    def i(self):
        return int(self._i)

    def reset(self):
        self.ups_timer = CallFrequencyLimiter(1 / self.max_ups)
        self.last_timer = TimeSinceLast()
        self.complete = False
        self._i = self.start
        self.total_steps_taken = 0

    def __call__(self):

        if self.ups_timer() is True:

            tp = self.last_timer()
            self._i = self._i + self.speed * tp * self.direction
            self.last_step = self.speed * tp   
            self.total_steps_taken += self.last_step

            if self.updown is False:
                self._one_direction_counter()
            else:
                self._up_down_counter()

        return self.i

    def _one_direction_counter(self):

        if self.repeat is True and self._i >= self.max_i and self.direction == 1:
            self._i = self.min_i

        elif self.repeat is True and self._i <= self.min_i and self.direction == -1:
            self._i = self.max_i

        elif self.repeat is False and self._i >= self.max_i and self.direction == 1:
            self._i = self.max_i
            self.complete = True

        elif self.repeat is False and self._i <= self.min_i and self.direction == -1:
            self._i = self.min_i
            self.complete = True

    #todo: fix updowncounter
    def _up_down_counter(self):

        if self._i > self.max_i:# and self.repeat is False:
            self._i = self.max_i
            self.direction *=-1

        elif self._i < self.min_i:# and self.repeat is False:
            self._i = self.min_i
            self.direction *= -1


class TimedRectangleCycle(Timer):

    def __init__(self,  x_range, y_range, cycle_t, repeat=True):
        """

        Args:
            x_range:
            y_range:
            cycle_t:
            repeat:
        """
        self.x_min, self.x_max = x_range
        self.y_min, self.y_max = y_range

        self.x_dist =  x_dist = (x_range[1]-x_range[0] + 1 )
        self.y_dist =  y_dist =  (y_range[1]-y_range[0]+1)
        self.total_distance = 2*(self.x_dist + self.y_dist)
        self.speed = self.total_distance / cycle_t
        self.counter = TimedCycle(min_i=0, max_i = self.total_distance - 1, cycle_t=cycle_t, repeat=repeat)

        self.c0 = x_dist
        self.c1 = x_dist + y_dist
        self.c2 = 2*x_dist + y_dist

    def __call__(self):

        i = self.counter()
        if i < self.c0:
            self.side = 0
            return (self.x_min + i, self.y_min)
        elif i < self.c1:
            self.side = 1
            return (self.x_max, self.y_min + (i-self.c0))
        elif i < self.c2:
            self.side = 2
            return (self.x_max - (i-self.c1), self.y_max)
        else:
            self.side = 3
            return (self.x_min, self.y_max - (i-self.c2))

if __name__=="__main__":
    updown = TimedCycle(min_i=50,
                        max_i=1170,
                        updown=True,
                        cycle_t=5
                        )
    tick = time.time()
    for i in range(400):
        time.sleep(.1)
        print(updown())

