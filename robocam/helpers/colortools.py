import cv2
from itertools import cycle
from robocam.helpers import timers

class UpDownCounter:

    def __init__(self, 
                 mini=0, 
                 maxi=255, 
                 step=1, 
                 start=0, 
                 forward=True,
                 Hz = 1
                 ):

        self.mini = mini
        self.maxi = maxi
        self.i = start
        self.forward = forward
        self.step = step
        self.cycle_length = maxi - mini + 1
        self.last_timer = timers.TimeSinceLast()
        self.Hz = Hz
        self.max_timer = timers.CallHzLimiter()

    def __call__(self):

        if self.i < self.maxi and self.forward is True:
            self.i = min(self.i + self.step, self.maxi)
            if self.i >= self.maxi:
                self.forward = False

        else:
            self.i = max(self.i - self.step, self.mini)
            if self.i <= self.mini:
                self.forward = True

        return self.i

class UpDownCounterT:

    def __init__(self,
                 mini=0,
                 maxi=255,
                 start=0,
                 dir = 1,
                 cycle_t = 1,
                 max_ups = 60,
                 repeat = True
                 ):

        self.mini = mini
        self.maxi = maxi
        self.i = start
        self.dir = dir

        self.length = (maxi - mini + 1)
        self.cycle_t = cycle_t
        self.last_timer = timers.TimeSinceLast()
        self.speed =  self.length/ self.cycle_t
        self.ups_timer = timers.CallHzLimiter(1/max_ups)
        self.repeat = repeat

    def __call__(self):

        if self.ups_timer() is True:

            tp = self.last_timer()
            self.i = self.i + self.speed * tp * self.dir
            self.last_step = self.speed * tp

            if self.i > self.maxi and self.repeat is True:
                self.i = self.mini

            elif self.i > self.maxi and self.repeat is False:
                self.i = self.maxi
                self.dir *=-1

            elif self.i < self.mini and self.repeat is True:
                self.i = self.maxi

            elif self.i < self.mini and self.repeat is False:
                self.i = self.mini
                self.dir *= -1

        return int(self.i)


COLOR_HASH = {
    'r': (0, 0, 255),
    'g': (0, 255, 0),
    'u': (255, 0, 0),
    'w': (255, 255, 255),
    'b': (0, 0, 0),
    'y': (0, 255, 255),
    'c': (255, 255, 0),
    'm' : (255, 0, 255),
    'grey' : (127, 127, 127)

}

def color_function(color):
    if color in COLOR_HASH.keys():
        return COLOR_HASH[color]
    else:
        return color


# def frame_portion_to_grey(frame, darken=.25):
#     p = mtw.position
#     f = mtw.fheight
#     v = mtw.vspace
#     l = mtw.llength
#     portion = frame[p[1]-f-v:p[1]+2*f+int(3.5*v), p[0]-v:p[0]+l+2*v,:]
#     grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY)
#
#     # grey_new = np.where(grey - 30 < 0, 0, grey-30)
#     new_array = grey[:,:]*darken
#     portion[:,:, 0]=portion[:,:, 1]=portion[:,:, 2]=new_array.astype('uint8')

def frame_portion_to_grey(frame, darken=.25):
    grey = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    new_array = grey[:, :] * darken
    frame[:, :, 0] = frame[:, :, 1] = frame[:, :, 2] = new_array.astype('uint8')


# def frame_portion_to_dark(frame):
#     from robocam.camera import CameraPlayer
#     p = mtw.position
#     f = mtw.fheight
#     v = mtw.vspace
#     l = mtw.llength
#     portion = frame[p[1]-f-v:p[1]+2*f+int(3.5*v), p[0]-v:p[0]+l+v,:]
#     middle = (portion *.25)
#     portion[:, :, :] = middle.astype('uint8')

class ColorCycle:

    def __init__(self, color_iter = None):
        self.colors = COLOR_HASH.keys()
        if color_iter is None:
            self._cycler = cycle(COLOR_HASH.keys())
        else:
            self._cycler = cycle(color_iter)

    def __call__(self):
        return next(self._cycler)

