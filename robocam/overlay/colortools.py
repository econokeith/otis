class UpDownCounter:

    def __init__(self, mini=0, maxi=255, step=1):
        self.mini = mini
        self.maxi = maxi
        self.i = 0
        self.forward = True
        self.step = step

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
    'b': (0, 0, 0)
}

def color_function(color):
    if color in COLOR_HASH.keys():
        return COLOR_HASH[color]
    else:
        return color