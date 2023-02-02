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

IMG_CF = 3
MAX_FACE_DISTANCE = .65

DEBUG = False
if DEBUG:
    logging.basicConfig(filename='text_files/logs/log.log',
                        filemode='w',
                        level=logging.INFO
                        )


def target(shared_data_object, args):
    # import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    if platform.system() == 'Darwin':
        model = 'hog'
        args.cf = 1
    else:
        model = 'cnn'


    known_names, known_encodings = cvtools.load_face_data(face_recognition, args.PATH_TO_FACES, __file__)
    known_names.append('unknown')

    max_faces = args.faces
    n_known_faces =  len(known_names)
    face_locator = timers.FunctionTimer(face_recognition.face_locations)

    # this was probably excessively complicated
    # counter dict just gives the order of unique observed_names here
    # so we can have multiple pictures of the same person
    name_dict = utils.CounterDict()
    for name in known_names:
        x = name_dict[name]

    model_timer = timers.TimeSinceLast()
    frame_copy = np.zeros((args.crop_to[1], args.crop_to[0], 3), dtype='uint8')
    face_distances = np.zeros((n_known_faces)*(max_faces), dtype=float).reshape((max_faces, n_known_faces))
    face_distances[:, -1] = MAX_FACE_DISTANCE

    model_timer()
    while True:
        # compress and convert from
        frame_copy[:,:,:] = np.array(shared.frame)
        frame_copy = frame_copy[:,:,::-1]
        compressed_frame = cvtools.resize(frame_copy, 1 / args.cf)

        if platform.system() == 'Darwin':
            observed_boxes = face_locator(compressed_frame)
        else:
            observed_boxes = face_locator(compressed_frame, model=model)

        observed_boxes = np.array(observed_boxes) * args.cf
        observed_encodings = face_recognition.face_encodings(frame_copy, observed_boxes,)
        shared.n_observed_faces.value = len(observed_boxes)

        for i in range(shared.n_observed_faces.value):

            np.copyto(shared.bbox_coords[i,:], observed_boxes[i])
            face_distances[i, :-1] = face_recognition.face_distance(known_encodings, observed_encodings[i])
            best_match_index = np.argmin(face_distances[i])
            shared.observed_names[i] = name_dict[known_names[best_match_index]]

        if DEBUG is True:
            log = '%i'
            for distance in face_distances:
                log += (','+str(distance))

            try:
                logging.info(f'log', best_match_index)
            except:
                logging.info(f'log', None)


        shared.model_update_time.value = model_timer()
        shared.new_overlay.value = True # tell other process about new data

        if shared.new_keyboard_input.value is True:
            key_board_input = shared_data_object.keyboard_input.value
            if key_board_input == ord('q'):
                break

            shared_data_object.key_input_received[1] = True

    sys.exit()

# if __name__=='__main__':
#     import face_recognition
#     frame = face_recognition.load_image_file('/users/keithblackwell/documents/github\
#                                             /otis/image_sprinkler/faces/keith_test.jpg')
#     print(face_recognition.face_locations(frame))