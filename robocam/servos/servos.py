import abc
#in case people only need the arduino controller
from robocam.servos.servotools import degree_to_other, AnglesList

try:
    import gpiozero
except:
    print("Raspberry Pi Dependency, gpiozero, Not Found")

try:
    from gpiozero.pins.pigpio import PiGPIOFactory
except:
    print("Raspberry Pi Dependency, pigpio, Not Found")

from robocam.servos.encoders import CommaDelimitedEncoder
from robocam.servos.connection import ArduinoSerialPort

class ServoController(abc.ABC):

    def __init__(self,
                 n=1,
                 use_micro=False,
                 zero_point=90,
                 m_range=(1000, 2000),
                 a_range=(0, 180),
                 steps=1
                 ):

        self.n = n
        self.zero_point = [zero_point] * n
        self.steps = [steps] * n
        self.flip = [0] * n
        self.a_range = [a_range] * n
        self.m_range = [m_range] * n
        self._angles = AnglesList(self.zero_point, self)
        self.use_micro = use_micro

    @property
    def angles(self):
        return self._angles

    @angles.setter
    def angles(self, new_angles):
        assert isinstance(new_angles, (tuple, list))
        assert len(new_angles) == self.n
        self._angles[:] = new_angles

    def reset(self):
        self.angles = self.zero_point
        self.write()

    def move(self, moves, write=True):
        assert len(moves)==self.n
        for i, m in enumerate(moves):
            self.angles[i] += m * (-1)**self.flip[i]

        if write is True:
            self.write()

    @property
    @abc.abstractmethod
    def is_open(self):
        pass

    @abc.abstractmethod
    def write(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def connect(self, *args, **kwargs):
        pass

    @abc.abstractmethod
    def close(self):
        pass


class ArduinoServo:

    def __init__(self,
                 n=1,
                 address=3,
                 connect=False,
                 baud=9600,
                 time_out=1,
                 use_micro=False,
                 zero_point=90,
                 m_range=(1000, 2000),
                 a_range=(0, 180),
                 steps=1,
                 # encoder = False,

                 ):
        """

        Args:
            n:
            address:
            connect:
            baud:
            time_out:
            use_micro:
            zero_point:
            m_range:
            a_range:
            steps:
        """
        self.n = n
        self.zero_point = [zero_point] * n
        self.steps = [steps] * n
        self.flip = [0] * n
        self.a_range = [a_range] * n
        self.m_range = [m_range] * n
        self._angles = AnglesList(self.zero_point, self)
        self.use_micro = use_micro

        self.connection = ArduinoSerialPort(address, baud, time_out=time_out)

        if connect is True:
            self.connection.connect()

        self.encoder = CommaDelimitedEncoder()

    @property
    def is_open(self):
        return self.connection.is_open

    @property
    def angles(self):
        return self._angles

    @angles.setter
    def angles(self, new_angles):
        assert isinstance(new_angles, (tuple, list))
        assert len(new_angles) == self.n
        self._angles[:] = new_angles

    def write(self, *args, **kwargs):
        if self.use_micro is True:
            data = []
            for i, angle in enumerate(self.angles):
                data.append(degree_to_other(angle, self.m_range[i]))
            data = [int(d) for d in data]
        else:
            data = [int(angle) for angle in self.angles]

        message = self.encoder.encode_data(data)
        self.connection.write(message)

    def connect(self, *args, **kwargs):
        self.connection.connect(*args, **kwargs)

    def reset(self):
        self.angles = self.zero_point
        self.write()

    def move(self, moves, write=True):
        assert len(moves)==self.n
        for i, m in enumerate(moves): 
            self.angles[i] += m * (-1)**self.flip[i]

        if write is True: 
            self.write()

    def close(self):
        self.connection.close()


class RPiServo(ServoController):

    def __init__(self,
                 address=None,
                 pins=(17,22),
                 connect=True,
                 **kwargs):

        if isinstance(pins, int):
            n = 1
        else:
            n = len(pins)

        super().__init__(n=n, **kwargs)
        self.factory = PiGPIOFactory(host=address)
        self.servos = []
        self.pins = pins
        if connect is True:
            self.connect(pins)


    def connect(self, pins=None):
        _pins = self.pins if pins is None else pins
        for i, pin in enumerate(_pins):
            servo = gpiozero.Servo(pin,
                                   pin_factory=self.factory,
                                   min_pulse_width = self.m_range[i][0]/1000000,
                                   max_pulse_width = self.m_range[i][1]/1000000)
            self.servos.append(servo)

    @property
    def is_open(self):
        for i, servo in enumerate(self.servos):
            if servo.closed is True:
                return False

        return True

    def close(self):
        for servo in self.servos:
            servo.close()
        self.servos = []

    def write(self):
        for i, servo in enumerate(self.servos):
            servo.value = degree_to_other(self.angles[i], (-1, 1))


def main():
    import time
    Servo = RPiServo('192.168.1.28')
    print(Servo.is_open)
    for i in range(4):
        Servo.move((10*-1**i, 10*-1**i))
        time.sleep(1)

    Servo.close()


if __name__=='__main__':
    main()


