import time
from threading import Thread

import cv2
import numpy as np
import imutils


class CameraPlayer:

    def __init__(self, src=0,
                 name='tracker',
                 dim=None,
                 **kwargs):

        self.camera_port = src
        self.capture = cv2.VideoCapture(src, cv2.CAP_V4L2)
        self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))

        if dim is not None:
            self.dim = dim
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, dim[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, dim[1])
        else:
            self.dim = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.dim = [int(d) for d in self.dim]

        self.center = int(self.dim[0]/2), int(self.dim[1]/2)
        self.frame = np.empty((*self.dim[::-1], 3))
        self.grabbed = None
        self.name = name
        self.stopped = False
        self.font = cv2.FONT_HERSHEY_DUPLEX
        self.latency = 0
        self.latency2 = 0

    def read(self, silent=False):
        tick = time.time()
        self.grabbed, self.frame = self.capture.read()
        self.latency = int(1000*(time.time()-tick))
        if silent is False:
            return self.grabbed, self.frame

    def show(self, scale=1, width=None):
        w = self.dim[0]*scale if width is None else width

        big_frame = imutils.resize(self.frame, width=int(w))
        cv2.imshow(self.name, big_frame)

    def test(self):
        tick = 0
        while True:
            timer = cv2.getTickCount()
            self.read(True)
            fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

            h, w, _ = self.frame.shape
            cv2.putText(self.frame, f'dim = {w} x {h}', (10, 30), self.font, .75, (0, 0, 255), 1)
            cv2.putText(self.frame, f'FPS = {int(fps)}', (10, int(self.dim[1] - 90)), self.font, .75, (0, 0, 255), 1)
            latency = 1000*(time.time() - tick)
            cv2.putText(self.frame, f'LATENCY = {self.latency} ms', (10, int(self.dim[1] - 60)), self.font, .75, (0, 255, 0), 1)
            #cv2.putText(self.frame, f'LATENCY = {self.latency2}', (10, int(self.dim[1] - 30)), self.font, .75, (255,0, 0), 1)
            self.show()
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            tick = time.time()

        self.stop()

    def stop(self):
        self.capture.release()
        cv2.destroyAllWindows()
        self.stopped = True


class ThreadedCameraPlayer(CameraPlayer):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):

        while True:
            if self.stopped is True:
                return
            #timer = cv2.getTickCount()
            tick = time.time()
            self.grabbed, self.frame = self.capture.read()
            self.latency = int(1000*(time.time()-tick))
            #self.latency2 = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

    def read(self, silent=False):
        if silent is False:
            return self.grabbed, self.frame


if __name__=='__main__':
    cam = ThreadedCameraPlayer(dim=(1920, 1080))
    cam.start()
    cam.test()
