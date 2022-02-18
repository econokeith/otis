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
    while True:

        if shared.scene.value == 2:
            manager.hello_fr_loop()
        elif shared.scene.value == 1:
            manager.otis_tells_a_joke_loop()
        elif shared.scene.value == 0:
            manager.countdown_loop()
            if manager.countdown == 0:
                shared.scene.value = 1

        if utils.cv2waitkey() is True:
            break

    manager.capture.stop()
    sys.exit()


class SceneManager:

    def __init__(self, shared, args):

        self.shared = shared
        self.args = args
        self.name = 'otis'

        self.capture = camera.ThreadedCameraPlayer(dim=args.dim, name=self.name).start()
        self.event_countdown = events.CountDown(args.dim, name=self.name)
        ### writers for info info writer section
        self.info_writers = []
        for i in range(3):
            new_writer = writers.TextWriter((10, -30*(1+i)), ltype=1, scale=.5,
                                               ref='tl', color='u')
            self.info_writers.append(new_writer)

        self.info_writers[0].text_fun = lambda mt : f'model compute time = {int(1000 * mt)} ms'
        self.info_writers[1].text_fun = lambda l : f'camera fps = {int(1/l)}'
        self.info_writers[2].text_fun = lambda n: f'{n} face(s) detected'

        MA_N = 10
        self.model_time_MA = utils.MovingAverage(MA_N)
        self.latency_MA = utils.MovingAverage(MA_N)

        #trackers/queues/etc
        self.name_tracker = NameTracker()
        self.speech_queue = Queue()
        self.joke_script = Queue()

        #OTIS!!!! and otis section stuff
        self.OTIS = writers.TypeWriter((10, 400), scale=2, ltype=2,
                                    key_wait=(.02, .08),
                                    end_pause=1.5, color='g')

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

        for line in _JOKE_SCRIPT:
            self.joke_script.put(line)

    ####################################################################################################################

        BBoxes = []
        self.bbox_coords = np.array(shared.bbox_coords)

        for i in range(args.faces):
            box = assets.BoundingBox()
            box.coords = self.bbox_coords[i, :] # reference a line in teh shared array
            BBoxes.append(box)

        self.BBoxes = BBoxes
        self.is_updated = True


    ####################################################################################################################

        self.countdown_writer = writers.TextWriter(ref='c', scale=20, ltype=-1,
                                              thickness=30, color='b',
                                              position=(0, -200), jtype='c')
        self.countdown_timer = timers.CallHzLimiter(1)
        self.countdown = 10
        self.color_counter = ctools.UpDownCounterT(start=255, maxi=255,
                                                   dir=-1, mini=0,
                                                   cycle_t=1, repeat=True)

        self.constant_frame =  np.zeros((*args.dim[::-1], 3), dtype='uint8')
        self.no_camera_sleeper = timers.SmartSleeper(1/60)


    ####################################################################################################################
    def write_info(self):
        frame = self.capture.frame
        mtma = self.model_time_MA.ma
        lat = self.latency_MA.ma
        n = self.shared.n_faces.value
        for writer, data in zip(self.info_writers, (mtma, lat, n)):
            writer.write_fun(frame, data)

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











