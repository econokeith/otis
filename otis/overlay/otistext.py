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

class OtisText:
    """
    OtisText is a bookkeeping object that calculates stubs and anchor points for text. It's used internally
    by text writers to simplify the organization of those objects
    """

    def __init__(self,
                 text,
                 anchor_point = None,
                 font=None,
                 scale=None,
                 thickness=1,
                 line_spacing=.5,
                 max_line_length=None,
                 line_length_format='pixels',
                 max_lines=None,
                 ):

        self.font = font  # property
        self.scale = scale
        self.anchor_point = anchor_point

        if self.anchor_point is not None:
            self._coord_format = self.anchor_point + 'wh'
        else:
            self._coord_format = None

        self.max_line_length = max_line_length
        self.line_length_format = line_length_format
        self.max_lines = max_lines
        self.line_spacing = line_spacing
        self.thickness = thickness

        self.stubs = texttools.split_text_into_stubs(text,
                                                     max_line_length=self.max_line_length,
                                                     n_lines=self.max_lines,
                                                     line_length_format=self.line_length_format,
                                                     font=self.font,
                                                     scale=self.scale,
                                                     thickness=self.thickness,
                                                     )
        self.stub_queue = Queue()

        self.n_stubs = len(self.stubs)
        self.width = max([self.get_text_size(stub)[0] for stub in self.stubs])
        self.font_height = self.get_text_size('T')[1]
        self.height = self.n_stubs * self.font_height + (self.n_stubs - 1) * self.line_spacing


    def get_text_size(self, text):
        """
        Args:
            text: str
                text to the size
        Returns: tuple
                (text_width, text_height)
        """
        return cv2.getTextSize(text, self.font, self.scale, self.thickness)[0]

    def get_cv2_start_from_anchor(self, anchor_coords):
        if self.anchor_point is None:
            return anchor_coords
        else:
            relative_anchor_point = coordtools.absolute_point((0,0),
                                                              self.anchor_point,
                                                              dim=(self.width, self.height))

            anchor_box = tuple(anchor_coords[:2]) + (self.width, self.height)
            l, t, _, _ = coordtools.translate_box_coords(anchor_box,
                                                         in_format=self.anchor_point,
                                                         out_format='ltwh',
                                                         )

            return l, t + self.font_height
