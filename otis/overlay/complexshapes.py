import cv2
import numpy as np
import abc
from otis.helpers import shapefunctions, coordtools, misc
from otis.overlay import bases
from otis.overlay.bases import CircleType, RectangleType, LineType