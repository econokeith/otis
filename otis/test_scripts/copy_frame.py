import cv2
import otis.camera as camera
import otis.helpers.coordtools as coordtools
import sys
import otis.helpers.shapefunctions as shapefunctions
import otis.helpers.cvtools as cvtools
from otis.overlay import shapes

if __name__ == "__main__":

    square_dim = (200, 200)
    little_output_dim = (200, 50)
    big_output_dim = (300, 300)
    dim = (720, 720)
    capture = camera.ThreadedCameraPlayer(max_fps=30, dim=dim, flip=False).start()
    square = shapes.Rectangle((0, 0, *square_dim), 'cwh', ref='c', dim=dim, thickness=2)
    n_littles = 1
    while True:
        _, frame = capture.read()
        # frame_from = frame[tf:bf, lf:rf]
        # frame_to = frame[tt:bt, lt:rt]
        # frame_to[:] = cv2.resize(frame_from, frame_to.shape[:2][::-1])


        corners = ('rt', 'lb', 'lt', 'rb')
        os = 20
        ff = ((-os, -os), (os, os), (os, -os), (-os, os))
        for i, corner in enumerate(corners):

            shapefunctions.copy_frame_portion_to(frame,
                                                 (0, 0, *square_dim),
                                                 (*ff[i], *big_output_dim),
                                                 source_format='cwh',
                                                 destination_format=corner+'wh',
                                                 source_ref='c',
                                                 destination_ref=corner,
                                                 )


        bw, bh = big_output_dim
        for i in range(n_littles):
            w, h = little_output_dim
            shapefunctions.copy_frame_portion_to(frame,
                                                 (0, 0, *square_dim),
                                                 (bw+i*w, 0, *little_output_dim),
                                                 source_format='cwh',
                                                 destination_format='lbwh',
                                                 source_ref='c',
                                                 destination_ref='lb',
                                                 )
        for i in range(n_littles):
            w, h = little_output_dim
            shapefunctions.copy_frame_portion_to(frame,
                                                 (0, 0, *square_dim),
                                                 (-bw - i * w, 0, *little_output_dim),
                                                 source_format='cwh',
                                                 destination_format='rbwh',
                                                 source_ref='c',
                                                 destination_ref='rb',
                                                 )

        for i in range(n_littles):
            w, h = little_output_dim
            shapefunctions.copy_frame_portion_to(frame,
                                                 (0, 0, *square_dim),
                                                 (-bw - i * w, 0, *little_output_dim),
                                                 source_format='cwh',
                                                 destination_format='rtwh',
                                                 source_ref='c',
                                                 destination_ref='rt',
                                                 )

        for i in range(n_littles):
            w, h = little_output_dim
            shapefunctions.copy_frame_portion_to(frame,
                                                 (0, 0, *square_dim),
                                                 (bw + i * w, 0, *little_output_dim),
                                                 source_format='cwh',
                                                 destination_format='ltwh',
                                                 source_ref='c',
                                                 destination_ref='lt',
                                                 )

        square.write(frame)
        capture.show()
        if cvtools.cv2waitkey() == True:
            break

    capture.stop()
    sys.exit()
