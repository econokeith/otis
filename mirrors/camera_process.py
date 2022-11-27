import signal
import sys
import cv2
import numpy as np

from otis import camera as camera
from otis.helpers import multitools, cvtools, coordtools
from otis.overlay import scenes, writergroups, shapes, boundingobjects, textwriters, imageassets
from otis.helpers import shapefunctions, timers

pie_path = 'photo_asset_files/pie_asset'
MAX_KEYS_PER_SECOND = 10


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)

    manager = scenes.SceneManager(shared, pargs, file=__file__)
    manager.capture.silent_sleep = False
    # boxes = scenes.BoundingManager(manager)
    boxes = boundingobjects.BoundingManager(manager)
    info_group = writergroups.BasicInfoGroup((10, 40), manager)
    capture = manager.capture
    mirror = MirrorEffects(manager)

    n_faces_writer = textwriters.InfoWriter(text_fun=lambda: f'n_faces= {shared.n_observed_faces.value}',
                                            coords=(50, 200))
    active_faces_writer = textwriters.InfoWriter(text_fun=lambda: f'a_faces= {boxes.active_names}',
                                                 coords=(50, 250))
    p_target_writer = textwriters.InfoWriter(text_fun=lambda: f'primary= {boxes.primary_target}',
                                             coords=(50, 300))
    servo_target_writer = textwriters.InfoWriter(text_fun=lambda: f'target = {shared.servo_target}',
                                                 coords=(50, 350))
    keyboard_writer = textwriters.InfoWriter(text_fun=lambda: f'primary= {shared.keyboard_input.value}',
                                                 coords=(50, 400))

    show_info = True
    while True:

        check, frame = capture.read()
        shared.frame[:] = frame  # latest frame to shared frame
        frame_portion = coordtools.get_frame_portion(frame, (0, 0, 200, 200), ref='c')
        boxes.loop(frame)

        mirror.write(frame, frame_portion)


        if show_info is True:
            n_faces_writer.write(frame)
            active_faces_writer.write(frame)
            info_group.write(frame)
            p_target_writer.write(frame)
            servo_target_writer.write(frame)
            keyboard_writer.write(frame)

        capture.show(frame)
        keyboard_input = cv2.waitKey(1) & 0xFF

        if shared.new_keyboard_input.value is False and keyboard_input != 255:

            shared.keyboard_input.value = keyboard_input
            shared.new_keyboard_input.value = True

            if shared.keyboard_input.value == ord('q'):
                break

            elif shared.keyboard_input.value == ord('1'):
                show_info = not show_info

            shared.key_input_received[0] = True

        if np.count_nonzero(shared.key_input_received) == 3:
            shared.new_keyboard_input.value = False
            shared.key_input_received[:] = False

    capture.stop()
    sys.exit()

#######################################################################################################################
#######################################################################################################################
#######################################################################################################################

class MirrorEffects:

    def __init__(self,
                 manager
                 ):

        self.manager = manager
        self.shared = manager.shared
        self.pargs = manager.pargs
        self.image_writers = []
        self.image_writer = imageassets.AssetWithImage(copy_updates=True)
        self.sizes = [(300, 300)]

    def write(self, frame, image):

        image_writer = self.image_writer
        image_writer.resize_to = size = (300, 300)
        self.image_writer.image = image

        os = 20
        corners = ('rt', 'lb', 'lt', 'rb')
        offsets = ((-os, -os), (os, os), (os, -os), (-os, os))

        for corner, offset in zip(corners, offsets):
            image_writer.write(frame,
                               coords=(*offset,*size),
                               ref=corner,
                               in_format=corner+'wh')






