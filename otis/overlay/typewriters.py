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


class TypeWriter(TextWriter):

    def __init__(self,
                 coords=(0, 0),
                 font='duplex',
                 color='r',
                 scale=1,
                 ltype=1,
                 thickness=1,
                 ref=None,
                 text=None,
                 line_spacing=.5,
                 max_line_length=None,
                 line_length_format='pixels',
                 n_lines=None,
                 border_spacing=(5, 5),
                 jtype='l',
                 outliner=None,
                 o_ltype=None,
                 o_thickness=1,
                 invert_border=False,
                 one_border=False,
                 # unique to typewriter starts here
                 key_wait_range=(.05, .1),
                 end_pause=1,
                 loop=False,
                 ):

        super().__init__(coords=coords,
                         font=font,
                         color=color,
                         scale=scale,
                         ltype=ltype,
                         thickness=thickness,
                         ref=ref,
                         text=None,
                         line_spacing=line_spacing,
                         max_line_length=max_line_length,
                         line_length_format=line_length_format,
                         n_lines=n_lines,
                         border_spacing=border_spacing,
                         jtype=jtype,
                         outliner=outliner,
                         o_ltype=o_ltype,
                         o_thickness=o_thickness,
                         invert_border=invert_border,
                         one_border=one_border,
                         )

        self.is_waiting = True
        self.key_wait_range = key_wait_range
        self.end_pause = end_pause
        self.end_pause_timer = timers.TimeElapsedBool(end_pause, start=False)
        self.loop = loop
        self.line_iterator = dstructures.BoundIterator()
        self.text_complete = True
        self._current_stub = None
        self._output = ""
        self.cursor = timers.Cursor()
        self.key_press_timer = timers.RandomIntervalFrequencyLimiter(self.key_wait_range)
        self.total_timer = timers.TimeSinceFirst(start=True)
        self.completed_stubs = []

        self.text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        # updates text_generator when name is updated
        if isinstance(new_text, (tuple, list)):
            new_text, end_pause = new_text
            self.end_pause = end_pause
            self.end_pause_timer = timers.TimeElapsedBool(wait=self.end_pause, start=False)

        # this is straight from:
        # https://stackoverflow.com/questions/10810369/python-super-and-setting-parent-class-property
        super(self.__class__, self.__class__).text.fset(self, new_text)

        self.stub_queue = Queue()
        if new_text is not None:
            self.text_complete = False
            for stub in self.text_stubs:
                self.stub_queue.put(stub)

            self.current_stub = self.stub_queue.get()
            self._output = ""
            self.completed_stubs = []

        return

    @property
    def current_stub(self):
        return self._current_stub

    @current_stub.setter
    def current_stub(self, new_stub):
        old_stub = self.current_stub
        self._current_stub = new_stub
        self._output = ""
        self.line_iterator = dstructures.BoundIterator(self.current_stub)
        self.completed_stubs.append(old_stub)

    def write_line_of_text(self, frame, coords=None, show_outline = True, **kwargs):

        # if self.typing_complete is True and (not self.stub_queue.empty() or self.end_pause_timer() is True):
        #     self._stub_complete = True
        #     return

        if self.text_complete is True:
            return

        _coords = self.coords if coords is None else coords
        iter_empty = self.line_iterator.is_empty
        queue_empty = self.stub_queue.empty()

        if iter_empty is False and self.key_press_timer() is True:
            self._output += self.line_iterator()

        elif iter_empty is False and self.key_press_timer() is False:
            pass

        elif iter_empty is True and queue_empty is False:
            self.current_stub = self.stub_queue.get()
            # don't miss a frame if we need to refill
            # self.write_line_of_text(frame)

        elif iter_empty is True and queue_empty is True and self.end_pause_timer() is True:
            self.text_complete = True

        else:
            pass  # this can't happenn

        super().write_line_of_text(frame,
                                   text=self._output + self.cursor(),
                                   coords=_coords,
                                   show_outline=False
                                   )

    def write(self, frame, **kwargs):

        if self.text_complete is True and self.loop is False:
            return
        elif self.text_complete is True:
            self.text = self._text

        if self.one_border:
            self._write_one_border(frame, self.coords, self.color, self.ref)

        down_space = self.line_spacing + self.font_height

        if self.ref is not None:
            down_space *= -1

        i = 0
        x, y = self.coords
        for stub in self.completed_stubs:
            super().write_line_of_text(frame,
                                       stub,
                                       (x, y + i * down_space),
                                       self.color,
                                       self.ref,
                                       show_outline=False,
                                       )
            i += 1

        self.write_line_of_text(frame, coords=(x, y + i * down_space))


if __name__ == '__main__':

    from otis import camera

    capture = camera.ThreadedCameraPlayer(max_fps=30).start()
    writer = TypeWriter(coords=(100, 100), invert_border=True, max_line_length=300, one_border=True)
    writer.text = "HELLO MY NAME IS OTIS I WOULD LIKE TO BE YOUR FRIENDS"
    while True:

        capture.read()
        writer.write(capture.frame)
        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break
