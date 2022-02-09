"""
screens events like flashes or countdowns or pulses
"""
import numpy as np
import cv2

from robocam.helpers import colortools as ctools, timers as timers
from robocam.overlay import textwriters as writers

class CountDown:

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
        self.no_camera_sleeper = timers.SmartSleeper(1/60)
        self.name = name
        self.n = self.start
        self.finished = False

    def loop(self, reset=False, show=True):
        if reset is not False and self.n == 0:
            self.reset(reset)

        frame = self.frame
        if self.n >= 1:
            frame[:, :, :] = self.color_counter()

            self.countdown_writer.write(frame, text=str(self.n))
            if self.countdown_timer() is True:
                self.n -= 1

        else:
            frame[:, :, :] = 0

        self.no_camera_sleeper()

        if show is True:
            cv2.imshow(self.name, frame)

        if self.n == 0:
            self.finished = True

    def reset(self, start=None):
        if start is not None:
            self.start = start
        self.n = self.start

