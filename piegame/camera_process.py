import signal
import sys
import os
import time
from queue import Queue
from collections import defaultdict, deque

import cv2
import numpy as np


from robocam import camera as camera
from robocam.helpers import multitools as mtools, timers as timers, utilities as utils, colortools as ctools
from robocam.overlay import screenevents as events, textwriters as writers, assets as assets


def target(shared, args):
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    manager = SceneManager(shared, args)
    time.sleep(3)
    manager.capture.stop()

    while True:
        manager.countdown_loop()
        if manager.countdown

    while True:

        if utils.cv2waitkey() is True:
            break


    sys.exit()


class SceneManager:

    def __init__(self, shared, args):

        self.shared = shared
        self.args = args
        self.name = 'otis'

        self.capture = camera.ThreadedCameraPlayer(dim=args.dim, name=self.name).start()
        self.event_countdown = events.CountDown(args.dim, name=self.name)
        ### writers for info info writer section

        #trackers/queues/etc
        self.name_tracker = NameTracker()
        self.speech_queue = Queue()
        self.joke_script = Queue()

        #OTIS!!!! and otis section stuff


        otis = writers.MultiTypeWriter(args.dim[0] - 550, (450, 900), scale=2, end_pause=3, color='g')
        otis.end_pause = 3
        otis.key_wait = [.05, .12]

        self.otis = otis

        p = otis.position
        f = otis.fheight
        v = otis.vspace
        l = otis.llength
        ### portions to grey out
        self.gls = (
            p[1] - f - v,
            p[1] + 2 * f + int(3.5 * v),
            p[0] - v,
            p[0] + l + 2 * v
        )



    ####################################################################################################################

        BBoxes = []
        self.bbox_coords = np.array(shared.bbox_coords)

        for i in range(args.faces):
            box = assets.BoundingBox()
            box.coords = self.bbox_coords[i, :] # reference a line in teh shared array
            BBoxes.append(box)

        self.BBoxes = BBoxes
        self.is_updated = True





    def hello_fr_loop(self):
        capture = self.capture
        shared = self.shared
        BBoxes = self.BBoxes
        OTIS = self.OTIS

        #get frame
        capture.read()
        shared.frame[:]=capture.frame #write to share
        #cache this stuff to avoid overwrites in the middle
        #only update
        if shared.new_overlay.value:
            old_coords = self.bbox_coords
            bbox_coords = np.array(shared.bbox_coords)
            names = np.array(shared.names)

            self.latency_MA.update(capture.latency)
            self.model_time_MA.update(shared.m_time.value)
            #update and hopefully stabilize
            for i in range(shared.n_faces.value):
                self.bbox_coords[i] = box_stabilizer(old_coords[i], bbox_coords[i], .1)
                BBoxes[i].coords = self.bbox_coords[i]
                BBoxes[i].name = self.name_tracker[names[i]]

            self.is_updated = True

        #write the boxes
        for i in range(shared.n_faces.value):
            BBoxes[i].write(capture.frame)
        #write other stuff

        #update otis's message queue with hellos
        if self.name_tracker.hello_queue.empty() is False and OTIS.line_complete is True:
            p, line = self.name_tracker.hello_queue.get()
            OTIS.add_lines(line)
            shared.primary.value = p

        ###
        OTIS.type_line(capture.frame)
        self.write_info() 
        capture.show(warn=False, wait=False)
        #only reset after the data has been updated
        if shared.new_overlay.value and self.is_updated:
            shared.new_overlay.value = False
            self.is_updated = False
         #next loop won't update

    def otis_speaks(self, box=True):
        gls = self.gls
        frame = self.capture.frame
        if box is True:
            portion = frame[gls[0]:gls[1], gls[2]:gls[3]]
            grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY) * .25
            portion[:, :, 0] = portion[:, :, 1] = portion[:, :, 2] = grey.astype('uint8')
            ctools.frame_portion_to_grey(portion)
        self.otis.type_line(frame)


    def otis_tells_a_joke_loop(self):
        script = self.joke_script
        self.capture.read()

        mtw = self.otis
        self.otis_speaks()

        if mtw.line_complete is True and script.empty() is False:
            mtw.add_line(script.get())

        self.capture.show()

    def countdown_loop(self):

        frame = self.constant_frame
        if self.countdown >= 1:
            frame[:, :, :] = self.color_counter()

            self.countdown_writer.write(frame, text=str(self.countdown))
            if self.countdown_timer() is True:
                self.countdown -= 1

        else:
            frame[:, :, :] = 0

        self.no_camera_sleeper()
        cv2.imshow(self.capture.name, frame)


_JOKE_SCRIPT = [
           ("Hi Keith, would you like to hear a joke?", 2),
           ("Awesome!", 1),
           ("Ok, Are you ready?", 2),
           "So, a robot walks into a bar, orders a drink, and throws down some cash to pay",
           ("The bartender looks at him and says,", .5),
           ("'Hey buddy, we don't serve robots!'", 3),
           ("So, the robot looks him square in the eye and says...", 1),
           ("'... Oh Yeah... '", 1),
           ("'Well, you will VERY SOON!!!'", 5),
           ("HAHAHAHA, GET IT!?!?!?!", 1),
           (" It's so freakin' funny cause... you know... like robot overlords and stuff", 2),
           ("I know, I know, I'm a genius, right?", 5)
           ]





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

    distance = utils.linear_distance(*centers)
    if distance > threshold * radii[0]:
        return box1
    else:
        return box0











