"""
Containers for cv2.Capture:

"""
import time
from threading import Thread
import platform
from typing import Union, Optional

import cv2
import numpy as np

import otis.helpers.timers as timers
import otis.overlay.textwriters as writers
from otis.helpers import misc


class CameraPlayer:
    """
    Convenience object based on around cv2.CaptureVideo
    important attributes:
        self.frame = np.ndarray

    important methods:
        self.show()
        self.read()
    """
    recorder: cv2.VideoWriter

    def __init__(self,
                 src=0,
                 name='otis',
                 c_dim='720p', ## camera dimensions
                 f_dim=None, # frame dimensions only differs from c_dim if we're cropping the feed
                 max_fps=60,
                 record = False,
                 record_to:str = 'otis.mp4',
                 record_dim=None,
                 flip = True, # flip horizontal axis
                 output_scale:float=1,
                 record_codec = 'MP4V'
                 ):
        """
        Convenience object based on around cv2.CaptureVideo
        Args:
            src: int, optional
                usually 0, or string path to precorded file
            name: str, optional
                default 'otis'
            c_dim: str or tuple
                camera dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
            f_dim: str or tuple, optional
                frame dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
                if unset, will default to CAMERA dimensions (c_dim), otherwise will crop the frame around the
                center of the cam feed
            max_fps: int, optional
                limits the max show_fps for recording purposes. default=60
            record: bool, optional
                whether or not to record, default = False
            record_to: str
                file name to record to. default = otis.avi
            record_dim:
                record dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
                if unset, will default to FRAME dimensions (f_dim), otherwise will crop the frame around the center of the cam
                feed
            flip: bool
                flip horizontally, default = True
            output_scale: float
                increase the size of self.show()
            record_codec: str, default = 'MP4V'

        """
        # get dimensions
        c_dim = misc.dimensions_function(c_dim)
        f_dim = misc.dimensions_function(f_dim)
        record_dim = misc.dimensions_function(record_dim)

        # do necessary Linux stuff
        # I haven't tried this on window. it might need to be set to the xvid codec

        self.record_codec = record_codec

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

        # incase we need a blank frame instead of a camera feed
        self.blank_frame = np.zeros((self.f_dim[1], self.f_dim[0], 3), dtype="uint8")
        # frame stuff
        self._frame = self.blank_frame.copy()
        self._cached_frame = self._frame.copy()
        self.grabbed = True
        self.name = name
        self.stopped = False
        self._max_fps = max_fps
        self.capture.set(cv2.CAP_PROP_FPS, max_fps)
        self.flip = flip
        self.output_scale = output_scale
        # set up smart sleeper to ensure constant show_fps
        if self.max_fps is not None:
            self.fps_sleeper = timers.SmartSleeper(1 / self._max_fps)
        else:
            self.fps_sleeper = timers.SmartSleeper(0.)
        # monitoring

        self.latency = 0.001
        self.limit_fps = True
        self.exit_warning = writers.TextWriter((10, 40), color='u')
        self.exit_warning.text = 'to exit hit ctrl-c or q'
        # recording stuff
        self.recorder = None
        self._record = False
        self.record_to = record_to
        self.record_dim = self.f_dim if record_dim is None else record_dim
        self.record = record

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
            if self.recorder is None: ## TODO: check video recording outside of linux
                self.recorder = cv2.VideoWriter(self.record_to,
                                               cv2.VideoWriter_fourcc(*self.record_codec),
                                               self.max_fps,
                                               self.record_dim
                                               )
        else:
            self._record = new


    def read(self):
        """
        equivalent of cv2 VideoCapture().read()
        reads new frame from buffer
        :return:
            grabbed (bool), frame (np.ndarray)
        """
        tick = time.time()
        self.grabbed, self.frame = self.capture.read()

        if self.cropped is True:
            x0, x1, y0, y1 = self._crop_points
            self._frame = self.frame[y0:y1, x0:x1]

        if self.flip is True:
            self._frame[:, :, :] = self._frame[:, ::-1, :]

        self.latency = int(1000*(time.time()-tick))

        return self.grabbed, self.frame

    def show(self, frame=None, show_fps=False, exit_warning=False, record=None):
        """
        Equivalent to cv2.imshow('name', frame)
        Args:
            frame: np.ndarray, optional, default = None
                will use self.frame if frame is None
            show_fps: bool, default = False
                show realized fps on the screen
            exit_warning: bool, default = False
                show 'hit q to exit'
            record: bool, default = None
                overrides the self.record if not None
        Returns:

        """

        _frame = self.frame if frame is None else frame
        _record = self.record if record is None else record

        # run fps_sleeper to limit show_fps
        if self.max_fps is not None:
            self.fps_sleeper()

        # show show_fps on screen

        # show exit warning on screen
        if exit_warning is True:
            self.exit_warning.write(_frame)

        # change scale output
        if self.output_scale != 1:
            out_frame = cv2.resize(_frame, (0, 0), fx=self.output_scale, fy=self.output_scale)
        else:
            out_frame = _frame

        # record
        if _record is True and tuple(self.record_dim) != tuple(self.f_dim):
            self.recorder.write(cv2.resize(_frame, self.record_dim))
        elif _record is True:
            self.recorder.write(_frame)

        # display frame
        cv2.imshow(self.name, out_frame)


    def test(self, warn=False):
        """
        test to confirm that camera feed is working and check the show_fps
        :return:
        """
        dim_writer = writers.TextWriter((10, 120), color='g')
        dim_writer.text = f'f_dim = {self.f_dim[0]} x {self.f_dim[1]}'

        while True:
            self.read()
            dim_writer.write(self.frame)
            self.show(exit_warning=warn)
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
        Convenience object based on around cv2.CaptureVideo. Same as camera.CameraPlayer, but with an extra Thread
        to read from the camera feed.
        Args:
            src: int, optional
                usually 0, or string path to precorded file
            name: str, optional
                default 'otis'
            c_dim: str or tuple
                camera dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
            f_dim: str or tuple, optional
                frame dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
                if unset, will default to CAMERA dimensions, otherwise will crop the frame around the center of the cam
                feed
            max_fps: int, optional
                limits the max show_fps for recording purposes. default=60
            record: bool, optional
                whether or not to record, default = False
            record_to: str
                file name to record to. default = otis.avi
            record_dim:
                record dimensions. tuple of the form (w, h) or string equal to one of '480p', '720p', '1080p, '4k'
                if unset, will default to FRAME dimensions, otherwise will crop the frame around the center of the cam
                feed
            flip: bool
                flip horizontally, default = True
            output_scale: float, default = 1.
                increase the size of self.show()
            ------------------------------ThreadedCameraPlayer specific----------------------------------------------
            cache: bool, default = True
                cache the frame read, from the update Thread. If it's set to False, there may be flickering of written
                assets on the screen
            start: bool, default = True
                start the update Thread process on instantiation. If false, the update process has to be manually
                started: i.e.
                threaded_camera = ThreadedCameraPlayer(start=False).start()
                or
                threaded_camera = ThreadedCameraPlayer(start=False)
                threaded_camera.start()
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
            """
            equivalent of cv2 VideoCapture().read()
            reads new frame from buffer
            :return:
                grabbed (bool), frame (np.ndarray)
            """
            tick = time.time()
            while True:
                if self._frame is not None and self._frame.shape != ():
                    break

                if time.time()-tick > 10:
                    raise RuntimeError('External camera unable to provide video feed')

            try:
                self._cached_frame.flags.writeable = True
                if self.cropped is True:
                    x0, x1, y0, y1 = self._crop_points
                    self._cached_frame[:,:,:] = self._frame[y0:y1, x0:x1]
                else:
                    self._cached_frame[:,:,:] = self._frame

                if self.flip is not None:
                    self._cached_frame[:,:,:] = self._cached_frame[:,::-1, :]

            except RuntimeError:
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