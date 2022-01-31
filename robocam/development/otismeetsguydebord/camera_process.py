import signal
import sys
import os

import cv2
import numpy as np

from robocam import camera as camera
from robocam.helpers import multitools as mtools, timers as timers, utilities as utils
from robocam.overlay import textwriters as writers, assets as assets

def target(shared_data_object, args):
    #make sure process closes when ctrl+c
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)
    #start camera
    capture = camera.ThreadedCameraPlayer(dim=args.dim).start()
    #shorten shared name
    shared = shared_data_object
    #set up writers
    write_model_time = writers.TypeWriter((10, int(capture.dim[1] - 120)))
    #specify write function so that shared.m_time can be updated
    write_model_time.text_fun = lambda : f'model compute time = {int(1000*shared.m_time.value)} ms'
    write_n_faces = writers.TypeWriter((10, int(capture.dim[1] - 80)))
    write_n_faces.text_fun = lambda : f'{shared.n_faces.value} face(s) detected'

    name_list = NameTracker()

    BBoxes = []
    for i in range(args.faces):
        box = assets.BoundingBox()
        box.coords = shared.bbox_coords[i, :] # reference a line in teh shared array
        BBoxes.append(box)

    while True:
        #get frame
        capture.read()
        shared.frame[:]=capture.frame #write to share
        #make bbox
        for i in range(shared.n_faces.value):
            BBoxes[i].name = name_list[shared.names[i]]
            BBoxes[i].write(capture.frame)
        #write other stuff
        write_n_faces.write_fun(capture.frame)
        #write_fps.write(capture.frame)
        write_model_time.write_fun(capture.frame)
        #render
        capture.show(warn=True, wait=False)
        if utils.cv2waitkey() is True:
            break

    capture.stop()
    sys.exit()

#this is like this to preserve the local import


class NameTracker:

    def __init__(self):

        self.known_names = []
        self.n_known = 0
        self.loads_names()
        self.indices_of_observed = []
        self.unknown_count = 0
        self.name_for_unknowns = "Person"

    def loads_names(self):
        # this  might have to change
        abs_dir = os.path.dirname(os.path.abspath(__file__))
        face_folder = os.path.join(abs_dir, 'faces')
        face_files = os.listdir(face_folder)

        for file in face_files:
            name = ""
            for char in file:
                if char.isdigit() or char in ('.', '-'):
                    break
                else:
                    name += char

            self.known_names.append(name.capitalize())

        self.n_known = len(self.known_names)

    def __getitem__(self, i):
        if i < self.n_known:
            if i not in self.indices_of_observed:
                self.indices_of_observed.append(i)
                print(f'{self.known_names[i]} seen for the first time')
            return self.known_names[i]

        else:
            name = f'Person {i - self.n_known + 1}'
            if i not in self.indices_of_observed:
                self.indices_of_observed.append(i)
                self.unknown_count += 1
                print(f'{name} seen for the first time')

            return name


