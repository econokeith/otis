from collections import defaultdict

import numpy as np

from otis import camera as camera
from otis.helpers import cvtools, colortools

class SceneManager:
    capture: camera.ThreadedCameraPlayer

    def __init__(self, shared, pargs, capture=None, names=True, file=None,**kwargs):

        self.shared = shared
        self.pargs = pargs
        self.file = file

        # if observed_names is True:
        #
        #     try:
        #         self.name_tracker = cvtools.NameTracker(pargs.path_to_faces)
        #     except:
        #         self.name_tracker = None
        self.name_tracker = cvtools.NameTracker(pargs.path_to_faces, file=self.file)

        if capture is None:
            self.capture = camera.ThreadedCameraPlayer(0,
                                                  max_fps=pargs.max_fps,
                                                  c_dim=pargs.c_dim,
                                                  flip=True,
                                                  record=pargs.record,
                                                  record_to=pargs.record_to,
                                                  output_scale=pargs.output_scale,
                                                  record_scale=pargs.record_scale,
                                                  f_dim=pargs.crop_to,
                                                  **kwargs
                                                  ).start()
        else:
            self.capture = capture
        self.scene_number = 0


