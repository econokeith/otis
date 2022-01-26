#todo: Extend CameraPlayer to work with PiCamera Backend
#todo: add waitKey() break condition to CamperPlayer Method
import time
from threading import Thread

import cv2
import numpy as np
import imutils

import robocam.helpers.timers as timers
import robocam.overlay.textwriters as writers

class CameraPlayer:

    def __init__(self, src=0,
                 name='tracker',
                 dim=None,
                 max_fps=30,
                 **kwargs):

        self.capture = cv2.VideoCapture(src, cv2.CAP_V4L2)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if dim is not None:
            self.dim = dim
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, dim[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, dim[1])

        else:
            self.dim = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.dim = [int(d) for d in self.dim]

        self.center = int(self.dim[0]/2), int(self.dim[1]/2)
        self.frame = np.empty((*self.dim[::-1], 3))
        self.grabbed = True
        self.name = name
        self.stopped = False
        self._max_fps = max_fps
        self.sleeper = timers.SmartSleep(1 / self._max_fps)
        self.fps_writer = writers.FPSWriter((10, 60), scale=2, ltype=2, color='r')
        self.latency = 0
        self.limit_fps = True

    @property
    def max_fps(self):
        return self._max_fps

    @max_fps.setter
    def max_fps(self, new_fps):
        self._max_fps = new_fps
        self.sleeper.wait = 1/self._max_fps

    def write_fps(self):
        self.fps_writer.write(self.frame)

    def read(self, silent=False):
        """
        equivalent of cv2 VideoCapture().read()
        reads new frame from buffer
        :param silent:
        :return:
        """
        tick = time.time()
        self.grabbed, self.frame = self.capture.read()
        self.latency = int(1000*(time.time()-tick))
        if silent is False:
            return self.grabbed, self.frame

    def show(self, scale=1, width=None, wait=False, fps=False):
        if wait is True:
            self.sleeper()
        w = self.dim[0]*scale if width is None else width
        if fps is True:
            self.write_fps()

        big_frame = imutils.resize(self.frame, width=int(w))
        cv2.imshow(self.name, big_frame)

    def test(self, wait=False):
        """
        test to confirm that camera feed is working and check the fps
        :return:
        """
        dim_writer = writers.TextWriter((10, 120), scale=2, ltype=2, color='r')
        dim_writer.line = f'dim = {self.dim[0]} x {self.dim[1]}'

        while True:
            self.read()
            self.write_fps()
            dim_writer.write(self.frame)
            self.show(wait=wait)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop()

    def stop(self):
        """
        release the VideoCapture and destroy any remaining windows
        :return:
        """
        self.capture.release()
        cv2.destroyAllWindows()
        self.stopped = True


class ThreadedCameraPlayer(CameraPlayer):

    def __init__(self, *args, **kwargs):
        """
        separates the VideoCapture.read() and
        cv2.imshow functions into separate threads. Only really useful
        if you need the overlay to update more quickly than the camera is
        able to provide new frames.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.clock = timers.SmartSleep()

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):

        while True:
            if self.stopped is True:
                return

            self.grabbed, self.frame = self.capture.read()

    def read(self, silent=False):
        if silent is False:
            return self.grabbed, self.frame


if __name__=='__main__':
    cam = CameraPlayer(dim=(1920, 1080))
    cam.test()
