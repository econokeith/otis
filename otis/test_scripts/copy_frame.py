import cv2
import otis.camera as camera
import otis.helpers.coordtools as coordtools
import sys
import otis.helpers.shapefunctions as shapefunctions
import otis.helpers.cvtools as cvtools


if __name__ == "__main__":
    capture = camera.ThreadedCameraPlayer(max_fps=30, dim=(1280, 720), flip=False).start()
    # copy_from_rt = coordtools.abs_point((100, 100), 'c', dim=capture.dim)
    # copy_from_lb = coordtools.abs_point((-200, -200), 'c', dim=capture.dim)
    # from_points = list(copy_from_rt) + list(copy_from_lb)
    # copy_to_rt = coordtools.abs_point((0, 0), 'tr', dim=capture.dim)
    # copy_to_lb = coordtools.abs_point((-500, -500), 'tr', dim=capture.dim)
    # to_points = list(copy_to_rt) + list(copy_to_lb)
    #
    #
    # rf, tf, lf, bf = from_points
    # rt, tt, lt, bt = to_points




    while True:
        _, frame = capture.read()
        # frame_from = frame[tf:bf, lf:rf]
        # frame_to = frame[tt:bt, lt:rt]
        # frame_to[:] = cv2.resize(frame_from, frame_to.shape[:2][::-1])

        shapefunctions.copy_frame_portion_to(frame,
                                             (0,0, 100, 100),
                                             (0, 0, 300, 300),
                                             source_format='cwh',
                                             destination_format='rtwh',
                                             source_ref='c',
                                             destination_ref='rt',
                                             )
        capture.show()

        if cvtools.cv2waitkey() == True:
            break

    capture.stop()
    sys.exit()
