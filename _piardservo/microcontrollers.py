import abc
from collections import defaultdict

try:
    import gpiozero
except Exception as exc:
    print("Raspberry Pi Dependency, gpiozero, Not Found")
    raise

try:
    from gpiozero.pins.pigpio import PiGPIOFactory
except Exception as exc:
    print("Raspberry Pi Dependency, pigpio, Not Found")
    raise

import piardservo.container as cont


class MicroController(abc.ABC):
    container: cont.ServoContainer

    def __init__(self,
                 address=None,
                 container=None,
                 write_on_update=True
                 ):
        self.address = address
        self.container = container
        self.write_on_update = write_on_update
        self._open = False

    def __repr__(self):
        return self.__str__()

    def is_open(self):
        return self._open

    @abc.abstractmethod
    def connect(self):
        """
        connect to microcontroller and initialize servos
        """
        pass

    @abc.abstractmethod
    def write(self):
        """
        write servo positions to microcontroller
        """
        pass

    @abc.abstractmethod
    def close(self):
        """
        close connection to microcontroller and shutdown servos
        """
        pass


class RPiMicroController(MicroController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class ArduinoMicroController(MicroController):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class RPiWifi(RPiMicroController):
    factory: PiGPIOFactory
    _pi_servo_hash = defaultdict(lambda: [])

    @classmethod
    def close_servos_at(cls, address):
        for servo in cls._pi_servo_hash[address]:
            servo.close()
        cls._pi_servo_hash[address] = []

    def __init__(self,
                 address=None,
                 pins=(17, 22),
                 container=None,
                 write_on_update=True
                 ):

        super().__init__(address=address,
                         container=container,
                         write_on_update=write_on_update
                         )

        if isinstance(pins, int):
            n = 1
        else:
            n = len(pins)

        self.pins = pins
        self.n = n

        self.factory = None

    def __str__(self):
        return f'<RPiWifi(host={self.address}, n={self.n})>'

    def connect(self):

        self.close_servos_at(self.address)
        self.factory = PiGPIOFactory(host=self.address)

        if self.container is not None:

            min_pws = self.container.get_values('min_pulse_width')
            max_pws = self.container.get_values('max_pulse_width')
            ivs = self.container.values()
            pi_servos = self._pi_servo_hash[self.address]

            for i, pin in enumerate(self.pins):
                pi_servo = gpiozero.Servo(pin,
                                          pin_factory=self.factory,
                                          min_pulse_width=min_pws[i] / 1000000,
                                          max_pulse_width=max_pws[i] / 1000000,
                                          initial_value=ivs[i]
                                          )

                pi_servos.append(pi_servo)
                self.container[i].write_on_update = self.write_on_update

        self._open = True

    def write(self):
        _servos = self._pi_servo_hash[self.address]
        for i, servo in enumerate(self.container.servos):
            if servo._written is False:
                _servos[i].value = servo.value
                servo._written = True

    def close(self):
        self.factory.close()
        self._open = False


if __name__ == '__main__':
    pass
