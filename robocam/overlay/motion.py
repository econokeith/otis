import numpy as np
import cv2

from robocam.helpers import timers



# add vector form types
class AssetMover:

    def __init__(self,
                 asset,
                 mover_radius,
                 position0,  # must be in absolute coords
                 velocity0,
                 x_range,
                 y_range,
                 border_collision=False,
                 ups=30  # updates per second
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

        self.asset = asset
        self.radius = mover_radius
        self.position = np.array(position0)
        self.velocity = np.array(velocity0)
        self.x_range = np.array([x_range[0] + self.radius,
                                 x_range[1] - self.radius]
                                )

        self.y_range = np.array([y_range[0] + self.radius,
                                 y_range[1] - self.radius]
                                )

        self.border_collision = border_collision
        self.ups = ups
        self.timer = timers.CallHzLimiter(1 / ups)
        self.finished = False

        self.mass = self.radius
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

    def collide(self, ball):
        v1 = self.velocity
        v2 = ball.velocity
        x1 = self.position
        x2 = ball.position
        m1 = self.mass
        m2 = ball.mass

        dx = x1 - x2
        dx_norm_2 = np.sum(dx ** 2)
        dx_norm = np.sqrt(dx_norm_2)

        if dx_norm < (self.radius + ball.radius):
            dv = v1 - v2
            dot_p1 = np.inner(dv, dx)
            dot_p2 = np.inner(-dv, -dx)
            v1_new = v1 - 2 * m2 / (m1 + m2) * (dot_p1 / dx_norm_2) * dx
            v2_new = v2 - 2 * m1 / (m1 + m2) * (dot_p2 / dx_norm_2) * (-dx)
            self.velocity = v1_new
            ball.velocity = v2_new
            ball.move()
            self.move()

    def write(self, frame):
        if self.finished is True:
            return
        self.asset.write(frame, position=self.position.astype(int))


def ball_collision(ball1, ball2):
    v1 = ball1.velocity
    v2 = ball2.velocity
    x1 = ball1.position
    x2 = ball2.position
    m1 = ball1.mass
    m2 = ball2.mass

    dv = v1 - v2
    dx = x1 - x2
    dx_norm_2 = np.sum(dx ** 2)

    dot_p1 = np.inner(dv, dx)
    dot_p2 = np.inner(-dv, -dx)
    v1_new = v1 - 2 * m2 / (m1 + m2) * (dot_p1 / dx_norm_2) * dx
    v2_new = v2 - 2 * m1 / (m1 + m2) * (dot_p2 / dx_norm_2) * (-dx)

    return v1_new, b


def post_collision_velocities(v1, v2, x1, x2, m1=1, m2=1):
    dv = v1 - v2
    dx = x1 - x2
    dx_norm_2 = np.sum(dx ** 2)

    dot_p1 = np.inner(dv, dx)
    dot_p2 = np.inner(-dv, -dx)
    v1_new = v1 - 2 * m2 / (m1 + m2) * (dot_p1 / dx_norm_2) * dx
    v2_new = v2 - 2 * m1 / (m1 + m2) * (dot_p2 / dx_norm_2) * (-dx)
    return v1_new, v2_new


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
        # seperate along line connecting centers
        dc = r_sum - c + 1
        da = a * (c + dc) / c - a - 1
        db = b * (c + dc) / c - b - 1
        x1[0] -= da * m1 / (m1 + m2)
        x2[0] += db * m2 / (m1 + m2)
        x1[1] -= db * m1 / (m1 + m2)
        x2[1] += da * m2 / (m1 + m2)


class CollisionManager:

    def __init__(self, balls):
        self.balls = balls

    def detection_collisions(self):
        for i, b1 in enumerate(self.balls):

            for b2 in self.balls[i + 1:]:

                r1 = b1.radius
                r2 = b2.radius
                x1 = b1.position
                x2 = b2.position
                dx = x1 - x2
                dx_norm = np.sqrt(np.sum(dx ** 2))

                if dx_norm <= (r1 + r2):
                    v1 = b1.velocity
                    v2 = b2.velocity
                    m1 = b1.mass
                    m2 = b2.mass
                    remove_overlap(b1, b2)
                    v1, v2 = post_collision_velocities(v1, v2,
                                                       b1.position, b2.position,
                                                       m1, m2)
                    b1.velocity = v1
                    b2.velocity = v2


if __name__=='__main__':
    from robocam.overlay.cv2shapes import Circle
    from robocam.helpers.timers import CallHzLimiter
    from robocam.helpers.utilities import cv2waitkey
    from itertools import cycle
    from textwriters import FPSWriter

    color_cycle = cycle(['r', 'g', 'u', 'w'])
    DIMENSIONS = DX, DY = (1920, 1080)
    frame = np.zeros((*DIMENSIONS[::-1], 3), dtype='uint8')
    circle = Circle((0, 0), 50)
    circle2 = Circle((200, 200), 50, color='g')

    fps_limit = timers.SmartSleeper(1 / 60)
    fps_writer = FPSWriter()

    Circles = []
    for _ in range(10):
        circle = Circle((0, 0), 100, color=next(color_cycle))
        mover = AssetMover(circle, circle.radius,
                           np.random.randint(200, 600, 2),
                           np.random.randint(-500, 500, 2),
                           (0, DX - 1), (0, DY - 1),
                           border_collision=True,
                           ups=60)

        Circles.append(mover)

    # collision_manager = CollisionManager(Circles)
    for i, circle1 in enumerate(Circles):
        for circle2 in Circles[i + 1:]:
            remove_overlap(circle1, circle2)

    # remove_overlap(circle1, circle2)

    while True:
        frame[:, :, :] = 0
        for i, circle1 in enumerate(Circles):
            for circle2 in Circles[i + 1:]:
                remove_overlap(circle1, circle2)
        # for i, circle1 in enumerate(Circles):
        #     for circle2 in Circles[i + 1:]:
        #         remove_overlap(circle1, circle2)
        # collision_manager.detection_collisions()
        for i, circle1 in enumerate(Circles):
            circle1.move()
            for circle2 in Circles[i + 1:]:
                circle1.collide(circle2)

                #remove_overlap(circle1, circle2)
                # circle2.move()
        for circle in Circles:
            circle.move()
            circle.write(frame)


        # for circle in Circles:q
        #     circle1.move()
        #     circle.write(frame)
        fps_limit()
        fps_writer.write_fun(frame)
        cv2.imshow('test', frame)

        if cv2waitkey(1):
            break

    cv2.destroyAllWindows()