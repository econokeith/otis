"""
This is a very simple collision detection class
can be sped up
"""
from collections import defaultdict

import numpy as np
import cv2

from robocam.helpers import timers



# add vector form types
class AssetMover:

    #track movers for collisions
    movers = []
    _n_movers= 0

    @classmethod
    def reset_movers(cls):
        cls.movers = []
        cls._n_movers = 0

    @classmethod
    def check_collisions(cls):
        for i, m1 in enumerate(cls.movers):
            for m2 in cls.movers[i + 1:]:
                m1.collide(m2)
                remove_overlap(m1, m2)

    @classmethod
    def move_all(cls):
        for mover in cls.movers:
            mover.move()

    @classmethod
    def write_all(cls, frame):
        for mover in cls.movers:
            mover.write(frame)

    @classmethod
    def move_write_all(cls, frame):
        for mover in cls.movers:
            mover.move()
            mover.write(frame)

    @classmethod
    def remove_fin(cls):
        living_movers = []
        for mover in cls.movers:
            if mover.finished is False:
                living_movers.append(mover)
        cls.movers = living_movers

    @classmethod
    def n(cls):
        return len(cls.movers)

    def __init__(self,
                 asset,
                 mover_radius,
                 position0,  # must be in absolute coords
                 velocity0,
                 x_range,
                 y_range,
                 border_collision=False,
                 ups=30,
                 mass=None # updates per second
                 ):
        """
        wrapper class for an asset so it can move around on the screen
        :param asset:
        :param mover_radius:
        :param position0:
        :param velocity0:
        :param x_range:
        :param y_range:
        :param border_collision:
        :param ups:
        """
        self.movers.append(self)
        self._n_movers +=1
        self.id = self._n_movers

        self.collision_hash = defaultdict(lambda: False)

        self.asset = asset
        self.radius = mover_radius
        self.position = np.array(position0, dtype=float)
        self.velocity = np.array(velocity0, dtype=float)
        self.x_range = np.array([x_range[0] + self.radius,
                                 x_range[1] - self.radius]
                                )

        self.y_range = np.array([y_range[0] + self.radius,
                                 y_range[1] - self.radius]
                                )

        self.border_collision = border_collision
        self.ups = ups
        self._ups = ups
        self.timer = timers.CallHzLimiter(1 / ups)
        self.real_timer = timers.TimeSinceLast()
        self.real_timer()
        self.finished = False
        self.mass = self.radius if mass is None else mass
        self.x_collision = False
        self.y_collision = False

    def move(self):
        # don't update if it's not time


        if self.timer() is False or self.finished is True:
            return

        # find proposal position
        prop_x, prop_y = self.position + self.velocity / self.ups

        # check if proposals are in bound and then act based on self.border_collision
        x0, x1 = self.x_range
        y0, y1 = self.y_range

        if x0 < prop_x < x1:
            self.position[0] = prop_x
            self.x_collision = False

        elif self.border_collision is True:

            if self.x_collision is False:
                self.velocity[0] *= -1
                self.x_collision = True

            self.position[0] += self.velocity[0] / self.ups

        else:
            self.finished = True

        if y0 < prop_y < y1:
            self.position[1] = prop_y
            self.y_collision = False

        elif self.border_collision is True:
            if self.y_collision is False:
                self.velocity[1] *= -1
            self.position[1] += self.velocity[0] / self.ups

        else:
            self.finished = True

        # make sure nothing is snagged on a boundary
        if self.position[0] < self.x_range[0]:
            self.position[0] = self.x_range[0] + 1
        elif self.position[0] > self.x_range[1]:
            self.position[0] = self.x_range[1] - 1

        if self.position[1] < self.y_range[0]:
            self.position[1] = self.y_range[0] + 1
        elif self.position[1] > self.y_range[1]:
            self.position[1] = self.y_range[1] - 1

    def collide(self, ball, clean=False):
        v1 = self.velocity
        v2 = ball.velocity
        x1 = self.position
        x2 = ball.position
        m1 = self.mass
        m2 = ball.mass

        dx = x1 - x2
        dx_norm_2 = np.sum(dx ** 2)
        dx_norm = np.sqrt(dx_norm_2)

        #collision hash makes it so that balls don't interact until they have fully seperated
        if dx_norm <= (self.radius + ball.radius) and self.collision_hash[ball.id] is False:
            dv = v1 - v2
            dot_p1 = np.inner(dv, dx)
            dot_p2 = np.inner(-dv, -dx)
            v1_new = v1 - 2 * m2 / (m1 + m2) * (dot_p1 / dx_norm_2) * dx
            v2_new = v2 - 2 * m1 / (m1 + m2) * (dot_p2 / dx_norm_2) * (-dx)
            self.velocity = v1_new
            ball.velocity = v2_new

            self.position += v1_new / self.ups
            ball.position += v2_new / self.ups
            self.collision_hash[ball.id] = True
            if clean is True:
                remove_overlap(self, ball)

        elif dx_norm <= (self.radius + ball.radius):
            self.position += self.velocity / self.ups
            ball.position += ball.velocity / self.ups

        elif dx_norm > (self.radius + ball.radius):
            self.collision_hash[ball.id] = False


    def write(self, frame):
        if self.finished is True:
            return
        self.ups = min(1./self.real_timer(), self._ups)
        try:
            self.asset.write(frame, position=self.position.astype(int))
        except:
            self.movers.remove(self)


def remove_overlap(ball1, ball2):
    x1 = ball1.position
    x2 = ball2.position
    r1 = ball1.radius
    r2 = ball2.radius
    m1 = ball1.mass
    m2 = ball2.mass
    # find sides
    a, b = dx = x2 - x1
    # check distance
    r_sum = r1 + r2
    c = np.hypot(*dx)

    if c < r_sum:
        # separate along line connecting centers
        dc = r_sum - c + 1
        da = a * (c + dc) / c - a
        db = b * (c + dc) / c - b
        x1[0] -= da * m1 / (m1 + m2)
        x2[0] += db * m2 / (m1 + m2)
        x1[1] -= db * m1 / (m1 + m2)
        x2[1] += da * m2 / (m1 + m2)
#

def main():
    """
    This tests using radix sort with balls of the same diameter to speeed it.
    it acheives roughly a 10x performance boost
    """
    from robocam.overlay.cv2shapes import Circle
    from robocam.helpers.utilities import cv2waitkey
    from itertools import cycle
    from textwriters import TextWriter
    from robocam.overlay.colortools import COLOR_HASH

    MAX_FPS = 30
    DIMENSIONS = DX, DY = (1920, 1080)
    RECORD = True
    MAX_BALLS = 500
    RETIRE = False
    BALL_FREQUENCY = [.05, .1]
    RADIUS_BOUNDS = 4
    BALL_V_ANGLE_BOUNDS = [10, 80]
    BALL_V_MAGNI_BOUNDS = [1000, 2000]
    STARTING_LOCATION = [50, DY - 50]

    colors = list(COLOR_HASH.keys())
    colors.remove('b')
    color_cycle = cycle(colors)

    frame = np.zeros((*DIMENSIONS[::-1], 3), dtype='uint8')

    if RECORD is True:
        recorder = cv2.VideoWriter('lotta_balls.avi',
                                   cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'),
                                   MAX_FPS,
                                   DIMENSIONS)

        record_toggled = False

    fps_limiter = timers.SmartSleeper(1. / MAX_FPS)
    fps_timer = timers.TimeSinceLast(); fps_timer()

    fps_writer = TextWriter((10, 40), ltype=1)
    fps_writer.text_fun = lambda: f'fps = {int(1 / fps_timer())}'

    collision_timer = timers.TimeSinceLast()
    collision_writer = TextWriter((10, 80), ltype=1)
    collision_writer.text_fun = lambda t: f'comp time = {int(t * 1000)} ms'

    n_writer = TextWriter((10, 120), ltype=1)
    n_writer.text_fun = lambda t: f'{t} balls'

    def circle_fun():
        if isinstance(RADIUS_BOUNDS, (int, float)):
            radius = RADIUS_BOUNDS
        else:
            radius = np.random.randint(*RADIUS_BOUNDS)
        circle = Circle((0, 0),
                        radius,
                        color=next(color_cycle),
                        thickness=-1)

        m = np.random.randint(*BALL_V_MAGNI_BOUNDS)
        a = np.random.randint(*BALL_V_ANGLE_BOUNDS)
        v = np.array([np.cos(a / 180 * np.pi) * m, -np.sin(a / 180 * np.pi) * m])

        AssetMover(circle, circle.radius,
                   STARTING_LOCATION,
                   v,
                   (0, DX - 1), (0, DY - 1),
                   border_collision=True,
                   ups=MAX_FPS)

    new_circle_timer = timers.CallHzLimiter()
    bf = BALL_FREQUENCY

    remove_counter = 0
    while True:
        frame[:, :, :] = 0

        dt = np.random.rand() * (bf[1] - bf[0]) + bf[0]
        if new_circle_timer(dt) is True:
            if AssetMover.n() > MAX_BALLS and RETIRE is True:
                AssetMover.movers.pop(0)

            if AssetMover.n() < MAX_BALLS:
                circle_fun()

        collision_timer()  # start
        y_zeros = [[] for _ in range(DIMENSIONS[1])]
        x_zeros = [[] for _ in range(DIMENSIONS[0])]

        for i, mover in enumerate(AssetMover.movers):
            x, y = mover.position.astype('int')
            try:
                x_zeros[x].append(i)
                y_zeros[y].append(i)
            except:
                AssetMover.movers.remove(mover)
                remove_counter += 1
                print(f'removed ball at {x},{y} : {remove_counter} total')

        x_array = []
        for x in x_zeros:
            if x:
                for m in x:
                    x_array.append(m)
        y_array = []
        for y in x_zeros:
            for m in y:
                y_array.append(m)

        movers = AssetMover.movers
        smash_hash = defaultdict(int)

        for array in [x_array, y_array]:
            for _i in range(len(array)-1):
                j = 1
                i1 = array[_i]
                m1 = movers[i1]
                x1 = m1.position[0]
                r1 = m1.radius
                while True:
                    if j+_i >= len(array):
                        break
                    i2 = array[j+_i]
                    m2 = movers[i2]
                    x2 = m2.position[0]
                    r2 = m2.radius
                    if (x2-x1) < (r1+r2):
                        idxs = tuple(sorted([i1, i2]))
                        smash_hash[idxs]+=1
                        j+=1
                    else:
                        break

        for key in smash_hash.keys():
            if smash_hash[key] >1:
                i1, i2 = key
                m1 = movers[i1]
                m2 = movers[i2]
                m1.collide(m2, True)

        AssetMover.move_all()
        ct = collision_timer()

        AssetMover.write_all(frame)

        collision_writer.write_fun(frame, ct)
        n_writer.write_fun(frame, AssetMover.n())
        fps_writer.write_fun(frame)
        fps_limiter()

        if RECORD is True and record_toggled is True:
            recorder.write(frame)

        cv2.imshow('test', frame)
        # out.write(frame)
        cv2_wait = cv2.waitKey(1)&0xFF

        if cv2_wait == ord('r') and RECORD is True:
            record_toggled = not record_toggled

        if cv2_wait == ord('q'):
            break

    cv2.destroyAllWindows()
    if RECORD is True:
        recorder.release()

if __name__=='__main__':

    main()


