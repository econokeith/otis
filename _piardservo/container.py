import sys, tty, os, termios, signal

from piardservo.servotools import servo_param_setter
import piardservo.servo_object as servo_object
import piardservo.microcontrollers as micro

# TODO: Allow for one container to control multiple microcontrollers
class ServoContainer:

    # microcontroller: micro.MicroController

    def __init__(self,
                 n=1,
                 min_angle=-90,
                 max_angle=90,
                 initial_angle=0,
                 center_angle_offset=0,
                 angle_format='minus_to_plus',
                 flip=0,
                 servo_range=180,
                 step_size=5,
                 min_pulse_width=1000,
                 max_pulse_width=2000,
                 connect=True,
                 microcontroller=None,
                 ):

        self._n = n
        self._connect = connect
        self.angle_format = angle_format
        self.microcontroller = microcontroller
        self.microcontroller.container = self

        _min_angle = servo_param_setter(n, min_angle)
        _max_angle = servo_param_setter(n, max_angle)
        _initial_angle = servo_param_setter(n, initial_angle)
        _servo_range = servo_param_setter(n, servo_range)
        _update_center_offset = servo_param_setter(n, center_angle_offset)

        if isinstance(self.microcontroller, micro.RPiMicroController):
            min_pulse_width -= 400
            max_pulse_width += 400

        _min_pulse_width = servo_param_setter(n, min_pulse_width)
        _max_pulse_width = servo_param_setter(n, max_pulse_width)
        _step_size = servo_param_setter(n, step_size)
        _flip = servo_param_setter(n, flip)

        self.servos = []

        for i in range(n):
            servo = servo_object.ServoObject(i=i,
                                             min_angle=_min_angle[i],
                                             max_angle=_max_angle[i],
                                             initial_angle=_initial_angle[i],
                                             center_angle_offset=_update_center_offset[i],
                                             angle_format=angle_format,
                                             flip=_flip[i],
                                             servo_range=_servo_range[i],
                                             step_size=_step_size[i],
                                             min_pulse_width=_min_pulse_width[i],
                                             max_pulse_width=_max_pulse_width[i],
                                             container=self
                                             )

            self.servos.append(servo)

        try:
            self._stdin_old = termios.tcgetattr(sys.stdin)
        except:
            self._stdin_old = None

    def __getitem__(self, i):
        return self.servos[i]

    def __iter__(self):
        return iter(self.servos)

    def __len__(self):
        return self.n

    @property
    def n(self):
        return self._n

    def angles(self):
        return tuple([servo.angle for servo in self.servos])

    def values(self):
        return tuple([servo.value for servo in self.servos])

    def set_values(self, values):
        """
        get's a tuple of values from the servos
        """

        for servo, value in zip(self.servos, values):
            servo.value = value


    def pulse_widths(self):
        return tuple([servo.pulse_width for servo in self.servos])

    def get_values(self, name):
        """
        get's a tuple of values from the servos
        """
        out = []
        for servo in self.servos:
            out.append(getattr(servo, name))
        return tuple(out)

    def connect(self):
        """
        orders the microcontroller to connect
        """
        self.microcontroller.connect()
        return self

    def write(self):
        """
        orders the microcontroller to write
        """
        self.microcontroller.write()

    def close(self):
        """
        closes the microcontroller connection
        """
        self.microcontroller.close()

    def keyboard(self, move_keys=None, close_on_finish=False):
        if self._stdin_old is None:
            raise RuntimeError("Keyboard control is only available through a non-emulated terminal, which may prevent \
                                it functioning properly in certain IDE's or Jupyter Notebooks")

        if move_keys is None:
            move_keys = [
                [['a', 'left'], ['d', 'right']],
                [['s', 'down'], ['w', 'up']]
            ]
        assert len(move_keys) == self.n
        # graceful quit function for sigint and sigterm using signal module
        def restore_keyboard(sig=None, frame=None):
            #reset settings, clean-up, close factory
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._stdin_old)
            os.system('stty sane')
            print('keyboard control relinquished')
            if close_on_finish is True:
                self.close()
                print('connection to ')

        # signal catchers
        signal.signal(signal.SIGTERM, restore_keyboard)
        signal.signal(signal.SIGINT, restore_keyboard)
        # change file descriptor setting to cbreak
        # allows it to read each individual key press without return
        tty.setcbreak(sys.stdin.fileno())

        try:
            while True:
                # read/decode 3 bytes of stdin
                pushed_key = os.read(sys.stdin.fileno(), 3).decode()
                # change special keys to more easily readable names
                pushed_key = special_key_name_converter(pushed_key)

                if pushed_key == 'esc':
                    break
                else:
                    for servo, keys in zip(self.servos, move_keys):

                        if pushed_key in tuple(keys[0]):
                            servo.angle -= servo.step_size
                            break

                        if pushed_key in tuple(keys[1]):
                            servo.angle += servo.step_size
                            break
            # change keyboard settings back
        except Exception as exc:
            print("ERROR: ", exc)

        finally:
            restore_keyboard()



def special_key_name_converter(b):

    k = ord(b[-1])
    special_keys = {
        127: 'backspace',
        10: 'return',
        32: 'space',
        9: 'tab',
        27: 'esc',
        65: 'up',
        66: 'down',
        67: 'right',
        68: 'left'
    }
    return special_keys.get(k, chr(k))


if __name__=='__main__':

    from piardservo.microcontrollers import RPiWifi
    rpi = RPiWifi(address='192.168.1.28', pins=(22, 17))
    sc = ServoContainer(n=2, microcontroller=rpi).connect()
    sc.keyboard()
    sc.micro.close()


