import cv2
import numpy as np
import os
from otis import camera
from otis.helpers import coordtools, timers
from otis.overlay import shapes, assetholders, imageassets, textwriters

def main():
    ############################## SETUP ###################################################
    # start the camera
    square_size = 200
    v0 = (200, 1)
    v1 = (200, -1)
    v2 = (200, 2)

    capture = camera.ThreadedCameraPlayer(c_dim='1080p',
                                          max_fps=30,
                                          output_scale=2,
                                          # record=False,
                                          # record_to='bouncy_movers.mov',
                                          # record_dim='720p'
                                          )
    center = capture.f_center

    path_to_dir = os.path.abspath(os.path.dirname(__file__))
    path_to_image = os.path.join(path_to_dir, 'David.jpg')
    image = cv2.imread(path_to_image)[180:, :, :]
    image = cv2.resize(image, (0,0), fx=.5, fy=.5)

    print(image.shape)

    print(image.shape)
    # set up image asset without an image, we'll update once the frame is running
    image_asset = imageassets.ImageAsset(
                                         hitbox_type='rectangle',
                                         border=True,
                                         b_color='b',
                                         resize_to = (300, 300)
                                         )
    image_asset.image = image
    # set up the mover holding the image asset
    mover = assetholders.AssetMover(image_asset,
                                    center=center,
                                    velocity=v0,
                                    dim=capture.f_dim,
                                    ups=capture.max_fps,
                                    copy_asset=True
                                    )
    # line connecting center of frame to center of mover

    mover2 = assetholders.AssetMover(image_asset,
                                    center=center + (200, 200),
                                    velocity=v1,
                                    dim=capture.f_dim,
                                    ups=capture.max_fps,
                                    copy_asset=True
                                    )

    mover3 = assetholders.AssetMover(image_asset,
                                    center=center + (-200, 200),
                                    velocity=v2,
                                    dim=capture.f_dim,
                                    ups=capture.max_fps,
                                    copy_asset=True
                                    )

    mover_manager = assetholders.CollidingAssetManager(collisions=True, move_before_delete=100)
    mover.name = '0'

    mover_manager.movers.append(mover)
    mover_manager.movers.append(mover2)
    mover_manager.movers.append(mover3)


    # center_square = shapes.Rectangle((0, 0, square_size, square_size),
    #                                  ref='c',
    #                                  coord_format='cwh',
    #                                  to_abs=True,
    #                                  dim=capture.f_dim
    #                                  )

    #################################### the loop ###########################################
    time_to_stop = timers.TimeElapsedBool(5)
    while True:
        # get newest frame
        _, frame = capture.read()
        # copy the center of the frame
        # frame_portion_saved = coordtools.get_frame_portion(frame,
        #                                                    (0, 0, square_size, square_size),
        #                                                    ref='c',
        #                                                    coord_format='cwh',
        #                                                    copy=True
        #                                                    )
        # write the line connecting centers
        # frame[:,:,:]=1
        # set copy of center to the image of the image asset of the mover
        mover.asset.image = image
        # update / mover / write the mover
        mover_manager.update_velocities()


        mover_manager.move()
        mover_manager.write(frame)
        # fj

        # get the reference frame
        # frame_portion_reference = coordtools.get_frame_portion(frame,
        #                                                        (0, 0, square_size, square_size),
        #                                                        ref='c',
        #                                                        coord_format='cwh',
        #                                                        copy=False
        #                                                        )
        # # copy the previously saved center back on top of the updated center
        # frame_portion_reference[:, :, :] = frame_portion_saved
        # # but the background on the center
        # square.write(frame)
        # show the frameq
        # if time_to_stop() is True:
        #     capture.record = True
        capture.show(frame)
        # break if you hit 'q' on the keyboard
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # kill all the stuff
    capture.stop()


if __name__ == '__main__':
    main()
