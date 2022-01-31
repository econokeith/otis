import signal
import sys

import os

import cv2
import numpy as np

from robocam.helpers import multitools as mtools
from robocam.helpers import timers
from robocam.helpers import utilities as utils

def target(shared_data_object, args):
    # import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    known_names, known_encodings = load_face_data(face_recognition)
    face_locator = timers.FunctionTimer(face_recognition.face_locations)

    model_timer = timers.TimeSinceLast()

    while True:
        # compress and convert from
        model_timer()
        compressed_frame = utils.resize(shared.frame, 1/args.cf)[:, :, ::-1]
        observed_boxes = face_locator(compressed_frame, model=model)
        observed_encodings = face_recognition.face_encodings(compressed_frame, observed_boxes)
        # shared.m_time.value = face_locator.time
        #write new bbox lcoations to shared array
        shared.n_faces.value = len(observed_boxes)

        for i in range(shared.n_faces.value):

            np.copyto(shared.bbox_coords[i,:], observed_boxes[i])
            shared.bbox_coords[i, :] *= args.cf
            matches = face_recognition.compare_faces(known_encodings, observed_encodings[i])

            if True in matches:
                first_match_index = matches.index(True)
                shared.names[i] = first_match_index
            else:
                known_encodings.append(observed_encodings[i])
                shared.names[i] = len(observed_encodings)

        if utils.cv2waitkey() is True:
            break

        shared.m_time.value = model_timer()

    sys.exit()

#this is like this to preserve the local import
def load_face_data(face_recognition):
    #this  might have to change
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    face_folder = os.path.join(abs_dir, 'faces')
    face_files = os.listdir(face_folder)

    names = []
    encodings = []

    for file in face_files:
        name = ""
        for char in file:
            if char.isdigit() or char in ('.', '-'):
                break
            else:
                name += char

        names.append(name.capitalize())
        image = os.path.join(face_folder, file)
        image = face_recognition.load_image_file(image)
        encoding = face_recognition.face_encodings(image)[0]
        encodings.append(encoding)

    return names, encodings