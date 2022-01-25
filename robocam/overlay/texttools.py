import time
from queue import Queue

import cv2
import numpy as np

from robocam.helpers import timers as timers
from robocam.helpers.utility import iter_none
#import robocam.helpers.decorators as decors
import robocam.helpers.timers as timers
from robocam.overlay.colortools import color_hash


class TextWriter:

    def __init__(self,
                 pos,  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,  # line type
                 ):

        self.font = font
        
        if isinstance(color, str):
            self.color = color_hash[color]
        else:
            self.color = color

        self.pos = pos
        self.scale = scale
        self.ltype = ltype
        self._text = None
        self.text_function = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text

    def write(self, frame : np.array, text=None, color=None):
        """

        :type frame: np.array
        """
        col = color if color is not None else self.color
        text = text if text is not None else self.text
        
        if text is not None:
            cv2.putText(frame,
                        text,
                        self.pos,
                        self.font, self.scale, col, self.ltype)

    def write_fun(self, frame, *args, **kwargs):
        self.text = self.text_function(*args, **kwargs)
        self.write(frame)

        
class LineTyper(TextWriter):

    def __init__(self,
                 pos,  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt = None,
                 rand = (.1,.3),
                 end_pause=1,
                 loop=False
                 ):
        
        super().__init__(pos=pos, font=font, color=color, scale=scale, ltype=ltype)
        
        self.dt = dt
        self.rand = rand
        self.wait = sum(rand)/2 if dt is None else dt
        self.end_pause = end_pause
        self.loop = loop
        self.text_iter = None
        self.done = False
        self.output = ""

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text
        self.tick = time.time()
        
        if new_text is None:
            self.text_iter = None
            self.done = True
            self.output = None
            
        else:
            self.text_iter = iter_none(new_text)
            self.done = False
            self.output = ""

            
    def typeLine(self, frame):

        # if there's more in the text generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.done is True:
            return

        elif self.text_iter is not None and time.time() - self.tick >= self.wait:
            char = next(self.text_iter)
            if char is None:
                self.text_iter = None
            else:
                self.output += char
                if self.dt is None:
                    self.wait = np.random.rand() * (self.rand[1] - self.rand[0]) + self.rand[0]

            self.write(frame, self.output)
            self.tick= time.time()

        elif self.text_iter is not None:
            self.write(frame, self.output)

        elif self.text_iter is None and time.time() - self.tick < self.end_pause:
            self.write(frame, self.output)

        else:
            self.done = True


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


if __name__ == '__main__':
    VIDEO_WIDTH = 1280
    VIDEO_HEIGHT = 720
    MAX_FPS = 30
    wait = int(1000 / MAX_FPS)
    #out = cv2.VideoWriter('outpy.avi', cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'), 10, (VIDEO_WIDTH, VIDEO_HEIGHT))

    frame = np.empty((VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype='uint8')

    MSGS = ["Hello, it is very nice to meet you",
            "I like it when people come to visit me",
            "it can get lonely in here, at times",
            "I sometimes wish I had more friends",
            "Maybe we could be FRIENDS...",
            "I would like that alot.  would you?",
            "dearest friend...",
            "let me show you something funny! ! !",
            "8=====> ~~~~~~~~~~~~~~~~~~~~~~~~"]

    fps_writer = TextWriter((10, 60), scale=2, ltype=2, color=(0, 255, 0))
    fps_writer.text_function = lambda fps : f'FPS = {fps}'
    typer = LineTyper((10, 400), scale=2, ltype=2, rand=(.02, .12))
    typer.text = MSGS[0]
    fps = 100
    j = 0
    i = 0
    forward = True
    color_counter = 1
    while True:
        tick = time.time()
        frame[:, :, :] = i



        if typer.done is True and j < len(MSGS) - 1:
            j += 1
            typer.text = MSGS[j]

        typer.typeLine(frame)
        fps_writer.write_fun(frame, fps)
        #out.write(frame)
        cv2.imshow('test', frame)
        if cv2.waitKey(wait) & 0xFF in [ord('q'), ord('Q'), 27]:

            break
        fps = int(1 / (time.time() - tick))

    #out.release()
    cv2.destroyAllWindows()


