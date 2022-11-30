import time
from queue import Queue
import copy
import types

import cv2
import numpy as np

import otis.helpers.coordtools
import otis.helpers.maths
from otis.helpers import timers, colortools, shapefunctions, texttools, cvtools, dstructures, coordtools, misc
from otis.overlay import bases, shapes

class TextWriter(bases.AssetWriter):
    text_fun: types.FunctionType
    outliner: shapes.ShapeAsset

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
                 max_line_length = None,
                 line_length_format = 'pixels',
                 n_lines = None,
                 border_spacing = (5, 5),
                 jtype='l',
                 outliner=None,
                 o_ltype=None,
                 o_thickness=1,
                 invert_border=False,
                 one_border = False
                 ):

        super().__init__()


        self.font = font # property
        self.color = color # property
        self.ref = ref
        self.coords = np.array(coords, dtype=int)
        self.scale = scale
        self.ltype = ltype

        self.max_line_length = max_line_length
        self.line_length_format = line_length_format
        self.n_lines = n_lines
        self.n_split_plus = 1
        self.line_spacing = line_spacing
        self.thickness = thickness
        self.jtype = jtype
        self.border_spacing = border_spacing # property
        self.o_ltype = o_ltype
        self.o_thickness = o_thickness
        self.one_border = one_border

        if invert_border is True:
            self.outliner = 'border'
            self.outliner.thickness = -1
        elif self.one_border is True:
            self.outliner = 'border'
            self.outliner.coord_format = 'ltwh'

        else:
            self.outliner = outliner

        self.invert_border = invert_border
        self.text_stubs = []
        self.text = text  # property
        self.text_fun = None

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, new_font):
        self._font = texttools.TEXT_HASH[new_font]

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):

        self._text = new_text
        if self._text is None:
            return

        self.text_stubs = texttools.split_text_into_lines(new_text,
                                                          max_line_length=self.max_line_length,
                                                          n_lines=self.n_lines,
                                                          line_length_format=self.line_length_format,
                                                          font=self.font,
                                                          scale=self.scale,
                                                          thickness=self.thickness,
                                                          )

        # for determining borders. all in pixels
        if self.max_line_length != 'pixels':
            longest_stub = max(self.text_stubs, key=lambda stub: self.get_text_size(stub)[0])
            self.total_length = self.get_text_size(longest_stub)[0]
        else:
            self.total_length = self.max_line_length

        if self.n_lines is None:
            n_stubs = len(self.text_stubs)
        else:
            n_stubs = self.n_lines

        self.total_height = n_stubs * self.font_height + (n_stubs-1) * self.line_spacing



    @property
    def outliner(self):
        return self._outliner

    @outliner.setter
    def outliner(self, new_style):

        if new_style is None:
            self._outliner = None

        elif new_style == 'border':
            self._outliner = shapes.Rectangle((0, 0, 0, 0),
                                             color=self.color,
                                             thickness=self.o_thickness,
                                             ltype=self.o_ltype,
                                             ref=None,
                                             dim=None,
                                             coord_format='lbwh',
                                             update_format=None,
                                             )

        elif new_style == 'underline':
            self._outliner = shapes.Line((0, 0, 0, 0),
                                        color=self.color,
                                        thickness=self.o_thickness,
                                        ltype=self.o_ltype,
                                        ref=None,
                                        dim=None,
                                        coord_format='points',
                                        )

        elif isinstance(new_style, (shapes.Rectangle, shapes.Line)):
            self._outliner = copy.deepcopy(new_style)

        else:
            pass

    @property
    def font_height(self):
        return self.get_text_size("T")[1]

    @property
    def font_width(self):
        return self.get_text_size("T")[0]

    @property
    def text_length(self):
        return self.get_text_size(self.text)[0]

    @property
    def border_spacing(self):
        h_space, v_space = self._border_spacing
        if isinstance(h_space, float):
            h_space = int(h_space * self.font_height)
        if isinstance(v_space, float):
            v_space = int(v_space * self.font_height)
        return h_space, v_space

    @border_spacing.setter
    def border_spacing(self, new_spacing):
        if isinstance(new_spacing, (int, float)):
            self._border_spacing = (new_spacing, new_spacing)
        else:
            self._border_spacing = new_spacing

    @property
    def line_spacing(self):
        spacing = self._line_spacing
        if isinstance(spacing, int):
            return spacing
        elif isinstance(spacing, float):
            return int(spacing * self.font_height)
        else:
            raise ValueError("line_spacing must either be int or float")

    @line_spacing.setter
    def line_spacing(self, spacing):
        self._line_spacing = spacing


    def get_text_size(self, text=None):
        _text = self.text if text is None else text
        return cv2.getTextSize(_text, self.font, self.scale, self.ltype)[0]

    def write_line_of_text(self,
                           frame,
                           text=None,
                           coords=None,
                           color=None,
                           ref=None,
                           jtype=None,
                           show_outline=True,
                           ):
        """
        :type frame: np.array
        """
        _text, _coords, _color, _ref , _jtype = misc.update_save_keywords(self,
                                                                 locals(),
                                                                 ['text', 'coords','color', 'ref', 'jtype'],
                                                                 )

        justified_position = texttools.find_justified_start(text,
                                                            _coords,
                                                            font=self.font,
                                                            scale= self.scale,
                                                            thickness= self.thickness,
                                                            jtype=_jtype,
                                                            ref=_ref,
                                                            dim=frame
                                                            )

        h_space, v_space = self.border_spacing
        if isinstance(self.outliner, shapes.Rectangle) and show_outline is True:

            l = justified_position[0] - h_space
            b = justified_position[1] + v_space
            w, h = self.get_text_size(_text)

            w += 2*h_space
            h += 2*v_space

            self.outliner.write(frame, (l, b, w, h), color=_color)

        # for underlined text
        elif isinstance(self.outliner, shapes.Line):
            w, _ = self.get_text_size()
            self.outliner.write(frame, (0, -v_space, w, -v_space), color=_color, ref=justified_position)
        else:
            pass

        if self.invert_border is True:
            _color = 'w'

        shapefunctions.write_text(frame,
                                  _text,
                                  pos=justified_position,
                                  font=self.font,
                                  color=_color,
                                  scale=self.scale,
                                  thickness=self.thickness,
                                  ltype=self.ltype,
                                  ref=None,
                                  jtype='l'
                                  )

    def write_outline(self, frame, justified_position, color=None):
        _color = self.color if color is None else color
        # for bordered text
        h_space, v_space = self.border_spacing
        if isinstance(self.outliner, shapes.Rectangle):

            l = justified_position[0] - h_space
            b = justified_position[1] + v_space
            w, h = self.get_text_size()

            w += 2*h_space
            h += 2*v_space

            self.outliner.write(frame, (l, b, w, h), color=_color)

        # for underlined text
        elif isinstance(self.outliner, shapes.Line):
            w, _ = self.get_text_size()
            self.outliner.write(frame, (0, -v_space, w, -v_space), color=_color, ref=justified_position)
        else:
            pass

    def write(self, frame, text=None, coords=None, color=None, ref=None, save=False):
        _coords = self.coords if coords is None else coords
        _ref = self.ref if ref is None else ref

        if text is not None:
            self.write_line_of_text(frame,
                                    text=text,
                                    coords=_coords,
                                    color=color,
                                    ref=_ref
                                    )

        else:
            if self.one_border:
                self._write_one_border(frame, self.coords, self.color, self.ref)
            down_space = self.line_spacing + self.font_height
            if _ref is not None:
                down_space *= -1
            for i, stub in enumerate(self.text_stubs):
                x, y = _coords
                self.write_line_of_text(frame,
                                        text=stub,
                                        coords=(x, y+i*down_space),
                                        ref=_ref,
                                        show_outline=(not self.one_border),
                                        )



    def _write_one_border(self, frame, coords, color, ref):
        if isinstance(self.outliner, shapes.Rectangle):
            x, y = coordtools.abs_point(coords, ref, frame)
            v_space, h_space = self.border_spacing
            h = self.total_height + 2 * v_space
            w = self.total_length + 2 * h_space
            y -= (self.font_height + v_space)
            if self.jtype == 'l':
                x -= h_space
            elif self.jtype == 'r':
                x -= h_space + self.total_length
            else:
                x -= h_space + self.total_length//2
            self.outliner.coord_format = 'ltwh'
            self.outliner.write(frame, (x,y, w, h), color=color)

    def write_fun(self, frame, *args, **kwargs):
        self.write(frame, self.text_fun(*args, **kwargs))


class NameTag(TextWriter):

    def __init__(self,
                 name = None,
                 v_offset=20,
                 h_offset=0,
                 attached_to=None,
                 color = None,
                 box_reference='c', #'c', 'l', 'r'
                 line_to_box= False,
                 ltb_offset=0,
                 **kwargs,
                 ):

        super().__init__(**kwargs)

        self.name = name
        self.v_offset = v_offset
        self.h_offset = h_offset
        self.attached_to = attached_to
        self.color = color
        self.box_reference=box_reference
        self.ltb_offset = ltb_offset
        self.line_to_box = line_to_box
        self.jtype = box_reference

    @property
    def name(self):
        return self.text

    @name.setter
    def name(self, new_name):
        self.text = new_name

    def write(self, frame, name=None, **kwargs):
        #might wanna change this so that it just get's entered each time
        if self.name is not None:
            text = self.name
        elif self.attached_to.name is not None:
            text = self.attached_to.name
        else:
            return

        if self.color is not None:
            color = self.color
        else:
            color = self.attached_to.color

        x, y, w, h = self.attached_to.center_width_height()

        if self.box_reference == 'l':
            ref = (x-w//2, y-h//2)

        elif self.box_reference == 'r':
            ref = (x+w//2, y-h//2)
        else:
            ref = (x, y-h//2)

        super().write(frame,
                      text=text,
                      coords=(self.ltb_offset,
                              self.v_offset + self.border_spacing[1]),
                      color=color,
                      ref=ref,
                      save=False)

        shapefunctions.draw_line(frame,
                                 ref,
                                 (ref[0], ref[1]-self.v_offset + self.border_spacing[1]),
                                 thickness=1,
                                 color=color
                                 )


class InfoWriter(TextWriter):

    def __init__(self,
                 text_fun=lambda: "",
                 *args,
                 **kwargs
                 ):

        super().__init__(**kwargs)
        self.text_fun = text_fun

    def write(self, frame, *args, **kwargs):
        super().write(frame, text=self.text_fun(*args, **kwargs))


class TimerWriter(InfoWriter):
    timer_hash = {"first": timers.TimeSinceFirst,
                  "last": timers.TimeSinceLast,
                  "countdown": timers.CountDownTimer}

    def __init__(self,
                 title="update_limiter",
                 timer_type="last",
                 per_second=False,
                 roundw=1,
                 moving_average=10,
                 count_from=10,
                 *args,
                 **kwargs
                 ):

        super().__init__(*args, **kwargs)

        self.per_second = per_second
        self.title = title
        self.roundw = roundw
        self.moving_average = moving_average
        self.count_from = count_from
        self.timer_type = timer_type
        self._timer_complete = False

        if timer_type == "last":
            self._timer = timers.TimeSinceLast()

            if per_second is True:
                self._timer()

            if moving_average is not None:
                self.moving_average = otis.helpers.maths.MovingAverage(moving_average)

        elif timer_type == 'countdown':
            self._timer = timers.CountDownTimer(self.count_from)
            self.per_second = False
            self.moving_average = None


        elif timer_type == "first":
            self._timer = timers.TimeSinceFirst()
            self.per_second = False
            self.moving_average = None

        else:
            raise ValueError("invalid timer_type selection")

    @property
    def timer_finished(self):
        if self.timer_type == 'countdown':
            return self._timer.is_finished

    def timer(self):
        t = self._timer()
        if self.per_second is True and (t != 0 or t != 0.0):
            t = 1 / t

        if self.moving_average is not None:
            t = self.moving_average.update(t)

        if self.roundw == 0:
            t = int(t)
        else:
            t = round(t, self.roundw)

        return t

    def write(self, frame, text=None):

        super(InfoWriter, self).write(frame, f'{self.title} : {self.timer()}')


class TypeWriter(TextWriter):

    def __init__(self,
                 coords=(0, 0),  # coords
                 font='duplex',
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # _font scale,
                 ltype=2,
                 dt=None,
                 key_wait=(.04, .14),
                 end_pause=1,
                 loop=False,
                 ref=None,
                 text=None,
                 **kwargs
                 ):

        super().__init__(coords=coords, font=font, color=color, scale=scale, ltype=ltype, ref=ref, text=text, **kwargs)

        self.dt = dt
        self._key_wait = key_wait
        self.end_pause = end_pause
        self.end_timer = timers.TimeElapsedBool(end_pause)
        self.loop = loop
        self.line_iter = dstructures.BoundIterator([0])
        self.line_complete = True
        self.text = text
        self._output = ""
        self.cursor = Cursor()
        self.script = Queue()
        self.ktimer = timers.CallFrequencyLimiter(self.key_wait)

    @property
    def line(self):
        return self._line

    @line.setter
    def text(self, new_text):
        # updates text_generator when name is updated
        self._line = new_text
        self.tick = time.time()

        if new_text is None:
            self.line_iter = None
            self.line_complete = True
            self._output = ""

        else:
            self.line_iter = dstructures.BoundIterator(new_text)
            self.line_complete = False
            self._output = ""

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
            self.text = self.script.put(new_lines)

        return self

    def type_line(self, frame, coords=None, ref=None):
        if coords is not None:
            self.coords = coordtools.abs_point(coords, ref, frame)
        # if there's more in the name generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.line_complete is True and self.script.empty() is True:
            return

        elif self.line_complete is True and self.script.empty() is False:
            self.text = self.script.get()
        # update if there is more to teh text and t > wait
        elif self.line_iter.is_empty is False:

            if self.ktimer(self.key_wait):
                self._output += self.line_iter()

            self.write(frame, self._output)

        # if the text is done, but the end pause is still going. write whole text with cursor
        elif self.line_iter.is_empty and self.end_timer() is False:

            self.write(frame, self._output + self.cursor())

        # empty text generator and t > pause sets the text to done
        else:

            self.line_complete = True

            self.end_timer.reset(True)


class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.clock = timers.TimeSinceLast()
        self.clock()
        self.text_fun = lambda: f'FPS = {int(1 / self.clock())}'


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


class MultiTypeWriter(TypeWriter):

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
        self.end_timer.wait = self.end_pause if pause is None else pause

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
        self.end_timer.reset()
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
                self.write(frame, self._used_stubs[i], coords=(p0, p1 + i * v_move))
            # then type out current text
            self._type_stub(frame, coords=(p0, p1 + n_fin * v_move))
            return

        # refill and keep going
        if self._stub_complete is True and self._stub_queue.empty() is False:
            self.next_stub()

        else:  # same as above but the first check of the tiemr will start it.
            if self.end_timer() is False:
                for i in range(n_fin):
                    self.write(frame, self._used_stubs[i], coords=(p0, p1 + i * v_move))
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
            _coords = coordtools.abs_point(coords, ref, frame)

        if self._stub_iter.is_empty is False:
            # pause for a comma a tad
            if len(self._output) > 0 and self._output[-1] == ',':
                cpf = self.comma_pause_factor
            else:
                cpf = 1

            if self.ktimer(cpf * self.key_wait):
                self._output += self._stub_iter()

            self.write(frame, self._output, coords=_coords)

        # if the text is done, but the end pause is still going. write whole text with cursor
        else:
            self.write(frame, text=self._output + self.cursor(), coords=_coords)

            self._stub_complete = True


class ScriptTypeWriter(MultiTypeWriter):

    def __init__(self, line_length, *args, **kwargs):
        super().__init__(line_length, *args, **kwargs)

        self.script_queue = Queue()

    def add_script(self, script):
        for line in script:
            self.script_queue.put(line)
        return self

    def type_line(self, frame, **kwargs):
        if self.line_complete is False:
            super().type_line(frame)

        elif self.line_complete is True and not self.script_queue.empty():
            new_line = self.script_queue.get()

            self.add_line(new_line)
            super().type_line(frame)


class OTIS(ScriptTypeWriter):
    def __init__(self, line_length,
                 *args,
                 coords=(450, 900),
                 scale=2,
                 end_pause=3,
                 color='g',
                 **kwargs
                 ):

        super().__init__(line_length,
                         *args,
                         coords=coords,
                         scale=scale,
                         end_pause=end_pause,
                         color=color,
                         **kwargs
                         )

        self.key_wait = [.05, .12]

        f = self.get_text_size("T")[0]
        p = self.coords
        # f = self.font_height
        v = self.line_spacing
        l = self.llength
        ### portions to grey out
        self.gls = (
            p[1] - f - v,
            p[1] + 2 * f + int(3.5 * v),
            p[0] - v,
            p[0] + l + 2 * v
        )

    def type_line(self, frame, box=True):
        gls = self.gls

        if box is True:
            portion = frame[gls[0]:gls[1], gls[2]:gls[3]]
            colortools.frame_portion_to_grey(portion)

        super().type_line(frame)

if __name__=='__main__':
    from otis import camera
    capture = camera.ThreadedCameraPlayer(max_fps=30).start()
    writer = TextWriter(ref='c',
                        jtype='c',
                        text="HELLO MY NAME IS OTIS I WOULD LIKE TO BE YOUR FRIENDS",
                        n_lines=3
                        )

    while True:

        capture.read()
        writer.write(capture.frame)

        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break


