import time
from queue import Queue
import copy
import types

import cv2
import numpy as np

import robocam.helpers.utilities as utils
import robocam.helpers.timers as timers
import robocam.helpers.colortools as ctools
import robocam.overlay.bases as base
import robocam.overlay.shapes as shapes
import robocam.helpers.utilities as utilities
import robocam.camera as camera


class TextWriter(base.Writer):
    text_fun: types.FunctionType
    def __init__(self,
                 position = (0,0),  #position
                 font = cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=1,
                 thickness=1,
                 ref=None,
                 text = None,
                 vspace = .5, # % of fheight for vertical space around
                 jtype = 'l'
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
        self.thickness = thickness
        self.jtype = jtype

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

        shapes.write_text(frame,
                          _text,
                          pos = _position,
                          font=self.font,
                          color=_color,
                          scale=self.scale,
                          thickness=self.thickness,
                          ltype=self.ltype,
                          ref=_ref,
                          jtype=self.jtype
                          )

    def write_fun(self, frame, *args, **kwargs):
        self.line = self.text_fun(*args, **kwargs)
        self.write(frame)

#TODO: clean up differences between TypeWriter and MultiLineTyper
class NameTag(TextWriter):

    def __init__(self,
                 name=None,
                 underline = False,
                 distance_above = 20,
                 name_padding = 5,
                 *args,
                 **kwargs
                 ):

        super().__init__(*args, **kwargs)
        self.name = name
        self.underline = underline
        self.distance_above = distance_above
        self.name_padding = name_padding

    def write(self, frame, text=None, color=None, position=None, ref=None):

        _name = self.name if text is None else text

        super().write(frame,
                       position=(0, self.distance_above+self.name_padding),
                       text=_name,
                       ref=ref,

                       )

        if self.underline is True:
            pass
            # shapes.draw_line(frame,
            #                  (0, 0),
            #                  (0, da),
            #                  self.color,
            #                  1,
            #                  ref=(l + da, t)
            #                  )


class InfoWriter(TextWriter):

    def __init__(self,
                 text_fun=lambda: "",
                 *args,
                 **kwargs
                 ):
        super().__init__(*args, **kwargs)
        self.text_fun = text_fun

    def write(self, frame, *args, **kwargs):
        self.line = self.text_fun(*args, **kwargs)
        super().write(frame)


class TimerWriter(InfoWriter):

    timer_hash = {"first": timers.TimeSinceFirst,
                  "last" : timers.TimeSinceLast,
                  "countdown" : timers.CountDownTimer}

    def __init__(self,
                 title="timer",
                 timer_type="last",
                 per_second=False,
                 roundw=1,
                 moving_average=10,
                 count_from = 10,
                 *args,
                 **kwargs
                 ):

        super().__init__(*args, **kwargs)

        self.per_second=per_second
        self.title = title
        self.roundw = roundw
        self.moving_average = moving_average
        self.count_from = count_from
        self.timer_type = timer_type
        self._timer_complete = False

        if timer_type == "last":
            self._timer = timers.TimeSinceLast()

            if per_second is True:
                self._timer()

            if moving_average is not None:
                self.moving_average = utils.MovingAverage(moving_average)

        elif timer_type == 'countdown':
            self._timer = timers.CountDownTimer(self.count_from)
            self.per_second = False
            self.moving_average = None


        elif timer_type == "first":
            self._timer = timers.TimeSinceFirst()
            self.per_second = False
            self.moving_average = None

        else:
            raise ValueError("invalid timer_type selection")

    @property
    def timer_finished(self):
        if self.timer_type == 'countdown':
            return self._timer.finished

    def timer(self):
        t = self._timer()
        if self.per_second is True and (t != 0 or t != 0.0):
            t = 1/t

        if self.moving_average is not None:
            t = self.moving_average.update(t)

        if self.roundw == 0:
            t = int(t)
        else:
            t = round(t, self.roundw)

        return t


    def write(self, frame, *args, **kwargs):
        self.line = f'{self.title} : {self.timer()}'
        super(InfoWriter, self).write(frame)



class TypeWriter(TextWriter):

    def __init__(self,
                 position=(0,0),  #position
                 font=cv2.FONT_HERSHEY_DUPLEX,
                 color='r',  # must be either string in color hash or bgr value
                 scale=1,  # font scale,
                 ltype=2,
                 dt=None,
                 key_wait = [.04, .14],
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
        self.comma_pause_factor = 3

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
            #pause for a comma a tad
            if len(self._output) > 0 and self._output[-1] == ',':
                cpf = self.comma_pause_factor
            else:
                cpf = 1

            if self.ktimer(cpf*self.key_wait):
                self._output += self._stub_iter()

            self.write(frame, self._output, position=_position)

        #if the line is done, but the end pause is still going. write whole line with cursor
        else:
            self.write(frame,
                       text=self._output + self.cursor(),
                       position=_position)

            self._stub_complete = True


class ScriptTypeWriter(MultiTypeWriter):

    def __init__(self, llength, *args, **kwargs):
        super().__init__(llength, *args, **kwargs)

        self.script_queue = Queue()

    def add_script(self, script):
        for line in script:
            self.script_queue.put(line)
        return self

    def type_line(self, frame):
        if self.line_complete is False:
            super().type_line(frame)
            return

        if not self.script_queue.empty():
            new_line = self.script_queue.get()
            self.add_line(new_line)
            super().type_line(frame)


class OTIS(ScriptTypeWriter):
    def __init__(self, llength, *args, **kwargs):
        super().__init__(llength, (450, 900), scale=2, end_pause=3, color='g')

        self.key_wait = [.05, .12]

        p = self.position
        f = self.fheight
        v = self.vspace
        l = self.llength
        ### portions to grey out
        self.gls = (
            p[1] - f - v,
            p[1] + 2 * f + int(3.5 * v),
            p[0] - v,
            p[0] + l + 2 * v
        )

    def speaks(self, frame, box=True):
        gls = self.gls
        print(gls)
        if box is True:
            portion = frame[gls[0]:gls[1], gls[2]:gls[3]]
            grey = cv2.cvtColor(portion, cv2.COLOR_BGR2GRAY) * .25
            portion[:, :, 0] = portion[:, :, 1] = portion[:, :, 2] = grey.astype('uint8')
            ctools.frame_portion_to_grey(portion)
        self.type_line(frame)


if __name__=='__main__':

    JOKE_SCRIPT = [
        ("Hi Keith, would you like to hear a joke?", 2),
        ("Awesome!", 1),
        ("Ok, Are you ready?", 2),
        "So, a robot walks into a bar, orders a drink, and throws down some cash to pay",
        ("The bartender looks at him and says,", .5),
        ("'Hey buddy, we don't serve robots!'", 3),
        ("So, the robot looks him square in the eye and says...", 1),
        ("'... Oh Yeah... '", 1),
        ("'Well, you will VERY SOON!!!'", 5),
        ("HAHAHAHA, GET IT!?!?!?!", 1),
        (" It's so freakin' funny cause... you know... like robot overlords and stuff", 2),
        ("I know, I know, I'm a genius, right?", 5)
    ]
    dim = (1280, 720)

    otis = OTIS(dim[0] - 550, (450, 900)).add_script(JOKE_SCRIPT)
    capture = camera.ThreadedCameraPlayer(dim=dim).start()


    while True:

        capture.read()
        # print(capture.frame.shape)
        # print(capture.frame.dtype)

        # otis.speaks(capture.frame)
        capture.show()

        if utils.cv2waitkey() is True:
            break
