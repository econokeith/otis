import time
from queue import Queue
import copy
import types

import cv2
import numpy as np

import otis.helpers.coordtools
import otis.helpers.maths
from otis.helpers import timers, colortools, cvtools, dstructures, coordtools, misc
from otis.overlay import bases, shapes, textwriters

# Todo: there's a bit of a bug that causes right justified to justify off the left side. Probably need to add
#       justification offsets to OtisText

class OtisText:
    """
    OtisText is a bookkeeping object that calculates stubs and anchor points for text. It's used internally
    by text writers to simplify the organization of those objects
    """

    def __init__(self,
                 text="",
                 anchor_point=None,
                 font='duplex',
                 scale=1,
                 thickness=1,
                 line_spacing=.5,
                 max_line_length=None,
                 line_length_format='pixels',
                 max_lines=None,
                 perma_border = False
                 ):

        self.font = textwriters.FONT_HASH[font]
        self.scale = scale
        self.anchor_point = anchor_point
        self.text = text
        self.perma_border = perma_border

        if self.anchor_point is not None:
            self._coord_format = self.anchor_point + 'wh'
        else:
            self._coord_format = None

        self.max_line_length = max_line_length
        self.line_length_format = line_length_format
        self.max_lines = max_lines
        self.line_spacing = line_spacing
        self.thickness = thickness

        self.stubs = textwriters.split_text_into_stubs(text,
                                                       max_line_length=self.max_line_length,
                                                       n_lines=self.max_lines,
                                                       line_length_format=self.line_length_format,
                                                       font=self.font,
                                                       scale=self.scale,
                                                       thickness=self.thickness,
                                                       )

        self.n_stubs = len(self.stubs)

        if self.line_length_format != 'pixels' or self.max_line_length is None:
            self.width = max([self.get_text_size(stub)[0] for stub in self.stubs])
        else:
            self.width = self.max_line_length


        self.font_height = self.get_text_size('T')[1]

        if max_lines is not None and perma_border is True:
            self.height = max_lines * self.font_height + (max_lines - 1) * self.line_spacing
        else:
            self.height = self.n_stubs * self.font_height + (self.n_stubs - 1) * self.line_spacing

        self.start_offset = self.get_cv2_start_from_anchor()
        self.next_line_offset = self.font_height + self.line_spacing


    def get_text_size(self, text):
        """
        Args:
            text: str
                text to the size
        Returns: tuple
                (text_width, text_height)
        """
        return cv2.getTextSize(text, self.font, self.scale, self.thickness)[0]

    def get_cv2_start_from_anchor(self):
        if self.anchor_point is None:
            return np.zeros(2, dtype=int)
        else:

            l, t, _, _ = coordtools.translate_box_coords((0, self.font_height, self.width, self.height),
                                                         in_format=self.anchor_point + 'wh',
                                                         out_format='ltrb',
                                                         )
            return np.array((l,t), dtype=int)

    def get_cv2_start_from_center(self):
        l, t, _, _ = coordtools.translate_box_coords((0, self.font_height, self.width, self.height),
                                                     in_format='cwh',
                                                     out_format='ltrb',
                                                     )
        return np.array((l, t), dtype=int)


    def export_stub_queue(self):
        stub_queue = Queue()
        for stub in self.stubs:
            stub_queue.put(stub)

        return stub_queue
