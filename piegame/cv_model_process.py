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
    logging.basicConfig(filename='text_files/logs/log.log', filemode='w', level=logging.INFO)


def _target(shared, args):
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    # if utils.cv2waitkey() is True:
    #     break

    
        
def target(shared_data_object, args):
    # import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    known_names, known_encodings = load_face_data(face_recognition)
    face_locator = timers.FunctionTimer(face_recognition.face_locations)

    # this was probably excessively complicated
    # counter dict just gives the order of unique names here
    # so we can have multiple pictures of the same person
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

        if utils.cv2waitkey() is True:
            break

        shared.m_time.value = model_timer()
        shared.new_overlay.value = True # tell other process about new data

    sys.exit()

#this is like this to preserve the local import
def load_face_data(face_recognition, face_location=None):
    #this  might have to change
    abs_dir = os.path.dirname(os.path.abspath(__file__))
    face_folder = os.path.join(abs_dir, 'photo_assets/faces')
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

class NameTracker:

    def __init__(self):

        self._last_seen_timers = []
        self.known_names = []
        self.n_known = 0
        self.loads_names()
        self.indices_of_observed = []
        self.unknown_count = 0
        self.name_for_unknowns = "unknown"
        self.primary = 0
        self.hello_queue = Queue()

        #help keep from having random 1 frame bad calls triggering hellos
        #someone must show up in 5 frames in 1 second to get a hello
        _bad_hello_function =  lambda : [timers.TimeSinceFirst().start(), 0]
        self._bad_hello_dict = defaultdict(_bad_hello_function)

    def loads_names(self):
        # this  might have to change
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        face_folder = os.path.join(abs_dir, 'photo_assets/faces')
        face_files = os.listdir(face_folder)

        for file in face_files:
            name = ""
            for char in file:
                if char.isdigit() or char in ('.', '-'):
                    break
                else:
                    name += char

            #if name isn't new, add it to the list.
            if name not in self.known_names:
                self.known_names.append(name)
                self._last_seen_timers.append(timers.TimeSinceLast())
             #append name
             # set timers for each know
        self.n_known = len(self.known_names)

    def __getitem__(self, i):

        if i < self.n_known:
            # if it's a new known person
            if i not in self.indices_of_observed:
                timer, count = self._bad_hello_dict[i]
                print(timer(),count)

                ## todo: this should not be hardcoded
                if timer() <= 1.5 and count > 10:
                    self.indices_of_observed.append(i)
                    hello = f'Hello {self.known_names[i]}, welcome!'
                    self._last_seen_timers[i]() #replace this soon
                    self.hello_queue.put((i, hello))
                    #reset timer so it can be used for other things
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

                elif timer() <=1.5:
                    #count they were seen
                    self._bad_hello_dict[i][1] += 1

                else:
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

            return self.known_names[i]

        else:
            name = f'Person {i - self.n_known + 1}'
            if i not in self.indices_of_observed:
                #self.indices_of_observed.append(i)
                #self.unknown_count += 1
                hello = f'Hello {name}, do we know each other!'

            return ""


