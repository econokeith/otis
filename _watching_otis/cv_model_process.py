import signal
import sys
import logging
import os
import platform

import cv2
import numpy as np

from otis.helpers import multitools as mtools
from otis.helpers import timers, cvtools
from otis.helpers import dstructures as utils

def target(shared_data_object, args):
    import mediapipe as mp

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    mp_face_detection = mp.solutions.face_detection
    face_detection = mp_face_detection.FaceDetection(model_selection=1,
                                                     min_detection_confidence=.75
                                                     )

    shared = shared_data_object
    model_timer = timers.TimeSinceLast()
    model_timer()
    while True:
        # compress and convert from

        frame = cv2.cvtColor(shared.frame, cv2.COLOR_BGR2RGB)
        results = face_detection.process(frame)

        if results.detections:
            shared.n_observed_faces.value = 1
            coords = mediapipe_box_abs(results.detections[0], frame)
            np.copyto(shared.bbox_coords[0, :], coords)

        shared.model_update_time.value = model_timer()
        shared.new_overlay.value = True # tell other process about new data

        if shared.new_keyboard_input.value is True:
            key_board_input = shared_data_object.keyboard_input.value
            if key_board_input == ord('q'):
                break

            shared_data_object.key_input_received[1] = True

    sys.exit(0)


def mediapipe_box_abs(detection, frame):
    image_height, image_width = frame.shape[:2]
    box = detection.location_data.relative_bounding_box
    xmin = int(box.xmin * image_width)
    ymin = int(box.ymin * image_height)
    h = int(box.height * image_height)
    w = int(box.width * image_width)
    return xmin, ymin, w, h