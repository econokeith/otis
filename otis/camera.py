
import time
from threading import Thread
import platform

import cv2
import numpy as np

import otis.helpers.timers as timers
import otis.overlay.textwriters as writers


class CameraPlayer:
    recorder: cv2.VideoWriter

    def __init__(self,
                 src=0,
                 name='otis',
                 c_dim=(1280, 720), ## camera dimensions
                 f_dim=None, # frame dimensions only differs from c_dim if we're cropping the feed
                 max_fps=60,
                 record = False,
                 record_to = 'cam.avi',
                 flip = False, # flip horizontal axis
                 output_scale = 1,
                 record_scale = .5,  # I need to fix this
                 ):
        """

        Args:
            src:
            name:
            c_dim:
            max_fps:
            record:
            record_to:
            flip:
            output_scale:
            record_scale:
            silent_sleep:
        """

        # do necessary Linux stuff
        if platform.system() == 'Linux':
            self.capture = cv2.VideoCapture(src, cv2.CAP_V4L2)
            self.capture.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
        else:
            self.capture = cv2.VideoCapture(src)

        if c_dim is not None:
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, c_dim[0])
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, c_dim[1])
            self.c_dim = c_dim
        else:
            self.c_dim = self.capture.get(cv2.CAP_PROP_FRAME_WIDTH), self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

        self.c_dim = np.array(self.c_dim, dtype=int)
        self.c_center = np.array((self.c_dim[0] // 2, self.c_dim[1] // 2), dtype=int)

        if f_dim is None:
            self.f_dim = self.c_dim
            self.f_center = self.c_center
            self.cropped = False

        else:
            assert f_dim[0] <= self.c_dim[0] and f_dim[1] <= self.c_dim[1]
            self.f_dim = np.array(f_dim, dtype=int)
            dx1, dy1 = f_dim
            cx0, cy0 = self.c_center
            x1_min = cx0 - dx1//2
            x1_max = cx0 + dx1//2
            y1_min = cy0 - dy1//2
            y1_max = cy0 + dy1//2
            self._crop_points = (x1_min, x1_max, y1_min, y1_max)
            self.f_center = np.array((dx1//2, dy1//2), dtype=int)
            self.cropped=True

        self.blank_frame = np.zeros((self.f_dim[1], self.f_dim[0], 3), dtype="uint8")

        self._frame = self.blank_frame.copy()
        self._cached_frame = self._frame.copy()
        self.grabbed = True
        self.name = name
        self.stopped = False
        self._max_fps = max_fps
        self.capture.set(cv2.CAP_PROP_FPS, max_fps)

        # set up smart sleeper to ensure constant fps
        if self.max_fps is not None:
            self.fps_sleeper = timers.SmartSleeper(1 / self._max_fps)
        else:
            self.fps_sleeper = timers.SmartSleeper(0.)

        self.fps_writer = writers.FPSWriter((10, int(self.f_dim[1] - 40)))
        self.latency = 0.001
        self.limit_fps = True
        self.exit_warning = writers.TextWriter((10, 40), color='u')
        self.exit_warning.text = 'to exit hit ctrl-c or q'
        self.recorder = None
        self._record = False

        self.record_to = record_to
        self.record_scale = record_scale
        self.record = record
        self.flip = flip
        self.output_scale = output_scale

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
        self.fps_sleeper.wait = 1 / self._max_fps

    @property
    def record(self):
        return self._record

    @record.setter
    def record(self, new):
        assert isinstance(new, bool)
        if new is True:
            self._record = new
            if self.recorder is None:
                self.recorder = cv2.VideoWriter(self.record_to,
                                               cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                               self.max_fps,
                                               self.f_dim * self.record_scale
                                               )
        else:
            self._record = new

    def write_fps(self):
        self.fps_writer.write(self.frame)

    def read(self):
        """
        equivalent of cv2 VideoCapture().read()
        reads new frame from buffer
        :param silent:
        :return:
        """
        tick = time.time()
        self.grabbed, self.frame = self.capture.read()

        if self.cropped is not None:
            x0, x1, y0, y1 = self._crop_points
            self._frame = self.frame[y0:y1, x0:x1]

        if self.flip is True:
            self._frame[:, :, :] = self._frame[:, ::-1, :]

        self.latency = int(1000*(time.time()-tick))

        return self.grabbed, self.frame

    def show(self, frame=None, scale=None, fps=False, warn=False, record=None):

        _frame = self.frame if frame is None else frame
        _scale = self.output_scale if scale is None else scale
        _record = self.record if record is None else record

        # run fps_sleeper to limit fps
        if self.max_fps is not None:
            self.fps_sleeper()

        # show fps on screen
        if fps is True:
            self.write_fps()

        # show exit warning on screen
        if warn is True:
            self.exit_warning.write(_frame)

        # change scale output
        if _scale != 1:
            out_frame = cv2.resize(_frame, (0, 0), fx=_scale, fy=_scale)
        else:
            out_frame = _frame

        # record
        if _record is True:
            self.recorder.write(_frame.astype('uint8'))

        # display frame
        cv2.imshow(self.name, out_frame)


    def test(self, warn=False):
        """
        test to confirm that camera feed is working and check the fps
        :return:
        """
        dim_writer = writers.TextWriter((10, 120), color='g')
        dim_writer.text = f'f_dim = {self.f_dim[0]} x {self.f_dim[1]}'

        while True:
            self.read()
            self.write_fps()
            dim_writer.write(self.frame)
            self.show(warn=warn)
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


class ThreadedCameraPlayer(CameraPlayer):

    def __init__(self, *args, cache=True, start=True, **kwargs):
        """
        separates the VideoCapture.read() and
        cv2.imshow functions into separate threads. also caches the new frame in order to avoid flickering
        :param args:
        :param kwargs:
        """
        super().__init__(*args, **kwargs)
        self.clock = timers.SmartSleeper()
        self.cache = cache
        self._frame = None
        self._cached_frame = np.copy(self.blank_frame)
        self.started = False
        if start is True:
            self.start()

    @property
    def frame(self):
        if self.cache is True:
            return self._cached_frame
        else:
            return self._frame

    def start(self):
        if self.started is False:
            Thread(target=self.update, args=()).start()
            self.started = True
        return self

    def update(self):
        while True:
            if self.stopped is True:
                return

            tick = time.time()
            self.grabbed, self._frame = self.capture.read()
            #self.new_frame = True
            timer = (time.time() - tick)
            if timer == 0:
                timer = 1
            self.latency = 1//timer


    def read(self):

            tick = time.time()
            while True:
                if self._frame is not None and self._frame.shape != ():
                    break

                if time.time()-tick > 10:
                    raise RuntimeError('External camera unable to provide video feed')

            try:

                if self.cropped is True:
                    x0, x1, y0, y1 = self._crop_points
                    self._cached_frame[:,:,:] = self._frame[y0:y1, x0:x1]
                else:
                    self._cached_frame[:,:,:] = self._frame

                if self.flip is not None:
                    self._cached_frame[:,:,:] = self._cached_frame[:,::-1, :]

            except:
                frame_dim = self._frame.shape[:2][::-1]
                raise RuntimeError(f'Video feed {frame_dim} does not match specified dimensions {self.f_dim}. This '
                                   'usually occurs because your camera is unable to record at the speficied frame size. '
                                   'Check hardware limitations and camera setting or change camera.c_dim to a smaller size'
                                   )

            # if self.flip is True:
            #     self._cached_frame[:, :, :] = self._frame[:, ::-1, :]
            # else:
            #     self._cached_frame[:, :, :] = self._frame

            return self.grabbed, self.frame


if __name__=='__main__':
    capture = ThreadedCameraPlayer(c_dim=(1080, 720), f_dim=(720, 720))
    capture.read()
    print(capture.frame.shape)
    capture.test()