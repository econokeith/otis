import signal
import sys
import logging
import os

import cv2
import numpy as np

import otis.helpers.cvtools
from otis.helpers import timers, cvtools, multitools, dstructures

DEBUG = False
if DEBUG:
    logging.basicConfig(filename='text_files/logs/log.log', filemode='w', level=logging.INFO)

def target(shared_data_object, args):
    # import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    known_names, known_encodings = cvtools.load_face_data(face_recognition, args.PATH_TO_FACES)
    face_locator = timers.FunctionTimer(face_recognition.face_locations)
    # this was probably excessively complicated
    # counter dict just gives the order of unique names here
    # so we can have multiple pictures of the same person
    name_dict = dstructures.CounterDict()
    for name in known_names:
        name_dict[name]

    model_timer = timers.TimeSinceLast()

    frame_copy = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')

    while True:
        # compress and convert from
        model_timer()
        frame_copy[:,:,:] = shared.frame[:,:,::-1]
        compressed_frame = otis.helpers.cvtools.resize(frame_copy, 1 / args.cf)
        observed_boxes = face_locator(compressed_frame, model=model)
        observed_boxes = np.array(observed_boxes) * args.cf
        observed_encodings = face_recognition.face_encodings(frame_copy, observed_boxes,)
        shared.n_faces.value = len(observed_boxes)

        for i in range(shared.n_faces.value):
            np.copyto(shared.bbox_coords[i,:], observed_boxes[i])
            face_distances = face_recognition.face_distance(known_encodings, observed_encodings[i])
            best_match_index = np.argmin(face_distances)
            shared.names[i] = name_dict[known_names[best_match_index]]

        if DEBUG is True:
            log = '%i'
            for distance in face_distances:
                log += (','+str(distance))
            logging.info(f'log', best_match_index)

        if otis.helpers.cvtools.cv2waitkey() is True:
            break

        shared.m_time.value = model_timer()
        shared.new_overlay.value = True # tell other process about new data

    sys.exit()
