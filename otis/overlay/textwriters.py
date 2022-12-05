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

    def __init__(self,
                 coords=(0, 0),
                 font='duplex',
                 color='r',
                 scale=1.,
                 ltype=1,
                 thickness=1,
                 ref=None,
                 text=None,
                 line_spacing=.5,
                 max_line_length=None,
                 line_length_format='pixels',
                 n_lines=None,
                 jtype='l',
                 u_spacing=.1,
                 u_ltype=None,
                 u_thickness=1,
                 underliner=False,
                 border=False,
                 border_spacing=(.1, .1),
                 b_ltype=None,
                 b_thickness=1,
                 invert_border=False,
                 one_border=False,
                 transparent_background=0.,
                 perma_border = False,
                 ):

        super().__init__()

        self.font = font  # property
        self.color = color  # property
        self.ref = ref
        self.coords = np.array(coords, dtype=int)
        self.scale = scale
        self.ltype = ltype

        self.max_line_length = max_line_length
        self.line_length_format = line_length_format
        self.n_lines = n_lines
        self.line_spacing = line_spacing
        self.thickness = thickness
        self.jtype = jtype

        ########################### underliner ###########################################

        self.u_spacing = self._int_or_float_times_font_size(u_spacing)
        self.u_ltype = u_ltype
        self.u_thickness = u_thickness

        if isinstance(underliner, shapes.Line) or underliner is False:
            self.underliner = underliner
        else:
            self.underliner = shapes.Line((0, 0, 0, 0),
                                          color=self.color,
                                          thickness=self.u_thickness,
                                          ltype=self.u_ltype,
                                          ref=None,
                                          dim=None,
                                          coord_format='points',
                                          )

        #### border ####################################################

        if transparent_background != 0:
            border = shapes.TransparentBackground(coord_format= 'lbwh', transparency=transparent_background)

        elif one_border is True and border is False and not isinstance(border, bases.RectangleType):
            border = True

        elif invert_border is True and border is False and not isinstance(border, bases.RectangleType):
            border = True

        self.border_spacing = border_spacing  # property
        self.b_ltype = b_ltype
        self.b_thickness = b_thickness

        if isinstance(border, bases.RectangleType) or border is False:
            self.border = border

        else:
            self.border = shapes.Rectangle((0, 0, 0, 0),
                                           color=self.color,
                                           thickness=self.b_thickness,
                                           ltype=self.b_ltype,
                                           ref=None,
                                           dim=None,
                                           coord_format='lbwh',
                                           update_format=None,
                                           )

        self.one_border = one_border
        self.invert_border = invert_border

        if self.one_border is True:
            self.border.coord_format = 'ltwh'

        if self.invert_border is True:
            self.border.thickness = -1

        ################ Text Set UP #################################################################
        self.perma_border = perma_border
        self.text_stubs = []
        self.text = text  # property
        self.text_fun = lambda : ""


        if self.n_lines is None:
            n_stubs = len(self.text_stubs)
        else:
            n_stubs = self.n_lines
        self.total_height = n_stubs * self.font_height + (n_stubs - 1) * self.line_spacing

        try:
            if self.line_length_format != 'pixels':
                longest_stub = max(self.text_stubs, key=lambda stub: self.get_text_size(stub)[0])
                self.total_length = self.get_text_size(longest_stub)[0]
            else:
                self.total_length = self.max_line_length
        except:
            pass



    ############################# PROPERTIES ##########################################################
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

        self.text_stubs = texttools.split_text_into_stubs(new_text,
                                                          max_line_length=self.max_line_length,
                                                          n_lines=self.n_lines,
                                                          line_length_format=self.line_length_format,
                                                          font=self.font,
                                                          scale=self.scale,
                                                          thickness=self.thickness,
                                                          )

        # for determining borders. all in pixels

        if self.perma_border is False:
            if self.max_line_length != 'pixels':
                longest_stub = max(self.text_stubs, key=lambda stub: self.get_text_size(stub)[0])
                self.total_length = self.get_text_size(longest_stub)[0]
            else:
                self.total_length = self.max_line_length

            if self.n_lines is None:
                n_stubs = len(self.text_stubs)
            else:
                n_stubs = self.n_lines

            self.total_height = n_stubs * self.font_height + (n_stubs - 1) * self.line_spacing

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
        return cv2.getTextSize(_text, self.font, self.scale, self.thickness)[0]

    ################################## METHODS #############################################
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
        _text, _coords, _color, _ref, _jtype = misc.update_save_keywords(self,
                                                                         locals(),
                                                                         ['text', 'coords', 'color', 'ref', 'jtype'],
                                                                         )

        justified_position = texttools.find_justified_start(text,
                                                            _coords,
                                                            font=self.font,
                                                            scale=self.scale,
                                                            thickness=self.thickness,
                                                            jtype=_jtype,
                                                            ref=_ref,
                                                            dim=frame
                                                            )

        h_space, v_space = self.border_spacing
        w, h = self.get_text_size(_text)

        if isinstance(self.border, bases.RectangleType) and show_outline is True:

            l = justified_position[0] - h_space
            b = justified_position[1] + v_space
            w += 2 * h_space
            h += 2 * v_space
            self.border.write(frame, (l, b, w, h), color=_color)

        if self.invert_border is True:
            _color = 'w'

        if isinstance(self.underliner, bases.LineType):
            self.underliner.write(frame,
                                  (0, -v_space, w, -v_space),
                                  color=_color,
                                  ref=justified_position,
                                  )

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

    def write(self, frame, text=None, coords=None, color=None, ref=None, save=False):
        _coords = self.coords if coords is None else coords
        _ref = self.ref if ref is None else ref
        _color = self.color if color is None else color

        if text is not None:

            self.write_line_of_text(frame,
                                    text=text,
                                    coords=_coords,
                                    color=color,
                                    ref=_ref
                                    )

        else:

            if self.one_border:
                self._write_one_border(frame, self.coords, _color, self.ref)

            down_space = self.line_spacing + self.font_height
            if _ref is not None:
                down_space *= -1

            for i, stub in enumerate(self.text_stubs):
                x, y = _coords
                self.write_line_of_text(frame,
                                        text=stub,
                                        coords=(x, y + i * down_space),
                                        ref=_ref,
                                        show_outline=(not self.one_border),
                                        )

    def _write_one_border(self, frame, coords, color, ref):

        x, y = coordtools.absolute_point(coords, ref, frame)
        v_space, h_space = self.border_spacing
        h = self.total_height + 2 * v_space
        w = self.total_length + 2 * h_space
        y -= (self.font_height + v_space)

        if self.jtype == 'l':
            x -= h_space
        elif self.jtype == 'r':
            x -= h_space + self.total_length
        else:
            x -= h_space + self.total_length // 2

        border = self.border
        border.write(frame,
                     coords= (x, y, w, h),
                     color=color
                     )

    def write_fun(self, frame, *args, **kwargs):
        self.write(frame, self.text_fun(*args, **kwargs))

    def _int_or_float_times_font_size(self, value):

        if isinstance(value, float):
            return int(value * self.font_height)
        else:
            return value

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


class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.clock = timers.TimeSinceLast()
        self.clock()
        self.text_fun = lambda: f'FPS = {int(1 / self.clock())}'


def main():
    font_list = ('simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small', 's_simplex', 's_complex')
    from otis import camera

    capture = camera.ThreadedCameraPlayer(max_fps=30, dim=(1280, 720)).start()

    writer = TextWriter(ref='c',
                        jtype='c',
                        text="HELLO MY NAME",
                        border=True,
                        one_border=False,
                        border_spacing=(.5, .25),
                        transparent_background=1.,
                        color ='g'
                        )

    while True:

        _, frame = capture.read()

        for i, font in enumerate(font_list):
            writer.font = font
            writer.write(frame, text=font, coords=(0, 200-50*i))
        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break

if __name__ == '__main__':
    main()
