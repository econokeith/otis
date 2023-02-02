import cv2
import numpy as np

from otis import camera
from otis.helpers import coordtools, timers
from otis.overlay import shapes, assetholders, imageassets, textwriters

def main():
    ############################## SETUP ###################################################
    # start the camera
    square_size = 200
    v0 = (200, 1)
    v1 = (200, 1)
    v2 = (200, -2)

    capture = camera.ThreadedCameraPlayer(c_dim='720p',
                                          max_fps=30,
                                          record=False,
                                          record_to='bouncy_movers.mp4',
                                          record_dim='720p'
                                          )
    center = capture.f_center # note that this is a np.ndarray

    # set up frame asset without an frame, we'll update once the frame is running
    image_asset = imageassets.ImageAsset(resize_to=(square_size, square_size),
                                         hitbox_type='rectangle',
                                         border=True,
                                         b_color='b'
                                         )
    # set up the mover holding the frame asset
    mover = assetholders.AssetMover(image_asset,
                                    center=center + (200, 200),
                                    velocity=v0,
                                    dim=capture.f_dim,
                                    ups=capture.max_fps,
                                    )
    # line connecting center of frame to center of mover
    line = shapes.Line(thickness=2, color='g')
    # define the border of the center square that'll be copied to the frame asset each frame

    square = shapes.Rectangle(coords=(0, 0, square_size, square_size),
                              color='u',
                              ref='c',
                              dim=capture.f_dim,
                              thickness=2,
                              coord_format='cwh'
                              )
    #
    type_writer = textwriters.TypeWriter(coords=(0, 0),
                                         text="I am a mover I am a mover",
                                         loop=True,
                                         border=True,
                                         b_thickness=1,
                                         scale=1,
                                         one_border=True,
                                         max_lines=2,
                                         max_line_length=14,
                                         line_length_format='chars',
                                         perma_border=True,
                                         border_spacing=(.5, .5),
                                         anchor_point='c',
                                         jtype='l',
                                         transparent_background=.9,
                                         )
    # set up the mover holding the frame asset
    mover1 = assetholders.AssetMover(type_writer,
                                     center=center - (200, 200),
                                     velocity=v1,
                                     dim=capture.f_dim,
                                     ups=capture.max_fps,
                                     copy_asset=False,
                                     # show_hitbox=True,
                                     )

    #
    text_writer = textwriters.TextWriter(coords=(0, 0),
                                         text="I am a mover I am a mover",
                                         # loop=True,
                                         border=True,
                                         one_border=True,
                                         max_lines=2,
                                         max_line_length=14,
                                         # invert_background=True,
                                         line_length_format='chars',
                                         # perma_border = True,
                                         border_spacing=(.5, .5),
                                         anchor_point='c',
                                         jtype='l',
                                         background=True,
                                         back_color='g',
                                         transparent_background=.9,
                                         scale=1,
                                         )
    #

    mover2 = assetholders.AssetMover(text_writer,
                                     center=center - (-200, 200),
                                     velocity=v2,
                                     dim=capture.f_dim,
                                     ups=capture.max_fps,
                                     copy_asset=False,
                                     show_hitbox=True,
                                     )

    mover_manager = assetholders.CollidingAssetManager(collisions=True, move_before_delete=100)
    mover.name = '0'
    mover1.name = '1'
    mover2.name = '2'
    mover_manager.movers.append(mover)
    mover_manager.movers.append(mover1)
    mover_manager.movers.append(mover2)

    center_square = shapes.Rectangle((0, 0, square_size, square_size),
                                     ref='c',
                                     coord_format='cwh',
                                     to_abs=True,
                                     dim=capture.f_dim
                                     )

    #################################### the loop ###########################################
    time_to_stop = timers.TimeElapsedBool(5)
    while True:
        # get newest frame
        _, frame = capture.read()
        # copy the center of the frame
        frame_portion_saved = coordtools.get_frame_portion(frame,
                                                           (0, 0, square_size, square_size),
                                                           ref='c',
                                                           coord_format='cwh',
                                                           copy=True
                                                           )
        # write the line connecting centers

        # set copy of center to the frame of the frame asset of the mover
        mover.asset.image = frame_portion_saved
        # update / mover / write the mover
        mover_manager.update_velocities()

        for m in mover_manager.movers:
            mover_manager.detector.collide(m, center_square)

        mover_manager.move()
        mover_manager.write(frame)
        # fj
        line.write(frame, coords=(*center, *mover.center))
        # get the reference frame
        frame_portion_reference = coordtools.get_frame_portion(frame,
                                                               (0, 0, square_size, square_size),
                                                               ref='c',
                                                               coord_format='cwh',
                                                               copy=False
                                                               )
        # copy the previously saved center back on top of the updated center
        frame_portion_reference[:, :, :] = frame_portion_saved
        # but the background on the center
        square.write(frame)
        # show the frameq
        if time_to_stop() is True:
            capture.record = True
        capture.show()
        # break if you hit 'q' on the keyboard
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # kill all the stuff
    capture.stop()


if __name__ == '__main__':
    main()
