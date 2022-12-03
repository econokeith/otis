import cv2

from otis import camera
from otis.helpers import coordtools
from otis.overlay import shapes, assetmover, imageassets


def main():
    ############################# SETUP ###################################################
    # start the camera
    square_size = 200
    capture = camera.ThreadedCameraPlayer(c_dim='720p')
    center = capture.f_center
    print(center)
    # set up image asset without an image, we'll update once the frame is running
    image_asset = imageassets.ImageAsset(resize_to=(square_size, square_size),
                                         hitbox_type='rectangle',
                                         border=True,
                                         b_color='b'
                                         )
    # set up the mover holding the image asset
    mover = assetmover.AssetMover(image_asset,
                                  velocity=(200, 1),
                                  dim=capture.f_dim,
                                  ups=capture.max_fps,
                                  )
    # line connecting center of frame to center of mover
    line = shapes.Line(thickness=2, color='g')
    # define the border of the center square that'll be copied to the image asset each frame
    square = shapes.Rectangle(coords=(0, 0, square_size, square_size),
                              color='u',
                              ref='c',
                              dim=capture.f_dim,
                              thickness=2,
                              coord_format='cwh'
                              )

    ########## the loop ############################################
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
        line.write(frame, coords=(*center, *mover.center))
        # set copy of center to the image of the image asset of the mover
        mover.asset.image = frame_portion_saved
        # update / mover / write the mover
        mover.update_move_write(frame)
        # get a reference to the center of the scren
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
        capture.show()
        # break if you hit 'q' on the keyboard
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    # kill all the stuff
    capture.stop()


if __name__ == '__main__':
    main()
