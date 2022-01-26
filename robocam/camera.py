import time
from threading import Thread

import cv2
import numpy as np
import imutils

import robocam.helpers.decorators as decors
import robocam.helpers.timers as timers
import robocam.overlay.texttools as ttools

class CameraPlayer:

    def __init__(self, src=0,
                 name='tracker',
                 dim=None,
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
        self.max_fps = 30
        self.sleeper = timers.SmartSleep(1/self.max_fps)
        self.fps_writer = ttools.FPSWriter((10, 60), scale=2, ltype=2, color='r')

    def read(self, silent=False):
        tick = time.time()
        self.grabbed, self.frame = self.capture.read()
        self.latency = int(1000*(time.time()-tick))
        if silent is False:
            return self.grabbed, self.frame

    def show(self, scale=1, width=None, wait=None):
        if wait is not None:
            self.sleeper(wait)
        w = self.dim[0]*scale if width is None else width

        big_frame = imutils.resize(self.frame, width=int(w))
        cv2.imshow(self.name, big_frame)

    def test(self):
        dim_writer = ttools.TextWriter((10, 120), scale=2, ltype=2, color='r')
        dim_writer.line = f'dim = {self.dim[0]} x {self.dim[1]}'

        while True:
            self.read()
            self.fps_writer.write(self.frame)
            dim_writer.write(self.frame)
            self.show()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.stop()

    def stop(self):
        self.capture.release()
        cv2.destroyAllWindows()
        self.stopped = True


class ThreadedCameraPlayer(CameraPlayer):

    def __init__(self, *args, **kwargs):
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
