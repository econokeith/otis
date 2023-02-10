import cv2
import numpy as np
from otis.cvtools.mediapipe.facemesh_utils import FACEMESH_TESSELATION


class FaceMesh:

    def __init__(self, points=None):

        if points is None:
            self.points = np.zeros((468, 3), dtype=int)
        elif isinstance(points, np.ndarray):
            assert self.points.shape == (468, 3)
            self.points = points
        elif isinstance(points, str):
            self.points = np.zeros((468, 3), dtype=int)

        self.connections = FACEMESH_TESSELATION