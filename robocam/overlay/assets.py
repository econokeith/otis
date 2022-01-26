import argparse

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.textwriters as writers
import robocam.overlay.writer_base as base

class BBox(base.Writer):

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,  # line type
                 ):

        self.coords = np.zeros(4, dtype='uint8')
        self.color = color
        self.thick = 2

    def write(self, frame):
        t, r, b, l = self.coords
        cv2.rectangle(frame, (l, t), (r, b), self.color, 2)

