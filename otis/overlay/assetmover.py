"""
This is a very simple collision detection class
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
from otis.overlay import imageassets as imga, shapes
import otis.camera as camera

class Hitbox:
    asset: shapes.ShapeAsset
    def __init__(self,
                 shape_type, # circle rectable
                 dimensions=(0,0), # width, height
                 ):
        self.shape_type = shape_type

        if isinstance(dimensions, (int, float)):
            self.dimensions = np.array((dimensions,)*2).astype(int)

        else:
            self.dimensions = np.array(dimensions).astype(int)

    @property
    def height(self):
        return self.dimensions[1]

    @property
    def width(self):
        return self.dimensions[0]





class AssetMover:
    movers = []
    _n_movers= 0

    def __init__(self,
                 asset,
                 center=(0,0),
                 velocity=(0,0),
                 dim = (1280, 720),
                 x_range=None,
                 y_range=None,
                 border_collision=True,
                 ups=30, #this needs to match frame_rate
                 mass=None,
                 velocity_format = 'mag_radians'
                 ):

        self._coords = np.zeros(4)
        self._coords[:2] = center
        self.dim = dim
        self.asset = copy.deepcopy(asset)
        self.asset.center = (0, 0)
        self.asset.ref = self._coords[:2]

        if velocity_format == 'mag_radians':
            mag, theta = velocity
            tan = np.tan(theta)
            x = np.sqrt(mag**2/(1+tan**2))
            self._coords[2:] = x, x * tan
        else:
            self._coords[2:] = velocity


        self.movers.append(self)
        self._n_movers +=1
        self.id = self._n_movers
        self.scale = 1
        self.collision_hash = defaultdict(lambda: False)
        self.border_collisions = border_collision

        if x_range is None:
            self.x_range = np.array([0, dim[0]], dtype=int)
        else:
            self.x_range = np.array(x_range, dtype=int)

        if y_range is None:
            self.y_range = np.array([0, dim[1]], dtype=int)
        else:
            self.y_range = np.array(y_range, dtype=int)

        _, _, width, height = asset.center_width_height()

        if self.border_collisions is True:

            self.y_range += (height,-height)
            self.x_range += (width, -width)

        self.ups = ups
        self._ups = ups
        self.update_limiter = timers.CallFrequencyLimiter(1 / ups)
        self.real_time_elapsed = timers.TimeSinceLast()
        self.real_time_elapsed()
        self.is_finished = False
        self.mass = (height*width) if mass is None else mass
        self._x_border_collision = False
        self._y_border_collision = False

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, new_coords):
        self._coords[:] = new_coords


    @property
    def center(self):
        return self._coords[:2]

    @center.setter
    def center(self, new_center):
        self._coords[:2] = new_center

    @property
    def velocity(self):
        return self._coords[2:]

    @velocity.setter
    def velocity(self, new_velocity):
        self._coords[2:] = new_velocity

    def move(self):
        # don't update if it's not time
        if self.update_limiter() is False or self.is_finished is True:
            return

        self.ups = 1. / self.real_time_elapsed()
        self._check_for_border_collisions()
        self._check_for_boundary_snags()

    def _check_for_border_collisions(self):
        # find proposal coords this needs a timer added, but now it's fine.
        prop_x, prop_y = self._coords[:2] + self._coords[2:] / self.ups

        # check if proposals are in bound and then act based on self.border_collisions
        x0, x1 = self.x_range
        y0, y1 = self.y_range

        # is x inbounds after proposed move
        if x0 < prop_x < x1:
            self._x_border_collision = False
        else:
            self._x_border_collision = True

        if self._x_border_collision is False:
                self._coords[0] = prop_x

        elif self._x_border_collision is True and self.border_collisions is False:
                self.is_finished = True

        elif self._x_border_collision is True and self.border_collisions is True:

            self.velocity[0] *= -1
            self._coords[0] += self.velocity[0] / self.ups

        if y0 < prop_y < y1:
            self._y_border_collision = False
        else:
            self._y_border_collision = True

        if self._y_border_collision is False:
            self._coords[1] = prop_y

        elif self._y_border_collision is True and self.border_collisions is False:
            self.is_finished = True

        elif self._y_border_collision is True and self.border_collisions is True:

            self.velocity[1] *= -1
            self._coords[1] += self.velocity[1] / self.ups

    def _check_for_boundary_snags(self):
        # make sure nothing is snagged on a boundary
        if self._coords[0] < self.x_range[0]:
            self._coords[0] = self.x_range[0] + 1
        elif self._coords[0] > self.x_range[1]:
            self._coords[0] = self.x_range[1] - 1

        if self._coords[1] < self.y_range[0]:
            self._coords[1] = self.y_range[0] + 1
        elif self._coords[1] > self.y_range[1]:
            self._coords[1] = self.y_range[1] - 1

    def write(self, frame):
        if self.is_finished is True:
            return

        # self.ups = max(1. / self.real_time_elapsed(), self._ups)
        # print(self.ups)

        self.ups = 1. / self.real_time_elapsed()
        # try:
        #     self.asset.write(frame)
        # except:
        #     self.is_finished
        self.asset.write(frame)


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
        # separate along line connecting centers
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
                 starting_location = (200, -200),## TODO this relative thing will need to be fixed
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
        # put circle in a mover
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

        #if a0.shape == "circle" and a1.shape == 'circle':
        return self._circle_to_circle_check(a0, a1, _overlap)

    def _circle_to_circle_check(self, a0, a1, overlap=None):
        r0 = a0.radius
        r1 = a1.radius
        centers_distance = np.sqrt(np.square(a0.center-a1.center).sum())
        if (r1+r0) * (1-overlap) >= centers_distance:
            return True
        else:
            return False


if __name__=='__main__':
     # Reading an image in default mode
    from otis.helpers.colortools import ColorCycle
    dim = (800, 800)
    fps = 144
    frame = np.zeros(dim[0]*dim[1]*3).reshape((dim[1], dim[0], 3))
    circle = shapes.Circle((0, 0), 40)
    colors = ColorCycle()
    movers = []

    for i in range(30):

        circle = shapes.Circle((0, 0), np.random.randint(10, 100), color=colors())
        mover = AssetMover(circle,
                           center=(400, 400),
                           velocity = (np.random.randint(500, 1000), np.random.rand()*2*np.pi),
                           dim=dim,
                           ups=fps,
                           border_collision=True
                       )
        movers.append(mover)

    fps_limiter = timers.SmartSleeper(1/fps)

    while True:
        frame[:,:,:] = 0
        for mover in movers:
            mover.move()
            mover.write(frame)
        fps_limiter()

        cv2.imshow('meh', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()



