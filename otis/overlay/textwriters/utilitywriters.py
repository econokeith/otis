import otis.helpers
from otis.helpers import timers
from otis.overlay.textwriters.textwriters import TextWriter
from otis.overlay import shapes

class NameTag(TextWriter):

    def __init__(self,
                 name=None,
                 v_offset=20,
                 h_offset=0,
                 attached_to=None,
                 color=None,
                 box_reference='c_spirals',  # 'c_spirals', 'l', 'radius'
                 anchor_point='cb',
                 line_to_box=False,
                 ltb_offset=0,
                 **kwargs,
                 ):

        super().__init__(anchor_point=anchor_point, **kwargs)

        self.name = name
        self.v_offset = v_offset
        self.h_offset = h_offset
        self.attached_to = attached_to
        self.color = color
        self.box_reference = box_reference
        self.ltb_offset = ltb_offset
        self.line_to_box = line_to_box
        self.jtype = box_reference

    @property
    def name(self):
        return self.text

    @name.setter
    def name(self, new_name):
        self.text = new_name

    def write(self, frame, name=None, **kwargs):
        # might wanna change this so that it just get's entered each time

        if name is not None:
            text = name
        elif self.name is not None:
            text = self.name
        elif self.attached_to.name is not None:
            text = self.attached_to.name
        else:
            return

        if self.color is not None:
            color = self.color
        else:
            color = self.attached_to.color

        x, y, w, h = self.attached_to.center_width_height()

        if self.box_reference == 'l':
            ref = (x - w // 2, y - h // 2)

        elif self.box_reference == 'radius':
            ref = (x + w // 2, y - h // 2)
        else:
            ref = (x, y - h // 2)

        super().write(frame,
                      text=text,
                      coords=(self.ltb_offset,
                              self.v_offset + self.border_spacing[1]),
                      color=color,
                      ref=ref,
                      save=False
                      )

        if self.line_to_box is True:
            shapes.draw_line(frame,
                             ref,
                             (ref[0], ref[1] - self.v_offset + self.border_spacing[1]),
                             thickness=self.u_thickness,
                             color=color
                             )


class InfoWriter(TextWriter):

    def __init__(self,
                 text_fun=lambda: "",
                 *args,
                 **kwargs
                 ):
        super().__init__(**kwargs)
        self.text_fun = text_fun

    def write(self, frame, *args, **kwargs):
        super().write(frame, text=self.text_fun(*args, **kwargs))


class TimerWriter(InfoWriter):
    timer_hash = {"first": timers.TimeSinceFirst,
                  "last": timers.TimeSinceLast,
                  "countdown": timers.CountDownTimer}

    def __init__(self,
                 title="update_limiter",
                 timer_type="last",
                 per_second=False,
                 roundw=1,
                 moving_average=10,
                 count_from=10,
                 *args,
                 **kwargs
                 ):

        super().__init__(*args, **kwargs)

        self.per_second = per_second
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
                self.moving_average = otis.helpers.maths.MovingAverage(moving_average)

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
            return self._timer.is_finished

    def timer(self):
        t = self._timer()
        if self.per_second is True and (t != 0):
            t = 1 / t

        if self.moving_average is not None:
            t = self.moving_average.update(t)

        if self.roundw == 0:
            t = int(t)
        else:
            t = round(t, self.roundw)

        return t

    def write(self, frame, text=None):

        super(InfoWriter, self).write(frame, f'{self.title} : {self.timer()}')


class FPSWriter(TextWriter):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.clock = timers.TimeSinceLast()
        self.clock()
        self.text_fun = lambda: f'FPS = {int(1 / self.clock())}'
