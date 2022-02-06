"""
tools for making assets move around on the screen
"""
import numpy as np
import cv2

from robocam.helpers import timers

#add vector form types
class AssetMover:

    def __init__(self,
                 asset,
                 mover_radius,
                 position0, #must be in absolute coords
                 velocity0,
                 x_range,
                 y_range,
                 border_collision=False,
                 ups = 30 #updates per second
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
        self.x_range = np.array([x_range[0]+self.radius,
                                 x_range[1]-self.radius]
                                )

        self.y_range = np.array([y_range[0]+self.radius,
                                 y_range[1]-self.radius]
                                )

        self.border_collision = border_collision
        self.ups = ups
        self.timer = timers.CallHzLimiter(1/ups)
        self.finished = False

        self.mass = self.radius

    def move(self):
        #don't update if it's not time

        if self.timer() is False or self.finished is True:
            return

        # find proposal position
        prop_x, prop_y = self.position + self.velocity/self.ups

        #check if proposals are in bound and then act based on self.border_collision
        x0, x1 = self.x_range
        y0, y1 = self.y_range

        if x0 < prop_x < x1:
            self.position[0] = prop_x

        elif self.border_collision is True:
            self.velocity[0] *= -1
            self.position[0] += self.velocity[0]/self.ups

        else:
            self.finished = True

        if y0 < prop_y < y1:
            self.position[1] = prop_y

        elif self.border_collision is True:
            self.velocity[1] *= -1
            self.position[1] += self.velocity[0]/self.ups

        else:
            self.finished = True

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

    dv = v1-v2
    dx = x1-x2
    dx_norm_2 = np.sum(dx**2)

    dot_p1 = np.inner(dv,dx)
    dot_p2 = np.inner(-dv, -dx)
    v1_new = v1 - 2*m2/(m1+m2)*(dot_p1/dx_norm_2)*dx
    v2_new = v2 - 2*m1/(m1+m2)*(dot_p2/dx_norm_2)*(-dx)

def ball_collision(ball1, ball2):
    v1 = ball1.velocity
    v2 = ball2.velocity
    x1 = ball1.position
    x2 = ball2.position
    m1 = ball1.mass
    m2 = ball2.mass

    dv = v1-v2
    dx = x1-x2
    dx_norm_2 = np.sum(dx**2)

    dot_p1 = np.inner(dv,dx)
    dot_p2 = np.inner(-dv, -dx)
    v1_new = v1 - 2*m2/(m1+m2)*(dot_p1/dx_norm_2)*dx
    v2_new = v2 - 2*m1/(m1+m2)*(dot_p2/dx_norm_2)*(-dx)

def post_collision_velocities(v1, v2, x1, x2, m1=1, m2=1):

    dv = v1-v2
    dx = x1-x2
    dx_norm_2 = np.sum(dx**2)

    dot_p1 = np.inner(dv,dx)
    dot_p2 = np.inner(-dv, -dx)
    v1_new = v1 - 2*m2/(m1+m2)*(dot_p1/dx_norm_2)*dx
    v2_new = v2 - 2*m1/(m1+m2)*(dot_p2/dx_norm_2)*(-dx)
    return v1_new, v2_new

class CollisionManager:

    def __init__(self, balls):
        self.balls = balls

    def detection_collisions(self):
        for b1 in self.balls:
            for b2 in self.balls[1:]:
                r1 = b1.radius
                r2 = b2.radius
                x1 = b1.position
                x2 = b2.position
                dx = x1-x2
                dx_norm = np.sqrt(dx[0]**2+dx[1]**2)
                if dx_norm <= (r1+r2):
                    v1 = b1.velocity
                    v2 = b2.velocity
                    m1 = b1.mass
                    m2 = b2.mass
                    v1[:], v2[:] = post_collision_velocities(v1,v2,x1,x2,m1,m2)




if __name__=='__main__':
    from robocam.overlay.cv2shapes import Circle
    from robocam.helpers.timers import CallHzLimiter
    from robocam.helpers.utilities import cv2waitkey
    DIMENSIONS = dx, dy = (1080, 720)
    frame = np.zeros((*DIMENSIONS[::-1], 3), dtype='uint8')
    circle = Circle((0,0), 40)
    circle2 = Circle((50,50), 50, color='g')


    fps_limit = CallHzLimiter(1/60)
    moving_circle = AssetMover(circle, 50, (500, 300),(100, 200),
                               (0, dx-1),(0,dy-1), border_collision=True,
                               ups=60)
    moving_circle2 = AssetMover(circle2, 50, (500, 400),(100, 200),
                               (0, dx-1),(0,dy-1), border_collision=True,
                               ups=60)

    collision_manager = CollisionManager([moving_circle2, moving_circle])


    while True:
        frame[:,:,:] = 0
        collision_manager.detection_collisions()
        moving_circle.move()
        moving_circle.write(frame)
        moving_circle2.move()
        moving_circle2.write(frame)
        fps_limit()
        cv2.imshow('test', frame)

        if cv2waitkey(1):
            break








