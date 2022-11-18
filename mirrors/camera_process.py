import signal
import sys

from otis.helpers import multitools, cvtools
from otis.overlay import scenes, writergroups

pie_path = 'photo_asset_files/pie_asset'

def target(shared, pargs):

    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)

    manager = scenes.SceneManager(shared, pargs)
    boxes = scenes.BoundingManager(manager)
    info_group = writergroups.BasicInfoGroup((10, 40), manager)
    capture = manager.capture

    while True:

        check, frame = capture.read()
        shared.frame[:] = frame  # latest frame to shared frame
        boxes.loop(frame)
        info_group.write(frame)
        capture.show(frame)

        if cvtools.cv2waitkey() is True:
            break

    capture.stop()
    sys.exit()


#######################################################################################################################
#######################################################################################################################
#######################################################################################################################


