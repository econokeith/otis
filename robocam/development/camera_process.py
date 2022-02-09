import signal
import sys
import os
from queue import Queue
from collections import defaultdict

import numpy as np

import robocam.helpers.math
import robocam.helpers.utilities
from robocam import camera as camera
from robocam.helpers import multitools as mtools, timers as timers, utilities as utils
from robocam.helpers.utilities import MovingAverage
from robocam.overlay import textwriters as writers, assets as assets

def target(shared_data_object, args):
    #make sure process closes when ctrl+c
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)
    #start camera
    capture = camera.ThreadedCameraPlayer(dim=args.dim, max_fps=args.max_fps).start()
    #shorten shared name
    shared = shared_data_object
    #set up writers
    write_model_time = writers.TypeWriter((10, -30), ltype=1, scale=.5,
                                          ref='tl', color='u')
    write_n_faces = writers.TypeWriter((10, -60), ltype=1, scale=.5,
                                         ref='tl', color='u')
    write_latency = writers.TypeWriter((10, -90), ltype=1, scale=.5,
                                       ref='tl', color='u')
    #set up text functions
    write_model_time.text_fun = lambda mt : f'model compute time = {int(1000*mt)} ms'
    write_latency.text_fun = lambda l: f'camera fps = {int(l)}'
    write_n_faces.text_fun = lambda : f'{shared.n_faces.value} face(s) detected'
    #moving average to smooth the
    MA_N = 10
    model_time_MA = MovingAverage(MA_N)
    latency_MA = MovingAverage(MA_N)
    #OTIS!!!!
    OTIS = writers.TypeWriter((10, 400), scale=2, ltype=2,
                                 key_wait=(.02, .08),
                                 end_pause=1.5, color='g')

    tracked_names = NameTracker()
    speech_queue = Queue()

    # make the bboxes
    BBoxes = []
    bbox_coords = np.array(shared.bbox_coords)
    for i in range(args.faces):
        box = assets.BoundingBox()
        box.coords = bbox_coords[i, :] # reference a line in teh shared array
        BBoxes.append(box)

    is_updated = True

    while True:
        #get frame
        capture.read()
        shared.frame[:]=capture.frame #write to share
        #cache this stuff to avoid overwrites in the middle
        #only update
        if shared.new_overlay.value:
            old_coords = bbox_coords
            bbox_coords = np.array(shared.bbox_coords)
            names = np.array(shared.names)

            latency_MA.update(capture.latency)
            model_time_MA.update(shared.m_time.value)

            #update and hopefully stabilize
            for i in range(shared.n_faces.value):
                bbox_coords[i] = box_stabilizer(old_coords[i], bbox_coords[i], .1)
                BBoxes[i].coords = bbox_coords[i]
                BBoxes[i].name = tracked_names[names[i]]

            is_updated = True

        #write the boxes
        for i in range(shared.n_faces.value):
            BBoxes[i].write(capture.frame)
        #write other stuff

        #update otis's message queue with hellos
        if tracked_names.hello_queue.empty() is False and OTIS.stub_complete is True:
            p, line = tracked_names.hello_queue.get()
            OTIS.add_lines(line)
            shared.primary.value = p

        #
        OTIS.type_line(capture.frame)
        write_n_faces.write_fun(capture.frame)
        write_model_time.write_fun(capture.frame, model_time_MA())
        write_latency.write_fun(capture.frame, latency_MA())
        capture.show(warn=False, wait=False)

        #only reset after the data has been updated
        if shared.new_overlay.value and is_updated:
            shared.new_overlay.value = False
            is_updated = False
         #next loop won't update

        if utils.cv2waitkey() is True:
            break

    capture.stop()
    sys.exit()


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
        face_folder = os.path.join(abs_dir, '../../otismeetsguydebord/photo_assets/faces')
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


def box_stabilizer(box0, box1, threshold=.25):
    """
    checks that the distance between center points is
    less than a percentage of the
    hopefully keeps bboxes from jumping around so much.
    :param box0: (t, r, b, l)
    :param box1: (t, r, b, l)
    :param threshold: float
    :return: (t, r, b, l)
    """
    centers = []
    radii = []
    for box in [box0, box1]:
        t, r, b, l = box
        c = (r + l) / 2, (t + b) / 2
        r = np.sqrt((b-t)**2 + (l-r)**2)
        centers.append(c)
        radii.append(r)

    distance = robocam.helpers.utilities.linear_distance(*centers)
    if distance > threshold * radii[0]:
        return box1
    else:
        return box0

    # ht = (box0[2]-box0[0])*threshold
    # wt = (box0[1]-box0[3])*threshold

    # dts = [ht,wt]
    # j = 1
    # for i in range(4):
    #     j = j&0
    #     if abs(box1[i]-box0[i]) < dts[j]:
    #         return box0
    #
    # return box1








