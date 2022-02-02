import signal
import sys
import logging
import os

import cv2
import numpy as np

from robocam.helpers import multitools as mtools
from robocam.helpers import timers
from robocam.helpers import utilities as utils

DEBUG = False
if DEBUG:
    logging.basicConfig(filename='log.log', filemode='w', level=logging.INFO)

def target(shared_data_object, args):
    # import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    known_names, known_encodings = load_face_data(face_recognition)
    face_locator = timers.FunctionTimer(face_recognition.face_locations)

    #this was probably excessively complicated
    #counter dict just gives the order of unique names here
    name_dict = utils.CounterDict()
    for name in known_names:
        name_dict[name]

    model_timer = timers.TimeSinceLast()

    frame_copy = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')

    while True:
        # compress and convert from
        model_timer()
        frame_copy[:,:,:] = np.array(shared.frame)
        frame_copy = frame_copy[:,:,::-1]
        compressed_frame = utils.resize(frame_copy, 1/args.cf)
        observed_boxes = face_locator(compressed_frame, model=model)

        observed_boxes = np.array(observed_boxes) * args.cf

        observed_encodings = face_recognition.face_encodings(frame_copy, observed_boxes)
        shared.n_faces.value = len(observed_boxes)

        for i in range(shared.n_faces.value):

            np.copyto(shared.bbox_coords[i,:], observed_boxes[i])
            face_distances = face_recognition.face_distance(known_encodings, observed_encodings[i])
            # print(known_names)
            # print(face_distances)
            best_match_index = np.argmin(face_distances)
            shared.names[i] = name_dict[known_names[best_match_index]]
            # if matches[best_match_index]:
            #     shared.names[i] = best_match_index
            #     print(known_names[best_match_index])
            # else:
            #     #known_encodings.append(observed_encodings[i])
            #     shared.names[i] = len(known_names)
            #     print('unkown')

        # if DEBUG is True:
        #     log = '%i'
        #     for distance in face_distances:
        #         log += (','+str(distance))
        #     logging.info(f'log', best_match_index)
        #     #logging.info('%i,%f,%f,%f', best_match_index, *fd)

        if utils.cv2waitkey() is True:
            break

        shared.m_time.value = model_timer()
        shared.new_overlay.value = True # tell other process about new data

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


        image_path = os.path.join(face_folder, file)
        image = face_recognition.load_image_file(image_path)
        try:
            encoding = face_recognition.face_encodings(image)[0]
            encodings.append(encoding)
            names.append(name.capitalize())
        except:
            print("no face was found in", file)

    return names, encodings

