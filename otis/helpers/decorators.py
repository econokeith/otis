"""
A collection of decorators that  are mainly useful when testing functionality in
Jupyter notebooks
"""
import time
import otis.helpers.timers as timers

def min_wait_between_calls(min_wait=1 / 30):
    """
    max_frequency(hz):
    sets a maximum frequency (hz) a function can be run
    """
    def decorate(func):

        def wait_function(*args, **kwargs):

            tock = time.time()
            if tock - wait_function.tick >= wait_function.min_wait:
                wait_function.tick = tock
                return func(*args, **kwargs)

            else:
                return None

        wait_function.min_wait = min_wait
        wait_function.tick = 0

        return wait_function

    return decorate


def make_me_blink(on_time=.5, off_time=.5):
    """
    blinker(period, duty_cycle)
    sets when a function when and won't respond to a call
    """
    def decorate(func):

        def blink_fun(*args, **kwargs):
            tock = time.time()
            if blink_fun.on is True:
                if tock - blink_fun.tick > blink_fun.on_time:
                    blink_fun.on = False
                    blink_fun.tick = time.time()

                return func(*args, *kwargs)

            else:

                if tock - blink_fun.tick > blink_fun.off_time:
                    blink_fun.on = True
                    blink_fun.tick = time.time()

                return None

        blink_fun.on_time = on_time
        blink_fun.off_time = off_time
        blink_fun.tick = time.time()
        blink_fun.on = True
        return blink_fun

    return decorate

def smart_sleeper_method(fps=30):
    sleeper = timers.SmartSleeper()
    def decorate(func):
        def sleeper_fun(*args, **kwargs):
            sleeper(1/decorate.fps)
            return func(*args, **kwargs)

        return sleeper_fun

    decorate.fps = fps
    return decorate

def frequency_tracker():
    """
    count the frequency of executions per second
    """
    pass


