"""
screens events like flashes or countdowns or pulses
"""
import abc
import queue

import numpy as np
import cv2

from robocam.helpers import colortools as ctools, timers as timers
from robocam.overlay import textwriters as writers

class ScreenEvent(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass
    
    @abc.abstractmethod
    def loop(self, *args,**kwargs):
        pass
    
    @abc.abstractmethod
    def reset(self):
        pass


class CountDown(ScreenEvent):

    def __init__(self, dim, start=10, name='tracker'):
        self.countdown_writer = writers.TextWriter(ref='c', 
                                                   scale=20, 
                                                   ltype=-1,
                                                   thickness=30, 
                                                   color='b',
                                                   position=(0, -200), 
                                                   jtype='c'
                                                   )

        self.countdown_timer = timers.CallHzLimiter(1)
        self.start = start
        self.color_counter = ctools.UpDownCounterT(start=255, maxi=255,
                                                   dir=-1, mini=0,
                                                   cycle_t=1, repeat=True)

        self.frame =  np.zeros((*dim[::-1], 3), dtype='uint8')
        self.no_camera_sleeper = timers.SmartSleeper(1/30)
        self.name = name
        self.i = self.start
        self.finished = False

    def loop(self, reset=False, show=True):
        if reset is not False and self.i == 0:
            self.reset(reset)

        frame = self.frame
        
        if self.i >= 1:
            frame[:, :, :] = self.color_counter()
            self.countdown_writer.write(frame, text=str(self.i))

            if self.countdown_timer() is True:
                self.i -= 1

        else:
            frame[:, :, :] = 0

        self.no_camera_sleeper()

        if show is True:
            cv2.imshow(self.name, frame)

        if self.i == 0:
            self.finished = True

    def reset(self, start=None):
        if start is not None:
            self.start = start
        self.i = self.start


class ColorFlash(ScreenEvent):

    def __init__(self,
                 pixel=2,
                 show=True,
                 mini=0,
                 maxi=255,
                 start=0,
                 dir = 1,
                 cycle_t = 1,
                 max_ups = 60,
                 repeat = True,
                 updown = False, 
                 end_value = None
                 ):
        """
        currently just GBR column fix
        """
        
        self.pixel = pixel
        self.show = show
        self.counter = timers.TimedCycle(
                                        mini=mini,
                                        maxi=maxi,
                                        start=start,
                                        dir = dir,
                                        cycle_t = cycle_t,
                                        max_ups = max_ups,
                                        repeat = repeat,
                                        updown = updown , 
                                        end_value = end_value
                                        )


    @property
    def complete(self):
        return self.counter.complete

    def loop(self, frame):

        if self.complete is True:
            return

        i = self.counter()
        F = frame[:, :, self.pixel]
        frame[:, :, self.pixel] = np.where(F.astype('uint16')+ i  >= 255, 255, F+ i )

    def reset(self):
        self.counter.reset()


def main():
    from robocam import camera
    import time
    from robocam.helpers import utilities as utils

    capture = camera.CameraPlayer(dim=(1920, 1080))
    time.sleep(2)
    # time.sleep(3)
    event_queue = queue.Queue()
    color_flash = ColorFlash()
    event_queue.put(color_flash)
    # new_flash_timer = timers.CallHzLimiter(5)
    while True:
        capture.read()
        # if new_flash_timer is True:
        #     color_flash = ColorFlash(3)
        color_flash.loop(capture.frame)
        capture.show()

        if utils.cv2waitkey(1) is True:
            break

    capture.stop()


if __name__=='__main__':
    main()


