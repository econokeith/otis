import os
import inspect
from collections import defaultdict
from queue import Queue

import cv2
import numpy as np

from otis.helpers import timers, maths

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
    if threshold == 0:
        return box1

    centers = []
    radii = []
    for box in [box0, box1]:
        t, r, b, l = box
        c = (r + l) / 2, (t + b) / 2
        r = np.sqrt((b - t) ** 2 + (l - r) ** 2)
        centers.append(c)
        radii.append(r)

    distance = maths.linear_distance(*centers)
    if distance > threshold * radii[0]:
        return box1
    else:
        return box0


class BBoxStabilizer:

    @staticmethod
    def compare_boxes(box0, box1, threshold=.25):
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
            r = np.sqrt((b - t) ** 2 + (l - r) ** 2)
            centers.append(c)
            radii.append(r)

        distance = maths.linear_distance(*centers)
        if distance > threshold * radii[0]:
            return box1
        else:
            return box0

    def __init__(self, N, threshold=.25):
        self.N = N
        self.threshold = threshold
        self.last = np.zeros(4*N).reshape(N*4)

    def update_boxes(self, boxes, target_count=None):

        ll = boxes.shape[0] if target_count is None else target_count
        for i in range(ll):
            self.last[i] = self.compare_boxes(self.last[i],
                                              boxes[i],
                                              threshold=self.threshold
                                              )

        return self.last

def get_current_dir(file):
    return os.path.abspath(os.path.dirname(file))




def abs_path_relative_to_calling_file(relative_path,  file=None, layers_out=2):
    """
    convenience function to avoid os.path type boilerplate in loading data functions

    includes workaround to work when running debuggers
    Args:
        relative_path: relative path to data from the files where the function is called NOT WRITTEN

    Returns:
        abs_path
    """

    if file is None:
        python_files = list_python_files(layers_out)
        stack = inspect.stack()[::-1]

        for frame in stack:
            file_name = frame.filename

            if file_name in python_files:
                break

        for frame in stack:
            del frame
    else:
        file_name = file

    abs_dir =  os.path.dirname(file_name)


    return os.path.abspath(os.path.join(abs_dir, relative_path))

# def abs_path_relative_to_calling_file(relative_path):
#     bottom_of_stack = inspect.stack()[-1].filename
#     abs_directory = os.path.dirname(bottom_of_stack)
#     return os.path.abspath(os.path.join(abs_directory, relative_path))


def test_fun(file=lambda:__file__):
    return file()

def list_python_files(layers_out=2):
    """
    returns a list of python files in package relative the location of cvtool.py
    this is just so abs_path_relative_to_calling_file works when pycharm debugger is turned on
    """

    path_to_here = os.path.dirname(__file__)
    path_to_parent = path_to_here

    if layers_out > 0:
        path_to_parent += '/..'*layers_out

    python_file_list = []

    file_queue = Queue()
    for item in os.listdir(path_to_parent):

        file_queue.put((path_to_parent, item))
    # search file tree starting at otis to list all python files
    while True:

        path_to, item = file_queue.get()
        abs_path_to = os.path.join(path_to, item)

        if item[-3:] == '.py' and item[0] != "_":
            python_file_list.append(abs_path_to)

        elif item[0] == "_" or item.find('.') != -1:
            pass

        else:
            new_items = os.listdir(abs_path_to)

            for new_item in new_items:
                file_queue.put((abs_path_to, new_item))

        if file_queue.empty():
            break

    return [os.path.abspath(file) for file in python_file_list]


class NameTracker:

    def __init__(self, path_to_faces, file=None):

        if path_to_faces[0] == '.':
            self.path_to_faces = abs_path_relative_to_calling_file(path_to_faces, file=file)
        else:
            self.path_to_faces = path_to_faces


        self._last_seen_timers = []
        self.known_names = []
        self.n_known = 0
        self.loads_names()
        self.indices_of_observed = []
        self.unknown_count = 0
        self.name_for_unknowns = "unknown"
        self.primary = 0
        self.hello_queue = Queue()
        # help keep from having random 1 frame bad calls triggering hellos
        # someone must show up in 5 frames in 1 second to get a hello
        _bad_hello_function = lambda: [timers.TimeSinceFirst().start(), 0]
        self._bad_hello_dict = defaultdict(_bad_hello_function)

    def loads_names(self):
        # this  might have to change
        face_files = os.listdir(self.path_to_faces)

        for file in face_files:
            name = ""
            for char in file:
                if char.isdigit() or char in ('.', '-'):
                    break
                else:
                    name += char
            # if name isn't new, add it to the list.
            if name not in self.known_names:
                self.known_names.append(name)
                self._last_seen_timers.append(timers.TimeSinceLast())
            # append name
            # set timers for each know
        self.n_known = len(self.known_names)

    def __getitem__(self, i):

        if i < self.n_known:
            # if it's a new known person
            if i not in self.indices_of_observed:
                timer, count = self._bad_hello_dict[i]

                ## todo: undo hardcoding
                if timer() <= 1.5 and count > 10:
                    self.indices_of_observed.append(i)
                    hello = f'Hello {self.known_names[i]}, welcome!'
                    self._last_seen_timers[i]()  # replace this soon
                    self.hello_queue.put((i, hello))
                    # reset update_limiter so it can be used for other things
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

                elif timer() <= 1.5:
                    # count they were seen
                    self._bad_hello_dict[i][1] += 1

                else:
                    self._bad_hello_dict[i][0].reset()
                    self._bad_hello_dict[i][1] = 1

            return self.known_names[i]

        else:
            name = f'Person {i - self.n_known + 1}'
            if i not in self.indices_of_observed:
                # self.indices_of_observed.append(i)
                # self.unknown_count += 1
                hello = f'Hello {name}, do we know each other!'

            return ""


def load_face_data(face_recognition, path_to_faces, file=None):
    #this  might have to change
    if path_to_faces[0] == '.':

        path_to_faces = abs_path_relative_to_calling_file(path_to_faces, file=file)

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


# class BoxManager:
#
#     def __init__(self,
#                  name_tracker,
#                  box_type=assets.BoundingBox,
#                  color_cycler = None,
#                  **kwargs
#                  ):
#
#         assert issubclass(box_type, assets.BoundingBox)
#
#         self.box_hash = dict()
#         self.name_tracker = name_tracker
#         self.box_type = box_type
#         self.color_cycler = color_cycler
#
#         self.new_box_fun = lambda new_name : box_type(name=new_name,
#                                                       color=next(self.color_cycler)
#                                                       **kwargs,)
#
#     def _update_box(self, name):
#
#         try:
#             box = self.box_hash[name]
#
#         except:
#             box = self.new_box_fun(name)
def cv2waitkey(n=1):
    """
    will return True on keyboard mash of q, Q or esc
    else return False
    :param n: millisecond wait.
    :return: Bool
    """
    if cv2.waitKey(n) & 0xFF in [ord('q'), ord('Q'), 27]:
        return True
    else:
        return False

def resize(frame, scale=.5):
    return cv2.resize(frame, (0, 0), fx=scale, fy=scale)

if __name__ == '__main__':
    import os
    from queue import Queue
    path_to_here = os.path.dirname(__file__)
    print(path_to_here)
    path_to_parent = path_to_here +  '/..'

    python_file_list = []
    file_queue = Queue()
    for item in os.listdir(path_to_parent):
        print
        file_queue.put((path_to_parent, item))

    while True:
        path_to, item = file_queue.get()
        abs_path_to = os.path.join(path_to, item)

        if item[-3:] == '.py' and item[0] != "_":
            python_file_list.append(abs_path_to)

        elif item[0] == "_" or item.find('.') != -1:
            pass

        else:
            new_items = os.listdir(abs_path_to)

            for new_item in new_items:
                file_queue.put((abs_path_to, new_item))

        if file_queue.empty():
            break

    python_file_list = [os.path.abspath(file) for file in python_file_list]
    print(python_file_list)




