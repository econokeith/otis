import signal
import sys
import cv2
import numpy as np

from otis import camera as camera
from otis.helpers import multitools, cvtools
from otis.overlay import scenes, writergroups, shapes, boundingobjects, textwriters
from otis.helpers import shapefunctions, timers

pie_path = 'photo_asset_files/pie_asset'
MAX_KEYS_PER_SECOND = 10


def target(shared, pargs):
    signal.signal(signal.SIGTERM, multitools.close_gracefully)
    signal.signal(signal.SIGINT, multitools.close_gracefully)


    manager = scenes.SceneManager(shared, pargs)
    manager.capture.silent_sleep = False
    # boxes = scenes.BoundingManager(manager)
    boxes = boundingobjects.BoundingManager(manager)
    info_group = writergroups.BasicInfoGroup((10, 40), manager)
    capture = manager.capture

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
        boxes.loop(frame)
        mirror_loop(frame)

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

        if shared.new_keyboard_input.value is True:

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





def mirror_loop(frame):
    square_dim = (200, 200)
    wide_dim = (200, 50)
    tall_dim = (50, 200)
    big_output_dim = (300, 300)
    dim = (1280, 720)

    n_littles = 1

    corners = ('rt', 'lb', 'lt', 'rb')
    os = 20
    ff = ((-os, -os), (os, os), (os, -os), (-os, os))
    for i, corner in enumerate(corners):
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (*ff[i], *big_output_dim),
                                             source_format='cwh',
                                             destination_format=corner + 'wh',
                                             source_ref='c',
                                             destination_ref=corner,
                                             )

    bw, bh = big_output_dim
    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (bw + i * w, 5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='lbwh',
                                             source_ref='c',
                                             destination_ref='lb',
                                             )
    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (-bw - i * w, 5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='rbwh',
                                             source_ref='c',
                                             destination_ref='rb',
                                             )

    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (-bw - i * w, -5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='rtwh',
                                             source_ref='c',
                                             destination_ref='rt',
                                             )

    for i in range(n_littles):
        w, h = wide_dim
        shapefunctions.copy_frame_portion_to(frame,
                                             (0, 0, *square_dim),
                                             (bw + i * w, -5, *wide_dim),
                                             source_format='cwh',
                                             destination_format='ltwh',
                                             source_ref='c',
                                             destination_ref='lt',
                                             )

    shapefunctions.copy_frame_portion_to(frame,
                                         (0, 0, *square_dim),
                                         (5, -210, *(50, 300)),
                                         source_format='cwh',
                                         destination_format='ltwh',
                                         source_ref='c',
                                         destination_ref='lt',
                                         )

    shapefunctions.copy_frame_portion_to(frame,
                                         (0, 0, *square_dim),
                                         (-5, -210, *(50, 300)),
                                         source_format='cwh',
                                         destination_format='rtwh',
                                         source_ref='c',
                                         destination_ref='rt',
                                         )



pass
