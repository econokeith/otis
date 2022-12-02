"""
This is a very simple collisions detection class
can be sped up
"""
from collections import defaultdict
import os
import types
import time
import copy

import numpy as np
import cv2

from otis.helpers import timers
from otis.helpers.cvtools import cv2waitkey
from otis.overlay import imageassets as imga
import otis.camera as camera

# add vector form types
class AssetMover:

    # track movers for collisions
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
    def remove_finished(cls):
        living_movers = []
        for mover in cls.movers:
            if mover.is_finished is False:
                living_movers.append(mover)
        cls.movers = living_movers

    @classmethod
    def n(cls):
        return len(cls.movers)

    def __init__(self,
                 asset,
                 mover_radius,  #will be scaled with scale
                 coord0,  # must be in absolute coords
                 velocity0,
                 x_range,
                 y_range,
                 border_collision=True,
                 ups=30,
                 mass=None,  # updates per second
                 ):
        """
        wrapper class for an asset so it can move around on the screen
        :param asset:
        :param mover_radius:
        :param coord0:
        :param velocity0:
        :param x_range:
        :param y_range:
        :param border_collision:
        :param ups:
        """
        self.movers.append(self)
        self._n_movers +=1
        self.id = self._n_movers
        self.scale = 1
        self.collision_hash = defaultdict(lambda: False)

        self.asset = asset
        self.radius = mover_radius
        self._coords = np.array([50, 50, 50, 50])
        self.coords = np.array(coord0, dtype=float)
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
        self.timer = timers.CallFrequencyLimiter(1 / ups)
        self.real_timer = timers.TimeSinceLast()
        self.real_timer()
        self.finished = False
        self.mass = self.radius if mass is None else mass
        self.x_collision = False
        self.y_collision = False

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = new_coords
        t, r, b, l = self.coords
        self.coords = int((r + l) / 2), int((t + b) / 2)

    @property
    def center(self):
        return self.coords

    @center.setter
    def center(self, new_center):
        self.coords = new_center

    def move(self):
        # don't update if it's not time
        if self.timer() is False or self.finished is True:
            return

        # find proposal coords
        prop_x, prop_y = self.coords + self.velocity / self.ups

        # check if proposals are in bound and then act based on self.border_collisions
        x0, x1 = self.x_range
        y0, y1 = self.y_range

        if x0 < prop_x < x1:
            self.coords[0] = prop_x
            self.x_collision = False

        elif self.border_collision is True:

            if self.x_collision is False:
                self.velocity[0] *= -1
                self.x_collision = True

            self.coords[0] += self.velocity[0] / self.ups

        else:
            self.finished = True

        if y0 < prop_y < y1:
            self.coords[1] = prop_y
            self.y_collision = False

        elif self.border_collision is True:
            if self.y_collision is False:
                self.velocity[1] *= -1
            self.coords[1] += self.velocity[0] / self.ups

        else:
            self.finished = True

        # make sure nothing is snagged on a boundary
        if self.coords[0] < self.x_range[0]:
            self.coords[0] = self.x_range[0] + 1
        elif self.coords[0] > self.x_range[1]:
            self.coords[0] = self.x_range[1] - 1

        if self.coords[1] < self.y_range[0]:
            self.coords[1] = self.y_range[0] + 1
        elif self.coords[1] > self.y_range[1]:
            self.coords[1] = self.y_range[1] - 1

    def collide(self, ball, clean=False):
        v1 = self.velocity
        v2 = ball.velocity
        x1 = self.coords
        x2 = ball.center
        m1 = self.mass
        m2 = ball.mass

        dx = x1 - x2
        dx_norm_2 = np.sum(dx ** 2)
        dx_norm = np.sqrt(dx_norm_2)

        #collisions hash makes it so that balls don't interact until they have fully seperated
        if dx_norm <= (self.radius + ball.radius) and self.collision_hash[ball.id] is False:
            dv = v1 - v2
            dot_p1 = np.inner(dv, dx)
            dot_p2 = np.inner(-dv, -dx)
            v1_new = v1 - 2 * m2 / (m1 + m2) * (dot_p1 / dx_norm_2) * dx
            v2_new = v2 - 2 * m1 / (m1 + m2) * (dot_p2 / dx_norm_2) * (-dx)
            self.velocity = v1_new
            ball.velocity = v2_new

            self.coords += v1_new / self.ups
            ball.center += v2_new / self.ups
            self.collision_hash[ball.id] = True
            if clean is True:
                remove_overlap(self, ball)

        elif dx_norm <= (self.radius + ball.radius):
            self.coords += self.velocity / self.ups
            ball.center += ball.velocity / self.ups

        elif dx_norm > (self.radius + ball.radius):
            self.collision_hash[ball.id] = False

    def write(self, frame):
        if self.finished is True:
            return
        self.ups = min(1./self.real_timer(), self._ups)
        try:
            self.asset.write(frame)
        except:
            self.movers.remove(self)


def remove_overlap(ball1, ball2):
    x1 = ball1.center
    x2 = ball2.center
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
        # separate along text connecting centers
        dc = r_sum - c + 1
        da = a * (c + dc) / c - a
        db = b * (c + dc) / c - b
        x1[0] -= da * m1 / (m1 + m2)
        x2[0] += db * m2 / (m1 + m2)
        x1[1] -= db * m1 / (m1 + m2)
        x2[1] += da * m2 / (m1 + m2)
#

class BouncingAssetManager:

    def __init__(self,
                 asset_fun = None, #function or string path
                 dim = (1920, 1080),
                 max_balls = 2,
                 ball_frequency = (3,3),
                 velocity_magnitude_range = (300, 1000),
                 velocity_angle_range = (10, 80),
                 starting_location = (200, -200),
                 collisions = False,
                 max_fps = 30,
                 border_collision = True,
                 radius = 85,
                 scale = 1
                 ):

        assert asset_fun is not None
        self.radius = radius * scale
        self.dim = list(dim)
        self.max_balls = max_balls
        self.ball_frequency = list(ball_frequency)
        self.velocity_magnitude_range = list(velocity_magnitude_range)
        self.velocity_angle_range = list(velocity_angle_range)
        self.staring_location = list(starting_location)
        self.staring_location[1] += self.dim[1] # NEED TO NORMALIZE THIS LATER
        self.collision = collisions
        self.max_fps = max_fps
        self.border_collision = border_collision

        if isinstance(asset_fun, types.FunctionType): # check to see if asset fun is a function
            self.asset_fun = asset_fun

        elif isinstance(asset_fun, str):
            abs_dir = os.path.dirname((os.path.abspath(__file__)))
            asset_path = os.path.join(abs_dir, asset_fun)
            self.asset_fun = lambda: imga.ImageAsset(asset_path, scale=scale) # might want to do it slightly different adn not open
                                                                 # it from file each time.
        else:
            raise ValueError("asset_fun is not the proper type. it must be either function or string path")

        self.new_asset_timer = timers.CallFrequencyLimiter()
        self.dt_next = 0


    @property
    def n_movers(self):
        return AssetMover.n()

    @property
    def movers(self):
        return AssetMover.movers

    def make_new(self):
        # random initial velocity
        m = np.random.randint(*self.velocity_magnitude_range)
        a = np.random.randint(*self.velocity_angle_range) / 180 * np.pi
        v = np.array([np.cos(a) * m, -np.sin(a) * m])
        # put circle0 in a mover
        AssetMover(self.asset_fun(),
                 self.radius,
                 self.staring_location,
                 v,
                 (0, self.dim[0] - 1), (0, self.dim[1] - 1),
                 border_collision=self.border_collision,
                 ups=self.max_fps
                 )


    def move(self, frame):
        if self.border_collision is True:
            AssetMover.remove_finished()

        if self.new_asset_timer(self.dt_next) is True and AssetMover.n() < self.max_balls:
            self.make_new() # balls
            bf = self.ball_frequency
            self.dt_next = np.random.uniform(1) * (bf[1] - bf[0]) + bf[0]

        if self.collision is True:
            AssetMover.check_collisions()

        AssetMover.move_all()
        AssetMover.write_all(frame)


class CollisionDetector:
    """
    currently only supports circles, currently not optimized for searches faster than O(n^2)
    """

    def __init__(self, overlap=None):
        self.overlap = overlap

    def check(self, a0, a1, overlap=None):
        _overlap = overlap if overlap is not None else self.overlap

        #if asset_0.shape == "circle0" and asset_1.shape == 'circle0':
        return self._circle_to_circle_check(a0, a1, _overlap)

    def _circle_to_circle_check(self, a0, a1, overlap=None):
        r0 = a0.radius
        r1 = a1.radius
        centers_distance = np.sqrt(np.square(a0.center-a1.center).sum())
        if (r1+r0) * (1-overlap) >= centers_distance:
            return True
        else:
            return False

def main():
    MAX_FPS = 60
    DIMENSIONS = (1920, 1080)
    pie_path = './photo_asset_files/pie_asset'

    capture = camera.CameraPlayer(0,
                                  max_fps=MAX_FPS,
                                  dim=DIMENSIONS
                                  )

    bouncy_pies = BouncingAssetManager(asset_fun = pie_path,
                                       max_fps=60,
                                       dim=DIMENSIONS,
                                       collisions=True
                                       )


    time.sleep(1)

    while True:
        capture.read()
        bouncy_pies.move(capture.frame)
        capture.show()
        if cv2waitkey(1):
            break
    capture.stop()

class MovingAsset:

    movers = []
    _n_movers= 0
    def __int__(self,
                asset,
                coords=(0,0,0,0),  # must be in absolute coords
                velocity=(50, 50),
                x_range=(0,-1),
                y_range=(0,-1),
                border_collisions=True,
                ups=30,
                dim = (1280, 720),
                collidable = False,
                copy_asset=True,
                ):
        """
        MovingAssets only have absolute positions
        :param asset:
        :param coords:
        :param velocity:
        :param x_range:
        :param y_range:
        :param border_collisions:
        :param ups:
        :param dim:
        :param collidable:
        :return:
        """
        if copy_asset is True:
            self.asset = copy.deepcopy(asset)
        else:
            self.asset = asset

        self.coords = np.array(coords, dtype=int)
        self.velocity = np.array(velocity)

        self.dim = dim
        self.ups = ups

        self.x_range = x_range
        self.y_range = y_range

        if x_range[1] == -1:
            x_range[1] = dim[0]

        if y_range[1] == -1:
            y_range[1] = dim[1]

        self.border_collisions = border_collisions
        self.collidable = collidable

    def move(self):
        pass


if __name__=='__main__':
     # Reading an image in default mode
    image = np.zeros(400*400*3).reshape((400, 400, 3))
    # Window name in which image is displayed
    # Center coordinates
    center_coordinates = (120, 100)
    # Radius of circle0
    radius = 200
    # Red color in BGR
    color = (0, 0, 255)

    # Line thickness of -1 px
    thickness = -1

    # Using cv2.circle0() method
    # Draw a circle0 of red color of thickness -1 px
    image = cv2.circle(image, center_coordinates, radius, color, thickness)

    # Displaying the image
    cv2.imshow('meh', image)


