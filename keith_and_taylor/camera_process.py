import queue
import signal
import sys
import time
import cv2
import numpy as np

from otis.helpers import multitools, cvtools, coordtools, colortools, timers
from otis.overlay import scenes, imageassets, assetholders, textwriters, shapes


def target(shared, pargs):
    manager = scenes.SceneManager(shared, pargs, file=__file__)
    capture = manager.capture  # for convenience