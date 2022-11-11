import numpy as np
from robocam.helpers import utilities as utils


def box_stabilizer(box0, box1, threshold=.25):
    """
    checks that the distance between center points is
    less than a percentage of the
    hopefully keeps bboxes from jumping around so much.
    :param box0: (t, r, b, l)
    :param box1: (t, r, b, l)
    :param threshold: float
    :return: (t, r, b, l)
    """
    centers = []
    radii = []
    for box in [box0, box1]:
        t, r, b, l = box
        c = (r + l) / 2, (t + b) / 2
        r = np.sqrt((b - t) ** 2 + (l - r) ** 2)
        centers.append(c)
        radii.append(r)

    distance = utils.linear_distance(*centers)
    if distance > threshold * radii[0]:
        return box1
    else:
        return box0


class BBoxStabilizer:

    @staticmethod
    def compare_boxes(box0, box1, threshold=.25):
        """
        checks that the distance between center points is
        less than a percentage of the
        hopefully keeps bboxes from jumping around so much.
        :param box0: (t, r, b, l)
        :param box1: (t, r, b, l)
        :param threshold: float
        :return: (t, r, b, l)
        """
        centers = []
        radii = []
        for box in [box0, box1]:
            t, r, b, l = box
            c = (r + l) / 2, (t + b) / 2
            r = np.sqrt((b - t) ** 2 + (l - r) ** 2)
            centers.append(c)
            radii.append(r)

        distance = utils.linear_distance(*centers)
        if distance > threshold * radii[0]:
            return box1
        else:
            return box0

    def __init__(self, N, threshold=.25):
        self.N = N
        self.threshold = threshold
        self.last = np.zeros(4*N).reshape(N*4)


    def update_boxes(self, boxes, target_count=None):
        ll = boxes.shape[0] if target_count is None else target_count
        for i in range(ll):
            self.last[i] = self.compare_boxes(self.last[i],
                                              boxes[i],
                                              threshold=self.threshold
                                              )

        return self.last