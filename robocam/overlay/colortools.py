class UpDownCounter:

    def __init__(self, mini=0, maxi=255, step=1):
        self.mini = mini
        self.maxi = maxi
        self.i = 0
        self.forward = True
        self.step = 1

    def get_next(self):

        if self.i < self.maxi and self.forward is True:
            self.i = min(self.i + self.step, self.maxi)
            if self.i == 255:
                self.forward = False

        else:
            self.i = max(self.i - self.step, self.mini)
            if self.i == self.mini:
                self.forward = True

        return self.i


color_hash = {
    'r': (0, 0, 255),
    'g': (0, 255, 0),
    'u': (255, 0, 0),
    'w': (255, 255, 255),
    'b': (0, 0, 0)
}