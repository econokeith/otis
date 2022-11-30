import time
from queue import Queue
import copy
import types

import cv2
import numpy as np

import otis.helpers.coordtools
import otis.helpers.maths
from otis.helpers import timers, colortools, shapefunctions, texttools, \
    otistools, cvtools, dstructures, coordtools, misc
from otis.overlay import bases, shapes
from otis.overlay.textwriters import TextWriter

class SingleLineTypeWriter(TextWriter):

    def __init__(self,
                 coords=(0, 0),  # coords
                 font='duplex',
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt=None,
                 key_wait_range=(.5, .75),
                 end_pause=1,
                 loop=False,
                 ref=None,
                 text=None,
                 **kwargs
                 ):

        super().__init__(coords=coords,
                         font=font,
                         color=color,
                         scale=scale,
                         ltype=ltype,
                         ref=ref,
                         text=text,
                         **kwargs
                         )

        self.is_waiting = True
        self.dt = dt
        self.key_wait_range = key_wait_range
        self.end_pause = end_pause
        self.end_pause_timer = timers.TimeElapsedBool(end_pause, start=False)
        self.loop = loop
        self.line_iterator = dstructures.BoundIterator()
        self._typing_complete = True
        self._text_complete = True
        self.text = text
        self._output = ""
        self.cursor = Cursor()
        self.key_press_timer = timers.RandomIntervalFrequencyLimiter(self.key_wait_range)
        self.total_timer = timers.TimeSinceFirst(start=True)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        # updates text_generator when name is updated
        self._line = new_text
        self.tick = time.time()

        if new_text is None:
            self.line_iterator = dstructures.BoundIterator()
            self._text_complete = True
            self._typing_complete = True
            self._output = ""
            return

        if isinstance(new_text, (tuple, list)):
            new_text, wait = new_text
            self.end_pause = wait

        self.line_iterator = dstructures.BoundIterator(new_text)
        self._text_complete = False
        self._typing_complete = False
        self._output = ""
        self.end_pause_timer.reset(start=False)

    @property
    def text_complete(self):
        return self._text_complete

    @property
    def typing_complete(self):
        return self._typing_complete

    def write(self, frame, text=None, coords=None, color=None, ref=None, **kwargs):

        if self.typing_complete is True and self.end_pause_timer() is True:
            self._text_complete = True
            return

        if text is not None:
            self.coords = coordtools.abs_point(text, ref, frame)
        # if there's more in the name generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.line_iterator.is_empty is False:
            if self.key_press_timer():
                self._output += self.line_iterator()

        # if the text is done, but the end pause is still going. write whole text with cursor
        if self.line_iterator.is_empty is True and self.end_pause_timer() is False:
            self._typing_complete = True

        print(self._output + self.cursor(), round(1000*self.total_timer()))
        super().write(frame, self._output + self.cursor())











class MultiTypeWriter(SingleLineTypeWriter):

    def __init__(self, line_length, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.llength = line_length
        self._used_stubs = []
        self._stub_queue = Queue()
        self._stub = ""
        self._stub_iter = dstructures.BoundIterator(self._stub)
        self._stub_complete = True
        self.comma_pause_factor = 3

    def next_stub(self):
        self._used_stubs.append(self._stub)
        self._stub = self._stub_queue.get()
        self._stub_iter = dstructures.BoundIterator(self._stub)
        self._stub_complete = False
        self._output = ""

    def add_line(self, text, pause=None):
        """
        break up a long text into multiples that fit within self.line_length
        :param text:
        :return:
        """
        # allow input to be a tuple so we can change the pacing of the pauses
        if isinstance(text, (tuple, list)):
            self.add_line(*text)
            return
        # end pause will change for the current text but revert if it isn't updated
        self.end_pause_timer.wait = self.end_pause if pause is None else pause

        ts = self.get_text_size(text)[0]
        stubs = []

        while ts > self.llength:

            split_pos = int(self.llength / ts * len(text))
            split_proposal = text[:split_pos + 1]
            # break at last space in the shortened text
            for i in range(split_pos + 1):
                if split_proposal[-1 - i] == ' ':
                    break

            stubs.append(split_proposal[:split_pos - i])
            text = text[split_pos - i:].strip(' ')
            ts = self.get_text_size(text)[0]

        stubs.append(text)

        # set first stub
        self._stub = stubs[0]
        self._stub_iter = dstructures.BoundIterator(self._stub)

        # set stub que
        for stub in stubs[1:]:
            self._stub_queue.put(stub)

        # do some resets
        self._used_stubs = []
        self.line_complete = False
        self.end_pause_timer.reset()
        self._stub_complete = False
        self._output = ''

    def type_line(self, frame, **kwargs):
        v_move = self.line_spacing
        n_fin = len(self._used_stubs)
        [p0, p1] = self.coords

        # do nothing if the text is complete
        if self.line_complete is True:
            return

        if self._stub_complete is False:
            # print is_finished lines as static
            for i in range(n_fin):
                self.write(frame, self._used_stubs[i])
            # then type out current text
            self._type_stub(frame, coords=(p0, p1 + n_fin * v_move))
            return

        # refill and keep going
        if self._stub_complete is True and self._stub_queue.empty() is False:
            self.next_stub()

        else:  # same as above but the first check of the tiemr will start it.
            if self.end_pause_timer() is False:
                for i in range(n_fin):
                    self.write(frame, self._used_stubs[i])
                self._type_stub(frame, coords=(p0, p1 + (n_fin) * v_move))
            else:
                self.line_complete = True

    def _type_stub(self, frame, coords=None, ref=None):
        """
        single text stochastic typer just to clean things up.
        :param frame:
        :param coords:
        :param ref:
        :return:
        """
        if coords is None:
            _coords = self.coords
        else:
            _coords = coordtools.abs_point(coords, ref, frame.shape)

        if self._stub_iter.is_empty is False:
            # pause for a comma a tad
            if len(self._output) > 0 and self._output[-1] == ',':
                cpf = self.comma_pause_factor
            else:
                cpf = 1

            if self.key_press_timer(cpf * self.key_wait):
                self._output += self._stub_iter()

            self.write(frame, self._output)

        # if the text is done, but the end pause is still going. write whole text with cursor
        else:
            self.write(frame, text=self._output + self.cursor())

            self._stub_complete = True


class Cursor(timers.Blinker):

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



if __name__=='__main__':

    from otis import camera
    capture = camera.ThreadedCameraPlayer(max_fps=30).start()
    writer = SingleLineTypeWriter(coords=(100, 100))
    writer.text = "HELLO MY NAME IS OTIS I WOULD LIKE TO BE YOUR FRIENDS"
    while True:

        capture.read()
        writer.write(capture.frame)
        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break


