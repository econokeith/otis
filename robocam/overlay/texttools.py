import robocam.helpers.timers as timers

class Cursor(timers.Blinker):

    def __init__(self, on_time=.53, char_1='_', char_0=' '):

        super().__init__(timer=[on_time, on_time])
        self.char_0 = char_0
        self.char_1 = char_1

    def __call__(self):
        if super().__call__():
            return self.char_1
        else:
            return self.char_0