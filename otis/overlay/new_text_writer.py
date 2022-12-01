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

        self.perma_border = perma_border

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

        self.text_stubs = texttools.split_text_into_lines(new_text,
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
        return cv2.getTextSize(_text, self.font, self.scale, self.ltype)[0]

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
