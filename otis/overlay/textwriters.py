"""
Contains TextWriter and several other

"""
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
from otis.overlay import otistext


# todo - texttxt writer perma border doesn't work without one border turned on
class TextWriter(bases.AssetWriter):
    text_fun: types.FunctionType

    def __init__(self,
                 coords=(0, 0),
                 font='duplex',
                 color='r',  # can be 'r', 'g', 'u', 'w', 'b', 'y', 'c', 'm', 'grey' or (G, B, R) color tuple
                 scale=1.,
                 ltype=1,
                 thickness=1,
                 anchor_point=None,
                 ref=None,
                 text=None,
                 line_spacing=.5,  # int = pixels, float = percentage of font height
                 max_line_length=None,  #
                 line_length_format='pixels',  # pixels or characters
                 max_lines=None,  #
                 jtype='l',
                 ##################### underlining #############
                 u_spacing=.1,
                 u_ltype=None,
                 u_thickness=1,
                 u_color=None,
                 underline=False,
                 #################### BORDER ##########################
                 border=False,
                 border_spacing=(.1, .1),
                 b_ltype=None,
                 b_thickness=1,
                 b_color=None,
                 ##################### background and border #####################
                 one_border=False,
                 perma_border=False,
                 ##################### background #####################################
                 background=False,
                 transparent_background=0.,
                 back_color=None,
                 invert_background=False,
                 # for multiple lines, makes it so there is one big background/border
                 ):
        """

        Args:
            coords: tuple
                (x, y)
            font: str
                'simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small', 's_simplex', 's_complex'
            color: str or tuple
                can be 'r', 'g', 'u', 'w', 'b', 'y', 'c', 'm', 'grey' or (G, B, R) color tuple
            scale: float
                increases the size of text
            ltype: int
                cv2 line type
            thickness: int
                cv2 line thickness
            ref: None, tuple
                absolute frame coords
            text: str

            line_spacing: int or float
                int = pixels, float = percentage of font height
            max_line_length: int
                controls line breaks
            line_length_format: int, default = None
                pixels or characters
            max_lines: int or None.
                if max_line_length is also set
            jtype: str
                justification type, 'c', 'l', 'r'
            u_spacing: int/float
                underline vertical spacing int or float if int -> pixels. float -> % of font height
            u_ltype:int
                underline line ltype
            u_thickness: int
                underline thickniss
            underline: bool or shapes.Line
                under line the text
            border: bool or shapes.Rectangle
                put a border around the text
            border_spacing:
            b_ltype: int
                border line type
            b_thickness: int
                border thickness
            invert_background: bool
                background is colored and text is white
            one_border: bool
                for multiple lines, makes it so there is one big background/border
            transparent_background:  float
                between 0 and 1 or None, makes background grey transparent
            perma_border: bool
                border doesn't disappoint when there's no text
        """

        super().__init__()
        self.thickness = thickness
        self.font = font  # property
        self.color = color  # property
        self.ref = ref
        self.coords = np.array(coords, dtype=int)
        self.scale = scale
        self.ltype = ltype

        self.max_line_length = max_line_length
        self.line_length_format = line_length_format
        self.n_lines = max_lines
        self.line_spacing = line_spacing

        self.jtype = jtype
        self.anchor_point = anchor_point

        ##################################### underline ###########################################

        self.u_spacing = self._int_or_float_times_font_size(u_spacing)
        self.u_ltype = u_ltype
        self.u_thickness = u_thickness
        self.u_color = self.color if u_color is None else u_color

        if isinstance(underline, shapes.Line) or underline is False:
            self.underline = underline
        else:
            self.underline = shapes.Line((0, 0, 0, 0),
                                         color=self.color,
                                         thickness=self.u_thickness,
                                         ltype=self.u_ltype,
                                         ref=None,
                                         dim=None,
                                         coord_format='points',
                                         )

        ####################################  background  #####################################################
        self.one_border = one_border
        self.invert_background = invert_background
        self.back_color = back_color if back_color is not None else self.color

        if invert_background is True and border == False and background == False:
            background = True

        if transparent_background != 0:
            self.background = shapes.TransparentBackground(coord_format='lbwh',
                                                           transparency=transparent_background
                                                           )

        elif isinstance(background, bases.RectangleType) or border == False or border == None:
            self.background = background

        else:
            self.background = shapes.Rectangle((0, 0, 0, 0),
                                               color=self.back_color,
                                               thickness=-1,
                                               ref=None,
                                               dim=None,
                                               coord_format='lbwh',
                                               update_format=None,
                                               )

        ################################### border         ######################################################

        self.border_spacing = border_spacing  # property
        self.b_ltype = b_ltype if b_ltype is not None else self.ltype
        self.b_thickness = b_thickness if b_thickness is not None else self.thickness
        self.b_color = b_color if b_color is not None else self.color

        if isinstance(border, bases.RectangleType) or border == False:
            self.border = border

        else:
            self.border = shapes.Rectangle((0, 0, 0, 0),
                                           color=self.b_color,
                                           thickness=self.b_thickness,
                                           ltype=self.b_ltype,
                                           ref=None,
                                           dim=None,
                                           coord_format='lbwh',
                                           update_format=None,
                                           )

        ################ Text Set Up #################################################################

        self.perma_border = perma_border
        self.text = text  # property
        self.text_fun = lambda: ""

    ############################# PROPERTIES ##########################################################
    @property
    def stubs(self):
        return self.text_object.stubs

    @property
    def font(self):
        return self._font

    @font.setter
    def font(self, new_font):
        self._font = texttools.FONT_HASH[new_font]

    @property
    def text(self):
        return self.text_object.text

    @text.setter
    def text(self, new_text):
        """

        Args:
            new_text:
        """
        if new_text is None:
            new_text = ""

        self.text_object = otistext.OtisText(new_text,
                                             anchor_point=self.anchor_point,
                                             font=self.font,
                                             scale=self.scale,
                                             thickness=self.thickness,
                                             line_spacing=self.line_spacing,
                                             max_line_length=self.max_line_length,
                                             line_length_format=self.line_length_format,
                                             max_lines=self.n_lines,
                                             perma_border=self.perma_border
                                             )

    @property
    def total_height(self):
        return self.text_object.height

    @property
    def total_length(self):
        return self.text_object.width

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
        return self._border_spacing

    @border_spacing.setter
    def border_spacing(self, new_spacing):
        if isinstance(new_spacing, (int, float)):
            _new_spacing = (new_spacing, new_spacing)
        else:
            _new_spacing = new_spacing
        h_space, v_space = _new_spacing
        if isinstance(h_space, float):
            h_space = int(h_space * self.font_height)
        if isinstance(v_space, float):
            v_space = int(v_space * self.font_height)
        self._border_spacing = np.array((h_space, v_space))

    @property
    def line_spacing(self):
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, spacing):
        if isinstance(spacing, int):
            self._line_spacing = spacing
        elif isinstance(spacing, float):
            self._line_spacing = int(spacing * self.font_height)
        else:
            raise ValueError("line_spacing must either be int or float")

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
                           save=False
                           ):
        """
        :type frame: np.array
        """
        _text, _coords, _color, _ref, _jtype = misc.update_save_keywords(self,
                                                                         locals(),
                                                                         ['text', 'coords',
                                                                          'color', 'ref',
                                                                          'jtype'],
                                                                         )
        #
        justified_position = texttools.find_justified_start(text,
                                                            _coords,
                                                            font=self.font,
                                                            scale=self.scale,
                                                            thickness=self.thickness,
                                                            jtype=_jtype,
                                                            ref=ref,
                                                            dim=frame
                                                            )

        h_space, v_space = self.border_spacing
        w, h = self.get_text_size(_text)
        # write border
        l = justified_position[0] - h_space
        b = justified_position[1] + v_space
        w += 2 * h_space
        h += 2 * v_space

        if isinstance(self.background, bases.RectangleType) and show_outline is True:
            self.background.write(frame, (l, b, w, h), color=_color)

        if isinstance(self.border, bases.RectangleType) and show_outline is True:
            self.border.write(frame, (l, b, w, h), color=_color)

        if self.invert_background is True:
            _color = 'w'
        # underline
        if isinstance(self.underline, bases.LineType):
            self.underline.write(frame,
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

    def write(self, frame, text: str = None, coords=None, color=None, ref=None, save=False):
        """

        Args:
            frame:
            text:
            coords: 2d coords
            color: from color function
            ref:
            save: nothing currently

        Returns:
        """
        _coords = self.coords if coords is None else coords
        _ref = self.ref if ref is None else ref
        _color = self.color if color is None else color
        _color = colortools.color_function(_color)

        _coords = coordtools.absolute_point(self.coords, self.ref, frame)
        _coords += self.text_object.start_offset

        # if _ref is not None:
        #     _anchor_offset[1] *= -1

        # = _coords + _anchor_offset
        # if fed a line of text it just writes it.
        if text is not None:
            self.write_line_of_text(frame,
                                    text=text,
                                    coords=_coords,
                                    color=_color,
                                    ref=None
                                    )

        else:
            # otherwise it reads from the stubs
            if self.one_border:
                self._write_one_border(frame, _coords, _color, None)

            down_space = self.line_spacing + self.font_height

            x, y, = _coords
            for i, stub in enumerate(self.stubs):
                # this has to just keep running the ref stuff otherwise the justifications don't work
                # I think
                self.write_line_of_text(frame,
                                        stub,
                                        (x, y + i * down_space),
                                        _color,
                                        ref=None,
                                        show_outline=(not self.one_border),

                                        )

    def _write_one_border(self, frame, coords, color, ref):

        x, y = coordtools.absolute_point(coords, ref, frame)
        v_space, h_space = self.border_spacing
        h = self.total_height + 2 * v_space
        w = self.total_length + 2 * h_space
        y += (self.n_lines - 1) * self.font_height + (self.n_lines) * self.line_spacing

        if self.jtype == 'l':
            x -= h_space
        elif self.jtype == 'r':
            x -= h_space - self.total_length
        else:
            x -= h_space - self.total_length // 2

        if isinstance(self.background, shapes.Rectangle):
            self.background.write(frame,
                              coords=(x, y, w, h),
                              color=self.back_color,
                              )

        if isinstance(self.border, shapes.Rectangle):
            self.border.write(frame,
                              coords=(x, y, w, h),
                              color=self.b_color,
                              )

    def write_fun(self, frame, *args, **kwargs):
        self.write(frame, self.text_fun(*args, **kwargs))

    def _int_or_float_times_font_size(self, value):

        if isinstance(value, float):
            return int(value * self.font_height)
        else:
            return value

    def center_width_height(self):
        coords = coordtools.absolute_point(self.coords, self.ref)
        coords += self.text_object.start_offset
        x, y = coords
        v_space, h_space = self.border_spacing
        h = self.total_height + 2 * v_space
        w = self.total_length + 2 * h_space
        y -= (self.font_height + v_space)

        if self.jtype == 'l':
            x -= h_space
        elif self.jtype == 'r':
            x -= h_space - self.total_length
        else:
            x -= h_space - self.total_length // 2
        return x, y, w, h

    @property
    def radius(self):
        return (self.text_object.height + self.text_object.width) // 4


class NameTag(TextWriter):

    def __init__(self,
                 name=None,
                 v_offset=20,
                 h_offset=0,
                 attached_to=None,
                 color=None,
                 box_reference='c',  # 'c', 'l', 'r'
                 line_to_box=False,
                 ltb_offset=0,
                 **kwargs,
                 ):

        super().__init__(**kwargs)

        self.name = name
        self.v_offset = v_offset
        self.h_offset = h_offset
        self.attached_to = attached_to
        self.color = color
        self.box_reference = box_reference
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
        # might wanna change this so that it just get's entered each time
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
            ref = (x - w // 2, y - h // 2)

        elif self.box_reference == 'r':
            ref = (x + w // 2, y - h // 2)
        else:
            ref = (x, y - h // 2)

        super().write(frame,
                      text=text,
                      coords=(self.ltb_offset,
                              self.v_offset + self.border_spacing[1]),
                      color=color,
                      ref=ref,
                      save=False)

        shapefunctions.draw_line(frame,
                                 ref,
                                 (ref[0], ref[1] - self.v_offset + self.border_spacing[1]),
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
        if self.per_second is True and (t != 0):
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
        super().__init__(*args, **kwargs)
        self.clock = timers.TimeSinceLast()
        self.clock()
        self.text_fun = lambda: f'FPS = {int(1 / self.clock())}'


# def translate_text_coordinates(text_writer:TextWriter, to_format, from_format):
#     lb = text_writer.coords
#     c =
def main():
    font_list = ('simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small', 's_simplex', 's_complex')
    from otis import camera

    colors = colortools.ColorCycle()
    capture = camera.ThreadedCameraPlayer(max_fps=30, c_dim=(1280, 720)).start()
    center = capture.f_center
    text = 'HELLO I AM OTIS'

    writer = TextWriter(coords=(0, 0),
                        ref=capture.f_center,
                        jtype='c',
                        text=text,
                        border=True,
                        underline=True,
                        one_border=True,
                        border_spacing=(.5, .25),
                        transparent_background=1.,
                        color='r',
                        anchor_point='lb'
                        )

    writer1 = TextWriter(coords=(0, -100),
                         ref=capture.f_center,
                         jtype='c',
                         text=text,
                         border=True,
                         underline=True,
                         one_border=True,
                         border_spacing=(.5, .25),
                         transparent_background=1.,
                         color='r',
                         anchor_point='c'
                         )

    circle = shapes.Circle(radius_type=10, thickness=-1, color='g')
    circles = []

    for c in ('lb', 'cb', 'rb', 'cr', 'rt', 'ct', 'lt', 'cl', 'c'):
        texter = otistext.OtisText(text=text, anchor_point=c)

        circles.append(shapes.Circle(center=center + texter.start_offset, radius=10, thickness=-1, color=colors()))

    while True:

        _, frame = capture.read()
        writer.write(frame)
        writer1.write(frame)

        for circle in circles:
            circle.write(frame)
        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break


if __name__ == '__main__':
    main()
