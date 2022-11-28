import numpy as np
import cv2
import sys

from otis import camera
from otis.helpers import timers, coordtools
from otis.overlay import imageassets, assetmover, shapes
from otis.overlay.assetmover import AssetMover

if __name__ == "__main__":

        capture = camera.ThreadedCameraPlayer().start()
        sizes = (300,300)
        n_bouncers =40
        gravity = 0
        dampen = 0
        collide = True
        new_wait = .01
        time_since_ball = timers.TimeSinceLast()
        x_value = timers.TimedCycle(50, 1170, updown=True, cycle_t=2)
        circle = shapes.Circle((0, 0), 150, ref='c')
        circle.mass = np.inf
        circle.velocity = (0, 0)
        circle.width = 150
        circle.height = 150

        def mover_function():
            pie = imageassets.AssetWithImage(center=(0, 0),
                                             resize_to = (50, 50),
                                             hitbox_type='circle',
                                             use_circle_mask=True,
                                             )

            mover = AssetMover(pie,
                               center=(x_value(), 50),
                               velocity=(np.random.randint(200, 500),
                                         -np.pi/4 +np.random.rand() * -np.pi / 2),
                               dim=capture.dim,
                               ups=capture.max_fps,
                               border_collision=True,
                               gravity=gravity,
                               dampen=dampen,

                               )
            return mover


        manager = assetmover.CollidingAssetManager(collisions=collide, max_movers=n_bouncers)
        new_ball_timer = timers.CallFrequencyLimiter(new_wait)

        while True:
            _, frame = capture.read()
            frame_portion = coordtools.get_frame_portion(frame, (0,0,*sizes), ref='c')

            if new_ball_timer() is True:

                ball = mover_function()
                manager.movers.append(ball)

            manager.update_velocities()
            for mover in manager.movers:
                manager.detector.collide(circle, mover)

            manager.move()

            for mover in manager.movers:
                mover.asset.write(frame, frame_portion)


            circle.write(frame)
            capture.show(frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        capture.stop()
        sys.exit()
