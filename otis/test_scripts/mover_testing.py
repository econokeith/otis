import numpy as np
import cv2

from otis import camera
from otis.helpers import timers
from otis.overlay import imageassets, assetmover
from otis.overlay.assetmover import AssetMover

if __name__ == "__main__":
    while True:
        capture = camera.ThreadedCameraPlayer().start()

        def mover_function():
            pie = imageassets.AssetWithImage(center=(0, 0), hitbox_type='circle')
            pie.add_image_from_file('../overlay/photo_assets/pie_asset')

            mover = AssetMover(pie,
                               center=(100, 100),
                               velocity=(np.random.randint(200, 300), np.random.rand() * -np.pi / 2),
                               dim=capture.dim,
                               ups=capture.max_fps,
                               border_collision=True,
                               gravity=-20,
                               dampen=.02,
                               )
            return mover


        manager = assetmover.CollidingAssetManager(collisions=True)

        new_ball_timer = timers.CallFrequencyLimiter(1)

        while True:
            _, frame = capture.read()
            if manager.n < 2 and new_ball_timer():
                ball = mover_function()
                manager.movers.append(ball)

            manager.update_velocities()
            manager.move()
            manager.write(frame)
            capture.show()

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        capture.stop()
