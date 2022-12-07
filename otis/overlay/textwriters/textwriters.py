"""
Contains TextWriter and several other

"""
import types

import cv2
import numpy as np

from otis.helpers import colortools, coordtools, timers
from otis.overlay import bases, shapes
from otis.overlay.textwriters import otistext
from otis.overlay.shapes import shapefunctions
from otis.overlay.textwriters import texttools


# todo - texttxt writer perma border doesn't work without one border turned on
class TextWriter(bases.AssetWriter, bases.RectangleType, bases.TextType):
    text_fun: types.FunctionType

    def __init__(self,
                 coords=(0, 0),
                 font='duplex',
                 color='r',  # can be 'r', 'g', 'u', 'w', 'b', 'y', 'c', 'm', 'grey' or (G, B, R) color tuple
                 scale=1.,
                 ltype=1,
                 thickness=1,
                 anchor_point='lb',
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
        self.u_color = colortools.color_function(self.u_color)

        if isinstance(underline, shapes.Line) or underline is False or underline is None:
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
        self.back_color = colortools.color_function(back_color)

        if invert_background is True and border == False and background == False:
            background = True

        if transparent_background != 0.:
            self.background = shapes.TransparentBackground(coord_format='cwh',
                                                           transparency=transparent_background,
                                                           )

        elif isinstance(background, bases.RectangleType) or background == False or background == None:
            self.background = background

        else:
            self.background = shapes.Rectangle((0, 0, 0, 0),
                                               color=self.back_color,
                                               thickness=-1,
                                               ref=None,
                                               dim=None,
                                               coord_format='cwh',
                                               update_format=None,
                                               )

        ################################### border ######################################################

        self.border_spacing = border_spacing  # property
        self.b_ltype = b_ltype if b_ltype is not None else self.ltype
        self.b_thickness = b_thickness if b_thickness is not None else self.thickness
        self.b_color = b_color if b_color is not None else self.color
        self.b_color = colortools.color_function(self.b_color)

        if isinstance(border, bases.RectangleType) or border == False:
            self.border = border

        else:
            self.border = shapes.Rectangle((0, 0, 0, 0),
                                           color=self.b_color,
                                           thickness=self.b_thickness,
                                           ltype=self.b_ltype,
                                           ref=None,
                                           dim=None,
                                           coord_format='cwh',
                                           update_format=None,
                                           )

        ################ Text Set Up #################################################################

        self.perma_border = perma_border
        self.text = text  # property
        self.text_fun = lambda: ""
        self._typing_mode = 'textwriter'
        self._output = ""
        self.completed_stubs = []
        self.cursor = None

    ############################# PROPERTIES ##########################################################
    @property
    def stubs(self):
        return self.text_object.stubs

    @property
    def n_stubs(self):
        return self.text_object.n_stubs

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
    def height(self):
        return self.text_object.height + self.border_spacing[1]*2

    @property
    def width(self):
        return self.text_object.width + self.border_spacing[0]*2

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
    def _write_line_of_text(self, frame, text, coords=None, color=None, show_outline=True):
        """
        :type frame: np.array
        """
        h_space, v_space = self.border_spacing
        w, h = self.get_text_size(text)
        # write border
        l = coords[0] - h_space
        b = coords[1] + v_space
        w += 2 * h_space
        h += 2 * v_space

        cx = l + w//2
        cy = b - h//2

        if isinstance(self.background, bases.RectangleType) and show_outline is True:
            self.background.write(frame, (cx, cy, w, h), color=color)

        if isinstance(self.border, bases.RectangleType) and show_outline is True:
            self.border.write(frame, (cx, cy, w, h), color=color)

        if self.invert_background is True:
            _color = 'w'
        # underline
        if isinstance(self.underline, bases.LineType):
            self.underline.write(frame,
                                 (0, -v_space, w-2 * h_space, -v_space),
                                 color=color,
                                 ref=coords,
                                 )

        shapefunctions.write_text(frame,
                                  text,
                                  pos=coords,
                                  font=self.font,
                                  color=color,
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
            text: if text is not None, it will overwrite... this isn't what i want, but men
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

        _coords = coordtools.absolute_point(_coords, _ref, frame)
        # if fed a line of text it just writes it.
        if text is not None:
            self.text = text

        center_coords = cx, cy, w, h = coordtools.translate_box_coords((*_coords, self.width, self.height),
                                                       in_format=self.anchor_point + 'wh',
                                                       out_format='cwh',)

        if self.one_border is True:
            if isinstance(self.background, bases.RectangleType):
                self.background.write(frame, coords=center_coords, ref=None)

            if isinstance(self.border, bases.RectangleType):
                self.border.write(frame, coords=center_coords, ref=None)

        down_space = self.line_spacing + self.font_height
        start_coords = (cx, cy+self.font_height, self.text_object.width, self.text_object.height)

        start_coords = coordtools.translate_box_coords(start_coords,
                                                       in_format='cwh',
                                                       out_format='ltrb',
                                                       )

        x, y = start_coords[:2]

        for i, stub in enumerate(self.stubs):
            # this has to just keep running the ref stuff otherwise the justifications don't work
            # I think
            if self.jtype == 'c':
                j_offset = (self.text_object.width - self.get_text_size(stub)[0]) // 2
            elif self.jtype == 'r':
                j_offset = (self.text_object.width - self.get_text_size(stub)[0])
            else:
                j_offset = 0

            self._write_line_of_text(frame, stub, (x + j_offset, y + i * down_space), _color,
                                     show_outline=(not self.one_border))

    def write_fun(self, frame, *args, **kwargs):
        self.write(frame, self.text_fun(*args, **kwargs))

    def _int_or_float_times_font_size(self, value):

        if isinstance(value, float):
            return int(value * self.font_height)
        else:
            return value


if __name__ == '__main__':
    frame = np.zeros((500, 500, 3), dtype='uint8')
    text_writer = TextWriter(coords=(250, 250), text="hello, hello", border=True)
    sleeper = timers.SmartSleeper(1/30)
    new_coords = (100, 100)
    circle = shapes.Circle(center=new_coords, radius=5, thickness=-1)

    while True:

        frame[:,:,:] = 0
        circle.write(frame)
        text_writer.write(frame, text='YOOOO', coords=(100, 100))
        cv2.imshow('name', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

