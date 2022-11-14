#todo: Extend CameraPlayer to work with PiCamera Backend
#todo: add waitKey() break condition to CamperPlayer Method
import time
from threading import Thread
import platform

import cv2
import numpy as np

import robocam.helpers.timers as timers
import robocam.overlay.textwriters as writers


class CameraPlayer:
    recorder: cv2.VideoWriter

    def __init__(self, src=0,
                 name='tracker',
                 dim=None,
                 max_fps=None,
                 record = False,
                 record_to = 'cam.avi',
                 flip = True,
                 scale = 1,
                 **kwargs):

        #do necessary Linux stuff 
        if platform.system() == 'Linux':
            self.capture = cv2.VideoCapture(src, cv2.CAP_V4L2)
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        else:
            self.capture = cv2.VideoCapture(src)

        if dim is not None:
            self.dim = dim
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, dim[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, dim[1])

        else:
            self.dim = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            self.dim = [int(d) for d in self.dim]

        self.center = int(self.dim[0]/2), int(self.dim[1]/2)
        self._frame = np.empty((*self.dim[::-1], 3))
        self._c_frame = np.array(self._frame)
        self.grabbed = True
        self.name = name
        self.stopped = False
        self._max_fps = max_fps
        self.capture.set(cv2.CAP_PROP_FPS, max_fps)

        if self.max_fps is not None:
            self.sleeper = timers.SmartSleeper(1 / self._max_fps)
        else:
            self.sleeper = None

        self.fps_writer = writers.FPSWriter((10, int(self.dim[1] - 40)))
        self.latency = 0.001
        self.limit_fps = True
        self.exit_warning = writers.TextWriter((10, 40), color='u')
        self.exit_warning.line = 'to exit hit ctrl-c or q'
        self.recorder = None
        self._record = False
        self.record = record
        self.record_to = record_to
        self.record_scale = 1
        self.flip = flip
        self.scale = scale


    @property
    def frame(self):
        return self._frame

    @frame.setter
    def frame(self, new_frame):
        self._frame = new_frame

    @property
    def max_fps(self):
        return self._max_fps

    @max_fps.setter
    def max_fps(self, new_fps):
        self._max_fps = new_fps
        self.sleeper.wait = 1/self._max_fps

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, new):
        assert isinstance(new, bool)
        if new is True:
            self._record = new
            self.recorder = cv2.VideoWriter(self.record_to,
                                           cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                           self.max_fps,
                                           self.dim * self.record_scale
                                           )
        else:
            self._record = new

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
        if self.flip is True:
            self.frame = self.frame[:, ::-1, :]

        self.latency = int(1000*(time.time()-tick))
        if silent is False:
            return self.grabbed, self.frame

    def show(self, frame=None, scale=None, width=None, wait=False, fps=False, warn=False):
        _frame = self.frame if frame is None else frame
        _scale = self.scale if scale is None else scale
        if self.max_fps is not None:
            self.sleeper()
        w = self.dim[0]*_scale if width is None else width
        if fps is True:
            self.write_fps()

        if warn is True:
            self.exit_warning.write(_frame)


        if _scale != 1:
            _frame = cv2.resize(_frame, (0, 0), fx=_scale, fy=_scale)


        cv2.imshow(self.name, _frame)

        if self.record is True:
            self.recorder.write(self.frame.astype('uint8'))

    def test(self, wait=False, warn=False):
        """
        test to confirm that camera feed is working and check the fps
        :return:
        """
        dim_writer = writers.TextWriter((10, 120), color='g')
        dim_writer.line = f'dim = {self.dim[0]} x {self.dim[1]}'

        while True:
            self.read()
            self.write_fps()
            dim_writer.write(self.frame)
            self.show(wait=wait, warn=warn)
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
        if self.record is True:
            self.recorder.release()
            print(f'video_recorded to {self.record_to}')

#TODO maybe put in a wait until next frame option
class ThreadedCameraPlayer(CameraPlayer):

    def __init__(self, *args, cache=True, **kwargs):
        """
        separates the VideoCapture.read() and
        cv2.imshow functions into separate threads.
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.clock = timers.SmartSleeper()
        self.cache = cache
        self._frame = None
        self._c_frame = None

    @property
    def frame(self):
        if self.cache is True:
            return self._c_frame
        else:
            return self._frame

    def start(self):
        Thread(target=self.update, args=()).start()
        return self

    def update(self):

        while True:
            if self.stopped is True:
                return

            tick = time.time()
            self.grabbed, self._frame = self.capture.read()
            #self.new_frame = True
            self.latency = 1//(time.time() - tick)

    def read(self, Silent=False):
            #cache the newest frame
            # if self.new_frame is True and self.cache is True:
            #     self._c_frame = np.array(self._frame)
            #     self.new_frame = False
            self._c_frame = np.array(self._frame)

            return self.grabbed, self.frame


