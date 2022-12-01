"""
Example of putting BBoxes around faces
"""
import multiprocessing
import ctypes
import sys
import time

import numpy as np

import signal

import logging
import os
import platform

import face_recognition


from otis.helpers import multitools as mtools
from otis.helpers import timers, cvtools
from otis.helpers import dstructures as utils

from otis.helpers import multitools, otistools
import camera_process

parser = otistools.make_parser()
pargs = parser.parse_args()
pargs.video_center = np.array(pargs.dim) // 2
pargs.PATH_TO_FACES = '/home/keith/Projects/robocam/simple_otis_project/faces'
pargs.output_scale = 1.8
pargs.servo = True
pargs.cf = 2
pargs.max_fps = 60

IMG_CF = 3
MAX_FACE_DISTANCE = .65

if pargs.servo is True:
    try:
        import servo_process
        use_servo = True
    except:
        use_servo = False
        pargs.servo = False

def main():
    # set up shared data
    shared_data_object = multitools.SharedDataObject()
    # add shared values
    shared_data_object.add_value('model_update_time', 'd', .1)
    shared_data_object.add_value('n_observed_faces', 'i', 0)
    shared_data_object.add_value('n_boxes_active', 'i', 0)
    shared_data_object.add_value('primary_target', 'i', 0)
    shared_data_object.add_value('new_overlay', ctypes.c_bool, False)
    shared_data_object.add_value('scene', 'i', 0)
    shared_data_object.add_value('keyboard_input', 'i', 0)

    # add shared arrays
    shared_data_object.add_array('frame', ctypes.c_uint8, (pargs.dim[1], pargs.dim[0], 3)) # dims are backwards cause numpy
    shared_data_object.add_array('bbox_coords', ctypes.c_int64, (pargs.faces, 4))         # is reversed
    shared_data_object.add_array('error', ctypes.c_double, 2)
    shared_data_object.add_array('observed_names', ctypes.c_uint8, pargs.faces)
    shared_data_object.add_array('servo_target', ctypes.c_uint64, 2)
    shared_data_object.add_array('servo_position', ctypes.c_double, 2)
    # define Processes with shared data
    process_modules = [cv_model_process, camera_process]
    # if servos are true, add it to the process list
    if use_servo is True:
        process_modules.append(servo_process)

    processes = []
    # each process module should have a primary_target function called 'target'

    process = multiprocessing.Process(target=cv_model_process,
                                      args=(shared_data_object, pargs)
                                      )
    processes.append(process)

    process = multiprocessing.Process(target=camera_process.target,
                                      args=(shared_data_object, pargs)
                                      )
    processes.append(process)
    if use_servo is True:
        process = multiprocessing.Process(target=servo_process.target,
                                          args=(shared_data_object, pargs)
                                          )

        processes.append(process)


    # begin_at
    for process in processes:
        process.start()
    # join processes
    for process in processes:
        process.join()
    # exit on break key
    sys.exit()

DEBUG = False
if DEBUG:
    logging.basicConfig(filename='text_files/logs/log.log', filemode='w', level=logging.INFO)


def cv_model_process(shared_data_object, args):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    if platform.system() == 'Darwin':
        model = 'hog'
        args.cf = 1
    time.sleep(5)
    known_names, known_encodings = load_face_data(args.PATH_TO_FACES)
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
    frame_copy = np.zeros((args.dim[1], args.dim[0], 3), dtype='uint8')
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

        key_board_input = shared_data_object.keyboard_input.value
        if key_board_input == ord('q'):
            break

    sys.exit()

def load_face_data(path_to_faces):
    # this  might have to change
    if path_to_faces[0] == '.':
        path_to_faces = cvtools.abs_path_relative_to_calling_file(path_to_faces)

    face_files = os.listdir(path_to_faces)
    names = []
    encodings = []

    for file in face_files:
        name = ""
        for char in file:
            if char.isdigit() or char in ('.', '-'):
                break
            else:
                name += char

        image_path = os.path.join(path_to_faces, file)
        image = face_recognition.load_image_file(image_path)

        try:
            encoding = face_recognition.face_encodings(image)[0]
            encodings.append(encoding)
            names.append(name.capitalize())

        except:
            print("no face was found in", file)

    return names, encodings


if __name__ == '__main__':
    main()
