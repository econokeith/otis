import time
from queue import Queue

import cv2
import numpy as np

import robocam.helpers.utilities as utils
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.writer_base as base
import robocam.overlay.cv2shapes as shapes

class TextWriter(base.Writer):

    def __init__(self,
                 position = (0,0),  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 ref=None,
                 text = None
                 ):

        self.font = font
        self.color = ctools.color_function(color)

        self.ref = ref
        self.position = position
        self.scale = scale
        self.ltype = ltype
        self.line = text
        self.text_fun = None

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        self._line = new_text

    # @property
    # def position(self):
    #     return self._position
    #
    # @position.setter
    # def position(self, new_position):
    #     self._position = uti.abs_point(new_position, self.ref, self.dim)

    def add_fun(self, fun):
        self.text_fun = fun
        return self

    def write(self, frame, text=None, color=None, position=None, ref=None):
        """
        :type frame: np.array
        """
        _color = color if color is not None else self.color
        _text = text if text is not None else self.line
        _position = position if position is not None else self.position
        _ref = ref if ref is not None else self.ref

        shapes.write_text(frame, _text, _position, self.font, _color,
                          self.scale, self.ltype, _ref)

    def write_fun(self, frame, *args, **kwargs):
        self.line = self.text_fun(*args, **kwargs)
        self.write(frame)

        
class TypeWriter(TextWriter):

    def __init__(self,
                 position=(),  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt=None,
                 key_wait = [.1, .3],
                 end_pause=1,
                 loop=False,
                 ref = None,
                 text = None,
                 ):
        
        super().__init__(position=position, text=None, font=font, color=color, scale=scale, ltype=ltype, ref=ref)
        
        self.dt = dt
        self._key_wait = key_wait
        self.end_timer = timers.BoolTimer(end_pause)
        self.loop = loop
        self.line_iter = utils.BoundIterator([0])
        self.line_complete = True
        self.line = text
        self.output = ""
        self.cursor = Cursor()
        self.script = Queue()
        self.ktimer = timers.CallHzLimiter(self.key_wait)

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        # updates text_generator when text is updated
        self._line = new_text
        self.tick = time.time()
        
        if new_text is None:
            self.line_iter = None
            self.line_complete = True
            self.output = ""
            
        else:
            self.line_iter = utils.BoundIterator(new_text)
            self.line_complete = False
            self.output = ""

    @property
    def key_wait(self):
        if isinstance(self._key_wait, (float, int)):
            return self._key_wait
        else:
            return np.random.rand() * (self._key_wait[1] - self._key_wait[0]) + self._key_wait[0]

    @key_wait.setter
    def key_wait(self, new_wait):
        self._key_wait = new_wait

    @property
    def is_done(self):
        return self.line_complete and self.script.empty()

    def add_lines(self, new_lines):
        """
        adds lines to the queue if lines is either a string or
        an iterable object full of strings
        :param new_lines:
        :return:
        """
        if not isinstance(new_lines, str):
            for new_line in new_lines:
                self.add_lines(new_line)

        else:
            self.line = self.script.put(new_lines)

        return self

    def type_line(self, frame):

        # if there's more in the text generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.line_complete is True and self.script.empty() is True:
            return

        elif self.line_complete is True and self.script.empty() is False:
            self.line = self.script.get()
        # update if there is more to teh line and t > wait
        elif self.line_iter.is_empty is False:

            if self.ktimer(self.key_wait):
                self.output += self.line_iter()

            self.write(frame, self.output)

        #if the line is done, but the end pause is still going. write whole line with cursor
        elif self.line_iter.is_empty and self.end_timer() is False:
            self.write(frame, self.output+self.cursor())

        #empty line generator and t > pause sets the line to done
        else:
            self.line_complete = True
            self.end_timer.reset()

class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = timers.TimeSinceLast()
        self.text_function =  lambda fps : f'FPS = {int(1/fps)}'

    def write(self, frame: np.array, text=None, color=None):
        fps = self.text_function(self.clock())
        super().write(frame, fps)


class Cursor(timers.Blinker):

    def __init__(self, cycle=.53, char_1='_', char_0=' '):
        """
        returns char_1 if on and char_0 if off
        :param cycle: if float, [on_time, off_time] = [cycle, cycle], else on_time, off_time = cycle
        :param char_1:
        :param char_0:
        """
        super().__init__(cycle=cycle)
        self.char_0 = char_0
        self.char_1 = char_1

    def __call__(self):
        if super().__call__():
            return self.char_1
        else:
            return self.char_0

if __name__ == '__main__':
    pass