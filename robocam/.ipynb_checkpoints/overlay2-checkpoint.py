import time

import cv2
import numpy as np

from .helpers import none_iter, lagged_repeat, blinker


color_hash = {
    'r': (0, 0, 255),
    'g': (0, 255, 0),
    'u': (255, 0, 0),
    'w': (255, 255, 255),
    'b': (0, 0, 0)
}
def none_iter(iterable):
    yield from iterable
    yield None


class TextWriter:

    def __init__(self,
                 pos, #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 fscale=1,  # font scale,
                 ltype=2,  # line type
                 ):

        self.font = font
        
        if isinstance(color, str):
            self.color = color_hash[color]
        else:
            self.color = color

        self.pos = pos
        self.fscale = fscale
        self.ltype = ltype
        self._text = None
        self.text_function = None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, new_text):
        self._text = new_text

    def write(self, frame, text=None, color=None):
        col = color if color is not None else self.color
        text = text if text is not None else self.text
        
        if text is not None:
            cv2.putText(frame,
                        text,
                        self.pos,
                        self.font, self.fscale, col, self.ltype)

    def write_fun(self, frame, *args, **kwargs):
        self.text = self.text_function(*args, **kwargs)
        self.write(frame)

        
class LineTyper(TextWriter):

    def __init__(self,
                 pos, #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 fscale=1,  # font scale,
                 ltype=2,
                 dt = None,
                 rand = (.1,.3),
                 end_pause=1,
                 loop=False
                 ):
        
        super().__init__(pos=pos, font=font, color=color, fscale=fscale, ltype=ltype)
        
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
            self.text_iter = none_iter(new_text)
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


#     def typeLines(self, frame, text_list, pos, color=None, dt=None, rand=(.1, .3), reset=False, dur=3, loop=False):

#         if self.lines_in_progess is False and self.list_finished is False:
#             self.iter_list = none_iter(text_list)
#             self.line_in_progress = True
#             self.current_line = next(none_iter)

#         elif self.line_in_progress is True and self.


class LoopTimer:

    def __init__(self, wait):

        self.wait = wait
        self._wait_in_seconds = self.wait / 1000
        self.tick = time.time()
        self.loop_completed = False

        
    def wait(self, wait=None):
        wait = wait / 1000 if wait is not None else self._wait_in_seconds
        if self.loop_completed is False:
            time.sleep(self._wait_in_seconds)
            self.tick = time.time()
            self.loop_completed = True
        else:
            tock = time.time()
            if tock - tick < self._wait_in_seconds:
                time.sleep(self._wait_in_seconds - tock + tick)
            self.tick = tock


class Asset:

    def __init__(self):
        pass

    def write(self, frame):
        pass


class Cursor:

    def __init__(self, size, position, blink_rate=530):
        pass


class CommandLineWriter:

    def __init__(self, message):
        pass


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

    fps_writer = TextWriter((10, 60), fscale=2, ltype=2, color=(0, 255, 0))
    fps_writer.text_function = lambda fps : f'FPS = {fps}'
    typer = LineTyper((10, 400), fscale=2, ltype=2, rand=(.02, .12))
    typer.text = MSGS[0]
    fps = 100
    j = 0
    i = 0
    forward = True
    while True:
        tick = time.time()
        frame[:, :, :] = i

        if i < 255 and forward is True:
            i += 1
            if i == 255:
                forward = False
        else:
            i -= 1
            if i == 0:
                forward = True

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