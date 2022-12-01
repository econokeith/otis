import numpy as np
import cv2
import sys

from otis import camera
from otis.helpers import timers, coordtools
from otis.overlay import imageassets, assetmover, shapes
from otis.overlay.assetmover import AssetMover

if __name__ == "__main__":

    capture = camera.ThreadedCameraPlayer().start()
    sizes = (300, 300)
    n_bouncers = 10
    gravity = -10
    dampen = .05
    new_wait = 1
    time_since_ball = timers.TimeSinceLast()
    x_value = timers.TimedCycle(200, 1020, updown=True, cycle_t=1)
    circle = shapes.Circle((0, 0), 100,
                           ref='c',
                           dim=capture.dim,
                           to_abs=True)

    circle.velocity = (0, 0)
    ball_buffer = 5
    circle_buffer = 5
    collide = True
    small_size = 25


    def mover_function():
        pie = imageassets.ImageAsset(center=(0, 0),
                                     resize_to=(100, 100),
                                     hitbox_type='circle0',
                                     use_circle_mask=True,
                                     )

        mover = AssetMover(pie,
                           center=(640, 50),
                           velocity=(np.random.randint(100, 200),
                                     np.random.rand() * np.pi/2 + np.pi/4),
                           dim=capture.dim,
                           ups=capture.max_fps,
                           border_collision=True,
                           gravity=gravity,
                           dampen=dampen,

                           )
        return mover


    manager = assetmover.CollidingAssetManager(collisions=collide, max_movers=n_bouncers, buffer=10)
    new_ball_timer = timers.CallFrequencyLimiter(new_wait)

    while True:
        _, frame = capture.read()
        frame_portion = coordtools.get_frame_portion(frame, (0, 0, *sizes), ref='c')
        circle.write(frame)
        if new_ball_timer() is True:# and manager.n < n_bouncers:
            ball = mover_function()
            manager.movers.append(ball)

        manager.update_velocities()
        for mover in manager.movers:
            manager.detector.collide(circle, mover, buffer=10)
            assetmover.remove_overlap_w_no_mass(circle, mover)

        manager.move()

        for mover in manager.movers:
            mover.asset.write(frame, frame_portion)


        capture.show(frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()
    sys.exit()
