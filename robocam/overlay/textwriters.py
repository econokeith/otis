import time
from queue import Queue
import copy

import cv2
import numpy as np

import robocam.helpers.utilities as utils
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.bases as base
import robocam.overlay.cv2shapes as shapes


class TextWriter(base.Writer):

    def __init__(self,
                 position = (0,0),  #position
                 font = cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=-1,
                 thickness=1,
                 ref=None,
                 text = None,
                 vspace = .5 # % of fheight for vertical space around
                 ):

        self.font = font
        self.color = ctools.color_function(color)
        self.ref = ref
        self.position = position
        self.scale = scale
        self.ltype = ltype
        self.line = text
        self.text_fun = None
        self.fheight = self.get_text_size("T")[0][1]
        self.vspace = int(self.fheight * vspace)

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        self._line = new_text

    # @property
    # def position(self):
    #     return self._position
    #
    # @position.setter
    # def position(self, new_position):
    #     self._position = uti.abs_point(new_position, self.ref, self.dim)

    def get_text_size(self, text=None):
        _text = self.line if text is None else text
        return cv2.getTextSize(_text, self.font, self.scale, self.ltype)

    def add_fun(self, fun):
        self.text_fun = fun
        return self

    def write(self, frame, text=None, color=None, position=None, ref=None):
        """
        :type frame: np.array
        """
        _color = color if color is not None else self.color
        _text = text if text is not None else self.line
        _position = position if position is not None else self.position
        _ref = ref if ref is not None else self.ref

        shapes.write_text(frame, _text, _position, self.font, _color, self.scale, self.ltype, _ref)

    def write_fun(self, frame, *args, **kwargs):
        self.line = self.text_fun(*args, **kwargs)
        self.write(frame)

        
class TypeWriter(TextWriter):

    def __init__(self,
                 position=(0,0),  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt=None,
                 key_wait = [.02, .12],
                 end_pause=1,
                 loop=False,
                 ref = None,
                 text = None,
                 **kwargs
                 ):
        
        super().__init__(position=position, text=None, font=font, color=color, scale=scale, ltype=ltype, ref=ref, **kwargs)
        
        self.dt = dt
        self._key_wait = key_wait
        self.end_pause = end_pause
        self.end_timer = timers.SinceFirstBool(end_pause)
        self.loop = loop
        self.line_iter = utils.BoundIterator([0])
        self.line_complete = True
        self.line = text
        self._output = ""
        self.cursor = Cursor()
        self.script = Queue()
        self.ktimer = timers.CallHzLimiter(self.key_wait)

    @property
    def line(self):
        return self._line

    @line.setter
    def line(self, new_text):
        # updates text_generator when text is updated
        self._line = new_text
        self.tick = time.time()
        
        if new_text is None:
            self.line_iter = None
            self.line_complete = True
            self._output = ""
            
        else:
            self.line_iter = utils.BoundIterator(new_text)
            self.line_complete = False
            self._output = ""

    @property
    def key_wait(self):
        if isinstance(self._key_wait, (float, int)):
            return self._key_wait
        else:
            return np.random.rand() * (self._key_wait[1] - self._key_wait[0]) + self._key_wait[0]

    @key_wait.setter
    def key_wait(self, new_wait):
        self._key_wait = new_wait

    @property
    def is_done(self):
        return self.line_complete and self.script.empty()

    def add_lines(self, new_lines):
        """
        adds lines to the queue if lines is either a string or
        an iterable object full of strings
        :param new_lines:
        :return:
        """
        if not isinstance(new_lines, str):
            for new_line in new_lines:
                self.add_lines(new_line)

        else:
            self.line = self.script.put(new_lines)

        return self

    def type_line(self, frame, position=None, ref=None):
        if position is not None:
            self.position = utils.abs_point(position, ref, frame.shape)
        # if there's more in the text generator, it will continue to type new letters
        # then will show the full message for length of time self.end_pause
        # then finally stop shows
        if self.line_complete is True and self.script.empty() is True:
            return

        elif self.line_complete is True and self.script.empty() is False:
            self.line = self.script.get()
        # update if there is more to teh line and t > wait
        elif self.line_iter.is_empty is False:

            if self.ktimer(self.key_wait):
                self._output += self.line_iter()

            self.write(frame, self._output)

        #if the line is done, but the end pause is still going. write whole line with cursor
        elif self.line_iter.is_empty and self.end_timer() is False:

            self.write(frame, self._output + self.cursor())

        #empty line generator and t > pause sets the line to done
        else:

            self.line_complete = True
            print(self.line_complete)
            self.end_timer.reset()


class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = timers.TimeSinceLast()
        self.clock()
        self.text_fun =  lambda : f'FPS = {int(1/self.clock())}'

class Cursor(timers.Blinker):

    def __init__(self, cycle=.53, char_1='_', char_0=' '):
        """
        returns char_1 if on and char_0 if off
        :param cycle: if float, [on_time, off_time] = [cycle, cycle], else on_time, off_time = cycle
        :param char_1:
        :param char_0:
        """
        super().__init__(cycle=cycle)
        self.char_0 = char_0
        self.char_1 = char_1

    def __call__(self):
        if super().__call__():
            return self.char_1
        else:
            return self.char_0


class LineOfText:

    def __init__(self,
                 text=None,
                 font=None,
                 color=None,
                 scale=None,
                 ltype=None,
                 end_pause=None):
        """
        I think some kind of container object will be important eventually
        :param text:
        :param font:
        :param color:
        :param scale:
        :param ltype:
        :param end_pause:
        """

        self.font = font
        self.color = color
        self.scale= scale
        self.ltype = ltype
        self.end_pause = end_pause
        self.complete = True
        self.length = 0
        self.text = text

    def copy(self):
        return copy.copy(self)


class MultiTypeWriter(TypeWriter):

    def __init__(self, llength, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.llength = llength
        self._used_stubs = []
        self._stub_queue = Queue()
        self._stub = ""
        self._stub_iter = utils.BoundIterator(self._stub)
        self._stub_complete = True

    def next_stub(self):
        self._used_stubs.append(self._stub)
        self._stub = self._stub_queue.get()
        self._stub_iter = utils.BoundIterator(self._stub)
        self._stub_complete = False
        self._output = ""

    def add_line(self, text, pause=None):
        """
        break up a long line into multiples that fit within self.llength
        :param text:
        :return:
        """
        #allow input to be a tuple so we can change the pacing of the pauses
        if isinstance(text, (tuple, list)):
            self.add_line(*text)
            return

        #end pause will change for the current line but revert if it isn't updated
        self.end_timer.wait = self.end_pause if pause is None else pause


        ts = self.get_text_size(text)[0][0]
        stubs = []

        while ts > self.llength:

            split_pos = int(self.llength / ts * len(text))
            split_proposal = text[:split_pos + 1]
            #break at last space in the shortened line
            for i in range(split_pos+1):
                if split_proposal[-1-i] == ' ':
                    break

            stubs.append(split_proposal[:split_pos-i])
            text = text[split_pos - i:].strip(' ')
            ts = self.get_text_size(text)[0][0]

        stubs.append(text)

        #set first stub
        self._stub = stubs[0]
        self._stub_iter = utils.BoundIterator(self._stub)

        #set stub que
        for stub in stubs[1:]:
            self._stub_queue.put(stub)

        #do some resets
        self._used_stubs = []
        self.line_complete = False
        self.end_timer.reset()
        self._stub_complete = False
        self._output = ''

    def type_line(self, frame):
        v_move = self.fheight + self.vspace
        n_fin = len(self._used_stubs)
        [p0, p1] = self.position

        #do nothing if the line is complete
        if self.line_complete is True:
            return

        if self._stub_complete is False:
            #print finished lines as static
            for i in range(n_fin):
                self.write(frame, self._used_stubs[i], position=(p0, p1 + i * v_move))
            #then type out current line
            self._type_stub(frame, position=(p0, p1 + n_fin * v_move))
            return

        #refill and keep going
        if self._stub_complete is True and self._stub_queue.empty() is False:
            self.next_stub()

        else:#same as above but the first check of the tiemr will start it.
            if self.end_timer() is False:
                for i in range(n_fin):
                    self.write(frame, self._used_stubs[i], position=(p0, p1 + i * v_move))
                self._type_stub(frame, position=(p0, p1 + (n_fin) * v_move))
            else:
                self.line_complete = True

    def _type_stub(self, frame, position=None, ref=None):
        """
        single line stochastic typer just to clean things up.
        :param frame:
        :param position:
        :param ref:
        :return:
        """
        if position is None:
            _position = self.position
        else:
            _position = utils.abs_point(position, ref, frame.shape)

        if self._stub_iter.is_empty is False:

            if self.ktimer(self.key_wait):
                self._output += self._stub_iter()

            self.write(frame, self._output, position=_position)

        #if the line is done, but the end pause is still going. write whole line with cursor
        else:
            self.write(frame, self._output + self.cursor(), position=_position)
            self._stub_complete = True


if __name__=='__main__':
    DIM = (1920, 1080)
    #frame = np.zeros((720, 1080, 3), 'uint8')
    sleeper = timers.SmartSleeper(1/60)
    _script = [("Hey, wanna hear a joke?", 2),
               ("Awesome!", .5),
                "So, a robot walks into a bar, orders a drink, and drops a bill on the bar",
              "The bartender says, 'Hey, we don't serve robots in here'",
              ("And the robots replies...", 2),
               "'Oh Yeah!, well you will VERY SOON!!!'",
               "HAHAHAHA, GET IT!?!?!?! It's so freakin' funny cause, you know, like robot overlords and stuff",
               "I know, I know, I'm a genius, right?"
               ]

    script = Queue()
    for line in _script:
        script.put(line)

    mtw = MultiTypeWriter(DIM[0]-550, (450, 900), scale=2, end_pause=3, color='g')
    mtw.end_pause = 1
    mtw.key_wait = [.02, .08]
    capture = CameraPlayer(0, dim=DIM)




    def frame_portion_to_grey(frame):
        p = mtw.position
        f = mtw.fheight
        v = mtw.vspace
        l = mtw.llength
        portion = frame[p[1]-f-v:p[1]+2*f+int(3.5*v), p[0]-v:p[0]+l+2*v,:]
        grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY)

        # grey_new = np.where(grey - 30 < 0, 0, grey-30)
        new_array = grey[:,:]*.25
        portion[:,:, 0]=portion[:,:, 1]=portion[:,:, 2]=new_array.astype('uint8')


    def frame_portion_to_dark(frame):
        from robocam.camera import CameraPlayer
        p = mtw.position
        f = mtw.fheight
        v = mtw.vspace
        l = mtw.llength
        portion = frame[p[1]-f-v:p[1]+2*f+int(3.5*v), p[0]-v:p[0]+l+v,:]
        middle = (portion *.25)
        portion[:, :, :] = middle.astype('uint8')


    while True:
        capture.read()
        #frame[:,:,:] = 0
        tick = time.time()
        frame_portion_to_grey(capture.frame)
        #print(round(1000*(time.time()-tick), 2))

        if mtw.line_complete is True and script.empty() is False:
            mtw.add_line(script.get())

        mtw.type_line(capture.frame)
        shapes.write_bordered_text(capture.frame, "TEST TEST TEST TEST", (0,0), ref="c", jtype='c')
        capture.show()

        if utils.cv2waitkey():
            break










