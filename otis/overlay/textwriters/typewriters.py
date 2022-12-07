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

from otis.overlay import bases, shapes, textwriters

# something is happening when moving the transparent background
class TypeWriter(textwriters.TextWriter):

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
                 max_lines=None,
                 jtype='l',
                 u_spacing=.05,
                 u_ltype=None,
                 u_thickness=1,
                 underline=False,
                 border=False,
                 border_spacing=(.1, .1),
                 b_ltype=1,
                 b_thickness=1,
                 invert_background=False,
                 one_border=False,
                 transparent_background=0.,
                 anchor_point = 'lb',
                 # unique to typewriter starts here
                 key_wait_range=(.05, .1),
                 end_pause=1,
                 loop=False,
                 perma_border=True,
                 u_color=None,
                 b_color=None,
                 background=False,
                 back_color=False,
                 **kwargs
                 ):
        """
        writes text
        Args:
            coords:
            font:
            color:
            scale:
            ltype:
            thickness:
            ref:
            text:
            line_spacing:
            max_line_length:
            line_length_format:
            max_lines:
            jtype:
            u_spacing:
            u_ltype:
            u_thickness:
            underline:
            border:
            border_spacing:
            b_ltype:
            b_thickness:
            invert_background:
            one_border:
            transparent_background:
            key_wait_range:
            end_pause:
            loop:
            perma_border:
            **kwargs:
        """

        super().__init__(coords=coords,
                         font=font,
                         color=color,
                         scale=scale,
                         ltype=ltype,
                         thickness=thickness,
                         anchor_point=anchor_point,
                         ref=ref,
                         text=None,
                         line_spacing=line_spacing,
                         max_line_length=max_line_length,
                         line_length_format=line_length_format,
                         max_lines=max_lines,
                         jtype=jtype,
                         ##################### underlining #############
                         u_spacing=u_spacing,
                         u_ltype=u_ltype,
                         u_thickness=u_thickness,
                         u_color=u_color,
                         underline=underline,
                         ###############################################
                         border=border,
                         border_spacing=border_spacing,
                         b_ltype=b_ltype,
                         b_thickness=b_thickness,
                         b_color=b_color,
                         ##############################################
                         perma_border=perma_border,
                         one_border=one_border,
                         ##############################################
                         background=background,
                         transparent_background=transparent_background,
                         invert_background=invert_background,
                         back_color = back_color,
                         ################################################
                         **kwargs
                         )
        self._typing_mode = 'textwriter'
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
        self.perma_border = perma_border

    @property
    def text(self):
        return super().text

    @text.setter
    def text(self, new_text):
        # updates text_generator when name is updated
        if isinstance(new_text, (tuple, list)):
            new_text, end_pause = new_text
            self.end_pause = end_pause

        # this is straight from:
        # https://stackoverflow.com/questions/10810369/python-super-and-setting-parent-class-property
        super(self.__class__, self.__class__).text.fset(self, new_text)

        self.stub_queue = Queue()
        if new_text is not None:
            self.end_pause_timer = timers.TimeElapsedBool(wait=self.end_pause,
                                                          start=False
                                                          )

            self.text_complete = False
            for stub in self.stubs:
                self.stub_queue.put(stub)

            self.current_stub = self.stub_queue.get()
            self._output = ""
            self.completed_stubs = []

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

    def update_typing(self):

        if self.text_complete is True:
            return

        iter_empty = self.line_iterator.is_empty
        queue_empty = self.stub_queue.empty()

        if iter_empty is False and self.key_press_timer() is True:
            self._output += self.line_iterator()

        elif iter_empty is False and self.key_press_timer() is False:
            pass

        elif iter_empty is True and queue_empty is False:
            self.current_stub = self.stub_queue.get()

        elif iter_empty is True and queue_empty is True and self.end_pause_timer() is True:
            self.text_complete = True

        else:
            # don't update or make text complete, just pass
            pass


    def write(self, frame, **kwargs):
        coords = coordtools.absolute_point(self.coords, self.ref, frame)
        center_coords = cx, cy, w, h = coordtools.translate_box_coords((*coords, self.width, self.height),
                                                                        in_format=self.anchor_point + 'wh',
                                                                        out_format='cwh'
                                                                       )
        # do nothing if permaborder and loop are false
        if self.text_complete is True and self.loop is False and self.perma_border is False:
            return
        # loop the text if self.loop is True
        elif self.text_complete is True and self.loop is True:
            self.text = self.text_object.text

        # always show background with perma border or preprint if one_border is True
        if self.perma_border is True or self.one_border is True:
            if isinstance(self.background, bases.RectangleType):
                self.background.write(frame, coords=center_coords, ref=None)
            if isinstance(self.border, bases.RectangleType):
                self.border.write(frame, coords=center_coords, ref=None)

        if self.text_complete is True:
            return

        down_space = self.line_spacing + self.font_height
        # start coordinates are the top left of the otis_text box then down by 1x font height
        start_coords = (cx, cy + self.font_height, self.text_object.width, self.text_object.height)
        start_coords = coordtools.translate_box_coords(start_coords,
                                                       in_format='cwh',
                                                       out_format='ltrb',
                                                       )

        x, y = start_coords[:2]
        # this just eneded up beign the simplest way to add typewriter functionality
        self.update_typing() # update the typing
        # write the already written stubs and portion of the current stub that's been typed out
        for i, stub in enumerate(self.completed_stubs + [self._output + self.cursor()]):
            # this has to just keep running the ref stuff otherwise the justifications don't work
            # I think
            if self.jtype == 'c':
                j_offset = (self.text_object.width - self.get_text_size(stub)[0]) // 2
            elif self.jtype == 'r':
                j_offset = (self.text_object.width - self.get_text_size(stub)[0])
            else:
                j_offset = 0

            super()._write_line_of_text(frame, stub, (x + j_offset, y + i * down_space), self.color,
                                        show_outline=(not self.one_border))

if __name__ == '__main__':

    from otis import camera

    capture = camera.ThreadedCameraPlayer(max_fps=30).start()

    # writer = TypeWriter(coords=(0, 0),
    #                     ref='c',
    #                     jtype='c',
    #                     anchor_point='c',
    #                     scale=1.5,
    #                     perma_border=True,
    #                     underline=True,
    #                     border=True,
    #                     # max_line_length=1000,
    #                     one_border=True,
    #                     border_spacing=(.3, .3),
    #                     max_lines=2,
    #                     transparent_background=.9,
    #                     loop=True,
    #                     color='g'
    #                     )

    border = True
    underline = False
    line_spacing = 30
    border_spacing = (10, 20)
    transparent_background = .1
    one_border = True
    max_lines = 3
    u_spacing = .1
    scale = 1.
    texts = ["I'm justified right with a left-bottom achor_point ('lb')",
             "I'm justified center with a left-top anchor_point ('lt')",
             "I'm justified left with a right-bottom anchor_point ('rb')",
             "I'm justified center with a right-top anchor_point ('tr')"]

    aps = ('lb', 'lt', 'rb', 'rt')
    justs = ('r', 'c', 'l', 'c')
    # justs = ('l')*4
    writers = []
    TEXT = "HELLO I AM OTIS, I WOULD LOVE TO BE YOUR FRIEND AND HELP YOU MAKE THINGS, YEAH"
    for a, j in zip(aps, justs):
        writer = TypeWriter(text=TEXT,
                            coords=(0, 0),
                            u_spacing=u_spacing,
                            ref='c',
                            jtype=j,
                            anchor_point=a,
                            scale=scale,
                            perma_border=True,
                            underline=underline,
                            border=True,
                            max_line_length=500,
                            one_border=one_border,
                            border_spacing=border_spacing,
                            max_lines=3,
                            transparent_background=.9,
                            loop=True,
                            color='g'
                            )

        writers.append(writer)

    circle = shapes.Circle(center=capture.f_center, radius = 10, thickness=-1)
    while True:
        _, frame = capture.read()

        for writer in writers:
            writer.write(frame)
        circle.write(frame)
        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break
