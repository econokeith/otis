import abc
import os
from collections import defaultdict
from queue import Queue

from robocam.helpers import timers as timers


def bbox_to_center(coords):
    t, r, b, l = coords
    return int((r+l)/2), int((t+b)/2)


class NameTracker:

    def __init__(self, location_of_faces):

        self.location_of_faces = location_of_faces
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
