"""
Controls the movements . say more
"""
from collections import defaultdict, deque
import copy

import numpy as np
import cv2

from otis.helpers import timers, maths
from otis.overlay import shapes

class AssetMover:
    movers = []
    _n_movers = 0

    def __init__(self,
                 asset,
                 center=(0, 0),
                 velocity=(0, 0),
                 dim=(1280, 720),
                 x_range=None,
                 y_range=None,
                 border_collision=True,
                 ups=60, # this needs to match frame_rate
                 mass=None,
                 velocity_format='mag_radians',
                 gravity=0,
                 dampen=0.,
                 ):
        """
        moves the assets
        Args:
            asset:
            center:
            velocity:
            dim:
            x_range:
            y_range:
            border_collision:
            ups: updates per second. usually matches frame_rate, but it also automatically updates _ups to match how
                 the mover is being called.
            mass:
            velocity_format: either 'mag_radians' or 'xy
            gravity:
            dampen:
        """

        self._coords = np.zeros(4)
        self._coords[:2] = center
        self.dim = dim
        self.asset = copy.deepcopy(asset)
        self.asset.center = (0, 0)
        self.asset.ref = self._coords[:2]

        if velocity_format == 'mag_radians':
            mag, theta = velocity
            tan = np.tan(theta)
            x = np.sqrt(mag ** 2 / (1 + tan ** 2))
            self._coords[2:] = x, x * tan
        else:
            self._coords[2:] = velocity

        self.movers.append(self)
        AssetMover._n_movers += 1
        self.id = AssetMover._n_movers
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
            self.y_range += (height//2, -height//2)
            self.x_range += (width//2, -width//2)

        self.ups = ups
        self._ups = ups
        self.update_limiter = timers.CallFrequencyLimiter(1 / ups)
        self.real_time_elapsed = timers.TimeSinceLast()
        self.real_time_elapsed()
        self.is_finished = False
        self.mass = (height * width) if mass is None else mass
        self._x_border_collision = False
        self._y_border_collision = False
        self.gravity = gravity
        self.dampening = 1. - dampen
        self.has_moved = False

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

    @property
    def height(self):
        return self.asset.height

    @property
    def width(self):
        return self.asset.width

    @property
    def radius(self):
        return self.asset.radius

    def update_velocity(self):
        # don't update if it's not time
        if self.update_limiter() is False or self.is_finished is True:
            return

        self.velocity[1] -= self.gravity
        self._check_for_border_collisions()
        self._update_velocity_from_b_collisions()

    def move(self):
        self.coords[0] += self.velocity[0] / self.ups
        self.coords[1] += self.velocity[1] / self.ups
        self._check_for_boundary_snags()

    def write(self, frame, safe_delete=False, **kwargs):
        """

        Args:
            frame: cv2/np.ndarray frame
            safe_delete:
                adds:
                    try:
                        self.asset.write(frame, **kwargs)
                    except:
                        self.is_finished = True

        Returns:
            N/A
        """
        if self.is_finished is True:
            return
        # self.ups = max(1. / self.real_time_elapsed(), self._ups)
        # print(self.ups)
        self.ups = 1. / self.real_time_elapsed()
        if safe_delete is True:
            try:
                self.asset.write(frame, **kwargs)
            except:
                self.is_finished = True
        else:
            self.asset.write(frame, **kwargs)

    def update_move_write(self, frame):
        self.update_velocity()
        self.move()
        self.write(frame)

    def _check_for_border_collisions(self):

        prop_x, prop_y = self._coords[:2] + self._coords[2:] / self.ups
        x0, x1 = self.x_range
        y0, y1 = self.y_range

        if x0 < prop_x < x1:
            self._x_border_collision = False
        else:
            self._x_border_collision = True

        if y0 < prop_y < y1:
            self._y_border_collision = False
        else:
            self._y_border_collision = True

    def _update_velocity_from_b_collisions(self):
        if self._x_border_collision is True and self.border_collisions is False:
            self.is_finished = True
            print('deleted by border')
        elif self._x_border_collision is True and self.border_collisions is True:
            self.velocity[0] *= -1 * self.dampening
        else:
            pass

        if self._y_border_collision is True and self.border_collisions is False:
            self.is_finished = True
            print('deleted by border')

        elif self._y_border_collision is True and self.border_collisions is True:
            self.velocity[1] *= -1 * self.dampening
        else:
            pass

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

class CollidingAssetManager:

    def __init__(self,
                 dim=(1920, 1080),
                 collisions=False,
                 border_collision=True,
                 max_movers=None,
                 buffer=0,
                 ):

        """
        Manages Colliding assets on screen
        Args:
            dim: frame dimensions
            collisions: bool, default = False
                do assets collide
            border_collision: bool, default=True
                do assets collide with border of just run off the screen
            max_movers: int
                how many mover assets max
            buffer: tbd
        """

        self.collisions = collisions
        self.border_collision = border_collision
        self.movers = deque([], max_movers)
        self.dim = dim
        self.detector = CollisionDetector(buffer=buffer)
        self.max_movers = max_movers

    @property
    def n(self):
        return len(self.movers)

    def append(self, new):
        self.movers.append(new)

    def reset_movers(self):
        self.movers = []

    def add_movers(self, new_movers):
        self.movers += list(new_movers)

    def remove_finished(self):
        living_movers = []

        for mover in self.movers:
            if mover.is_finished is False:
                living_movers.append(mover)
            else:
                del mover

        self.movers = deque(living_movers, self.max_movers)

    def update_velocities(self):
        if self.collisions is True and self.n >= 2:

            for i in range(self.n-1):
                m0 = self.movers[i]
                for j in range(i+1, self.n):
                    m1 = self.movers[j]
                    self.detector.collide(m0, m1)

        for mover in self.movers:
            mover.update_velocity()

    def write(self, frame):

        for mover in self.movers:
            mover.write(frame)

    def move(self):
        """
        moves the movers and prunes the movers with mover.is_finished = True
        Returns: N/A

        """
        live_movers = deque([], self.max_movers)
        for mover in self.movers:
            if mover.is_finished is False:
                mover.move()
                live_movers.append(mover)
            else:
                del mover
        self.movers = live_movers

    def update_move_write(self, frame):
        self.update_velocities()
        self.move()
        self.write(frame)

class CollisionDetector:
    """
    currently only supports circles, currently not optimized for searches faster than O(n^2)
    """
    def __init__(self, buffer=0, move_before_delete=10):
        """

        Args:
            buffer: adds
            move_before_delete:
        """

        self.buffer = buffer
        self.moves_before_delete = move_before_delete

    def check(self, asset_0, asset_1, buffer=0):
        _buffer = buffer if buffer is not None else self.buffer

        # if asset_0.shape == "circle" and asset_1.shape == 'circle':
        return self._circle_to_circle_check(asset_0, asset_1, _buffer)

    def _circle_to_circle_check(self, a0, a1, buffer):
        r0 = a0.radius
        r1 = a1.radius
        centers_distance = np.sqrt(np.square(a0.center - a1.center).sum())

        if (r1 + r0) + buffer >= centers_distance:
            return True
        else:
            return False

    def collide(self, asset_0, asset_1, buffer=0):
        _buffer = buffer if buffer is not None else self.buffer
        self._two_circle_velocity_update(asset_0, asset_1, _buffer)

    def _two_circle_velocity_update(self, circle_0, circle_1, buffer):

        v0 = circle_0.velocity
        v1 = circle_1.velocity
        c0 = circle_0.center
        c1 = circle_1.center
        m0 = circle_0.mass
        m1 = circle_0.mass
        r0 = circle_0.radius
        r1 = circle_1.radius

        d_center = c0 - c1
        dist_2 = np.sum(d_center ** 2)
        distance = np.sqrt(dist_2)

        # collisions hash makes it so that balls don't interact until they have fully separated
        # need to add
        if distance <= (r0 + r1) + buffer and circle_0.mass is None:
            d_velocity = v0 - v1
            dot_p1 = np.inner(-d_velocity, -d_center)
            d_v1 = -2  * (dot_p1 / dist_2) * (-d_center)
            circle_1.coords[2:] += d_v1
            i = 0
            while True:
                circle_1.move()
                distance = maths.linear_distance(circle_1.center, circle_0.center)
                if distance > (r0 + r1) + buffer:
                    break

                if i>self.moves_before_delete :
                    circle_1.is_finished=True
                    print('deleted by bounder')
                    break

                i+=1

        # todo : turn the while loops on circle collision into some kind of function to get rid of the boilerplate
        elif distance <= (r0 + r1) + buffer and circle_1.mass is None:
            d_velocity = v0 - v1
            dot_p0 = np.inner(d_velocity, d_center)
            d_v0 = -2 * (dot_p0 / dist_2) * d_center
            circle_0.coords[2:] += d_v0
            # remove_overlap_w_no_mass(circle_1, circle_0)
            i=0
            while True:
                circle_0.move()
                distance = maths.linear_distance(circle_1.center, circle_0.center)

                if distance > (r0 + r1) + buffer:
                    break

                if i > self.moves_before_delete:
                    circle_0.is_finished = True
                    print('deleted by bounder')
                    break

                i += 1

        elif distance <= (r0 + r1) + buffer: #and circle_0.collision_hash[circle_1.id] is False:

            d_velocity = v0 - v1
            dot_p0 = np.inner(d_velocity, d_center)
            dot_p1 = np.inner(-d_velocity, -d_center)

            d_v0 = -2 * m1 / (m0 + m1) * (dot_p0 / dist_2) * d_center
            d_v1 = -2 * m0 / (m0 + m1) * (dot_p1 / dist_2) * (-d_center)

            circle_0.coords[2:] += d_v0
            circle_1.coords[2:] += d_v1

            i=0
            while True:
                circle_0.move()
                circle_1.move()
                distance = maths.linear_distance(circle_1.center, circle_0.center)

                if distance > (r0 + r1) + buffer:
                    break

                if i > self.moves_before_delete:
                    print('deleted by collision')
                    circle_1.is_finished = True
                    circle_0.is_finished = True
                    break

                i += 1
        ###############################################################
        # NOT CURRENTLY USING COLLISION_HASH. MAY COME BACK TO IT
        ###############################################################
            # circle_0.collision_hash[circle_1.id] = True
            # circle_1.collision_hash[circle_0.id] = True
            # remove_overlap(circle_0, circle_1)

        # elif distance <= (r0 + r1) + buffer and circle_0.collision_hash[circle_1.id] is True:
        #     pass  # no effect until they seperate
        #
        # elif distance > (r0 + r1) +buffer and circle_0.mass is not None and circle_1.mass is not None:
        #     circle_0.collision_hash[circle_1.id] = False
        #     circle_1.collision_hash[circle_0.id] = False

# todo: Consider adding Hitbox to all assets separately
class Hitbox:
    asset: shapes.ShapeAsset

    def __init__(self,
                 shape_type,  # circle0 rectable
                 dimensions=(0, 0),  # width, height
                 ):
        self.shape_type = shape_type

        if isinstance(dimensions, (int, float)):
            self.dimensions = np.array((dimensions,) * 2).astype(int)

        else:
            self.dimensions = np.array(dimensions).astype(int)

    @property
    def height(self):
        return self.dimensions[1]

    @property
    def width(self):
        return self.dimensions[0]


if __name__ == '__main__':
    # Reading an image in default mode
    from otis.helpers.colortools import ColorCycle
    from otis.overlay import imageassets
    dim = (800, 800)
    fps = 30
    frame = np.zeros(dim[0] * dim[1] * 3, dtype='uint8').reshape((dim[1], dim[0], 3))
    colors = ColorCycle()

    def mover_function():

        pie = imageassets.ImageAsset(center=(0, 0), hitbox_type='circle0')
        pie.add_image_from_file('./photo_assets/pie_asset', file=__file__)

        mover = AssetMover(pie,
                           center=(100, 100),
                           velocity=(np.random.randint(200, 300), np.random.rand() * -np.pi / 2),
                           dim=dim,
                           ups=fps,
                           border_collision=True,
                           gravity=-20,
                           dampen=.02,
                           )
        return mover

    fps_limiter = timers.SmartSleeper(1 / fps)

    manager = CollidingAssetManager(collisions=True)

    new_ball_timer = timers.CallFrequencyLimiter(1)

    while True:
        frame[:, :, :] = 0

        if manager.n < 2 and new_ball_timer():
            ball = mover_function()
            manager.movers.append(ball)

        manager.update_velocities()
        manager.move()
        manager.write(frame)

        fps_limiter()
        cv2.imshow('meh', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
