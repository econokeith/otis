from collections import defaultdict

import numpy as np

from otis import camera
from otis.helpers import cvtools, colortools
from otis.overlay import assets


class SceneManager:
    capture: camera.ThreadedCameraPlayer

    def __init__(self, shared, pargs, capture=None, names=True, file=None):

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
                                                  dim=pargs.dim,
                                                  flip=True,
                                                  record=pargs.record,
                                                  record_to=pargs.record_to,
                                                  output_scale=pargs.output_scale,
                                                  record_scale=pargs.record_scale
                                                  ).start()
        else:
            self.capture = capture
        self.scene_number = 0


class BoundingManager:

    def __init__(self, manager, threshold=.1):

        self.manager = manager
        self.shared = manager.shared
        self.args = manager.pargs
        self.capture = self.manager.capture
        self.threshold = threshold
        self.color_cycle = colortools.ColorCycle()

        self.bbox_coords = np.array(self.shared.bbox_coords)

        self.box_fun = lambda: assets.BoundingBox(threshold=self.threshold,
                                                  color= self.color_cycle()
                                                  )

        self.bbox_hash = defaultdict(self.box_fun)

        self.is_updated = True
        self.flash_event = False

        self.frame = np.zeros((self.args.dim[1], self.args.dim[0], 3), dtype='uint8')
        self.names = []

    def loop(self, frame):

        shared = self.shared
        bbox_hash = self.bbox_hash
        tracker = self.manager.name_tracker
        # cache this stuff to avoid overwrites in the middle
        # only updateq
        if shared.new_overlay.value:

            bbox_coords = shared.bbox_coords.copy()
            n_faces = self.shared.n_faces.value
            self.names = [tracker[name] for name in shared.observed_names[:n_faces]]

            for i, name in enumerate(self.names):
                box = bbox_hash[name]
                box.name = name
                box.coords = bbox_coords[i]
                box.write(frame)
