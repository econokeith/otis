import numpy as np
import cv2
import sys

from otis import camera
from otis.helpers import timers, coordtools
from otis.overlay import imageassets, assetmover
from otis.overlay.assetmover import AssetMover

if __name__ == "__main__":

        capture = camera.ThreadedCameraPlayer().start()
        sizes = (200, 200)
        n_bouncers = 500
        gravity = -1
        dampen = 0
        collide = False
        new_wait = .01


        def mover_function():
            pie = imageassets.AssetWithImage(center=(0, 0),
                                             resize_to = (50, 50),
                                             hitbox_type='circle',
                                             #use_circle_mask=True,
                                             )

            mover = AssetMover(pie,
                               center=(0, 0),
                               velocity=(np.random.randint(200, 500),
                                         np.random.rand() * -np.pi / 2),
                               dim=capture.dim,
                               ups=capture.max_fps,
                               border_collision=True,
                               gravity=gravity,
                               dampen=dampen,

                               )
            return mover


        manager = assetmover.CollidingAssetManager(collisions=collide)

        new_ball_timer = timers.CallFrequencyLimiter(new_wait)

        while True:
            _, frame = capture.read()
            frame_portion = coordtools.get_frame_portion(frame, (0,0,*sizes), ref='c')

            if manager.n < n_bouncers and new_ball_timer():
                ball = mover_function()
                manager.movers.append(ball)

            manager.update_velocities()
            manager.move()

            for mover in manager.movers:
                mover.asset.write(frame, frame_portion)
            capture.show()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        capture.stop()
        sys.exit()
