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
        #self.ips = 
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