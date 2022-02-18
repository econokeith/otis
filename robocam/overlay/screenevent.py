"""
screens events like flashes or countdowns or pulses
"""
import abc

import numpy as np
import cv2
from sympy import cycle_length

from robocam.helpers import colortools as ctools, timers as timers
from robocam.overlay import textwriters as writers

class ScreenInterrupt(abc.ABC):

    @abc.abstractmethod
    def __init__(self, *args, **kwargs):
        pass
    
    @abc.abstractmethod
    def loop(self, *args,**kwargs):
        pass
    
    @abc.abstractmethod
    def reset(self):
        pass


class CountDown(ScreenInterrupt):

    def __init__(self, dim, start=10, name='tracker'):
        self.countdown_writer = writers.TextWriter(ref='c', scale=20, ltype=-1,
                                              thickness=30, color='b',
                                              position=(0, -200), jtype='c')

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


class ColorFlash(ScreenInterrupt):

    def __init__(self,
                 pixel=2, 
                 mini=0,
                 maxi=255,
                 start=0,
                 dir=1,
                 cycle_t=1,
                 max_ups=30,
                 repeat=False
                 ):
        """
        currently just GBR column fix
        """
        
        self.pixel = pixel
        self.counter = ctools.UpDownCounterT(mini=mini,
                                             maxi=maxi,
                                             start=start,
                                             dir=dir,
                                             cycle_t=cycle_t,
                                             max_ups=max_ups,
                                             repeat = repeat
                                             )
        self.complete = False

    def loop(self, frame):

        dt = self.counter()
        if dt > 255 - int(self.counter.speed) + 1:
            self.complete = True

        _frame = frame[:,:,self.pixel]
        
        _frame = np.where(_frame <= 255-dt, _frame + dt, 255)





