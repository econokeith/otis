"""
screens events like flashes or countdowns or pulses
"""
import abc
import bisect
import queue

import time
from typing import Tuple, Union

from otis.helpers import dstructures as utils, colortools
import numpy as np
import cv2

from otis.helpers import colortools as ctools, timers as timers
from otis.overlay import textwriters as writers, shapes


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

    def __init__(self, dim, start=10, name='tracker', fps=30):
        self.countdown_writer = writers.TextWriter(coords=(0, -200), color='b', scale=20, ltype=-1, thickness=30,
                                                   ref='c', jtype='c')

        self.countdown_timer = timers.CallFrequencyLimiter(1)
        self.start = start
        self.color_counter = ctools.UpDownCounterT(start=255, maxi=255,
                                                   dir=-1, mini=0,
                                                   cycle_t=1, repeat=True)

        self.frame =  np.zeros((*dim[::-1], 3), dtype='uint8')
        self.no_camera_sleeper = timers.SmartSleeper(1/fps)
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
                 direction = 1,
                 cycle_t = 1,
                 max_ups = 60,
                 repeat = False,
                 updown = False,
                 end_value = None
                 ):
        """
        currently just GBR column fix
        """
        
        self.pixel = pixel
        self.show = show
        self.counter = timers.TimedCycle(
                                        min_i=mini,
                                        max_i=maxi,
                                        begin_at=start,
                                        direction= direction,
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
        # i comes after complete check so that we get to the last value
        i = self.counter()

        F = frame[:, :, self.pixel]
        frame[:, :, self.pixel] = np.where(F.astype('uint16')+ i  >= 255, 255, F+i )

    def reset(self):
        self.counter.reset()






if __name__=='__main__':
    pass


class ScreenGrid:

    def __init__(self,
                 dim: Tuple[int, int]= (1920, 1080),
                 columns: int = 8,
                 rows: int = 8,
                 color: Union[str, Union[Tuple[int, int, int]]] = 'grey',
                 thickness: int = 1,
                 x_bounds: Union[None, Tuple[int, int]]=None,
                 y_bounds: Union[None,  Tuple[int, int]] = None,
                 ):
        """

        Args:
            dim:
            columns:
            rows:
            color:
            thickness:
            x_bounds:
            y_bounds:
        """

        self.dim = dim
        self.columns = columns
        self.rows = rows
        self.color = colortools.color_function(color)
        self.thickness = thickness
        self.x_start = 0 if x_bounds is None else x_bounds[0]
        self.x_stop = self.dim[0] if x_bounds is None else x_bounds[1]
        self.y_start = 0 if y_bounds is None else y_bounds[0]
        self.y_stop = self.dim[1] if y_bounds is None else y_bounds[1]

        self.x_grid = np.linspace(self.x_start, self.x_stop,  self.columns, dtype=int)
        self.y_grid = np.linspace(self.y_start, self.y_stop, self.rows, dtype=int)

        self.grid_line = shapes.Line(color=self.color, thickness=self.thickness)

    def write(self, frame):
        for x in self.x_grid[1:-1]:
            coords = (x, self.y_grid[0], x, self.y_grid[-1])
            self.grid_line.write(frame, coords=coords)

        for y in self.y_grid[1:-1]:
            coords = (self.x_grid[0], y, self.x_grid[-1], y)
            self.grid_line.write(frame, coords=coords)

    def find_sector(self, point: Tuple[int, int], colorize: Union[None, Tuple[np.ndarray, int, int]] =None):
        x_idx = bisect.bisect_left(self.x_grid, point[0])
        y_idx = bisect.bisect_left(self.y_grid, point[1])

        if colorize is not None:
            frame, pixel_idx, value = colorize
            x0, x1 = self.x_grid[x_idx-1], self.x_grid[x_idx]
            y0, y1 = self.y_grid[y_idx-1], self.y_grid[y_idx]
            colortools.colorize_frame(frame[y0:y1+1, x0:x1+1], pixel_idx, value)

        return x_idx, x_idx + 1, y_idx, y_idx + 1
