import ctypes
import multiprocessing
import sys

import cv2
import numpy as np

from otis import camera
from otis.helpers import multitools, cvtools, timers, coordtools
from otis.overlay import shapes, assetholders, imageassets

DIM = (1280, 720)
F_DIM = (720, 720)
MAX_FACES = 2
RECORD_TO = 'taylor_and_me.mp4'
MAX_FPS = 30
RECORD = False
CF = 2
MODEL = 'cnn'
PATH_TO_FACES = 'photo_assets/taylor_and_me/faces'

def main():
    # create shared data objects
    dynamic_shared_data = multitools.SharedDataObject()
    # new overlay tag
    dynamic_shared_data.add_value('new_overlay', ctypes.c_bool, False) # tells camera process when there is new data
    dynamic_shared_data.add_value('n_observed_faces', 'i', 0) # number of faces observed
    # shared data arrays
    dynamic_shared_data.add_array('box_coords', 'i', (MAX_FACES, 4)) # box coords
    dynamic_shared_data.add_array('observed_names', 'i', MAX_FACES) # index for names
    dynamic_shared_data.add_array('frame', ctypes.c_uint8, (*F_DIM[::-1], 3)) # shared frame
    # define Processes with shared data
    process_functions = [camera_display_process, computer_vision_process] # defined below

    processes = []

    for process in process_functions:
        process = multiprocessing.Process(target=process,
                                          args=(dynamic_shared_data,)
                                          )
        processes.append(process)
    # begin_at
    for process in processes:
        process.start()
    # join processes
    for process in processes:
        process.join()
    # exit on break key
    sys.exit()

def camera_display_process(shared):
    # start camera
    capture = camera.ThreadedCameraPlayer(0,
                                          c_dim= DIM,                 
                                          max_fps=MAX_FPS,
                                          flip=True,
                                          record=RECORD,
                                          record_to=RECORD_TO,
                                          f_dim=F_DIM,
                                          record_dim=F_DIM
                                          ).start()

    ### set up screen assets ##
    # define the frame asset that will fill one of the bounding boxes
    image_asset = imageassets.ImageAsset(border=True,
                                         b_color='radius',
                                         b_thickness=1)
    # define its bounder
    bounder_0 = assetholders.BoundingAsset(asset=image_asset,
                                           name='Keith',
                                           name_tag_border=True,
                                           moving_average=(3, 3, 10, 10)
                                           )
    # define a regular bounding box with a rectangle shape as its asset
    bounder_1 = assetholders.BoundingAsset(asset=shapes.Rectangle(),
                                           name='Taylor Swift',
                                           color='g',
                                           name_tag_border=True,
                                           )

    boxes = [bounder_0, bounder_1]
    n_faces = 0
    observed_names = []
    # start loop
    while True:
        # read from the camera feed
        _, frame = capture.read()
        # copy frame data to shared data
        shared.frame[:] = frame
        # if cv process has completed a loop, update the box data
        if shared.new_overlay.value is True:
            n_faces = shared.n_observed_faces.value
            observed_names = np.copy(shared.observed_names)
            
            for i in range(n_faces):
                boxes[observed_names[i]].coords = shared.box_coords[i]
            shared.new_overlay.value = False

        # if I am the only face, then display the portion of the frame that is already in my bounding box
        if n_faces == 1 and observed_names[0] == 0:
            frame_portion = coordtools.get_frame_portion(frame,
                                                         bounder_0.coords)
            bounder_0.asset.image = frame_portion
        # if there are two faces, copy/resize/paste taylors bounding box into mine
        elif n_faces == 2 and 0 in observed_names and 1 in observed_names:
           frame_portion = coordtools.get_frame_portion(frame, bounder_1.coords)
           bounder_0.asset.image = frame_portion
           bounder_0.asset.resize_to = bounder_0.coords[2:]

        else:
            pass

        # write bounders onto frame
        for i in observed_names[:n_faces]:
            boxes[i].write(frame)

        # display updated frame
        capture.show(frame)

        # break if q0
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()
    sys.exit()

def computer_vision_process(shared_data_object):
    import face_recognition

    shared = shared_data_object

    known_names, known_encodings = cvtools.load_face_data(face_recognition, PATH_TO_FACES, __file__)

    face_locator = timers.FunctionTimer(face_recognition.face_locations)
    frame_copy = np.zeros((*F_DIM[::-1], 3), dtype='uint8')

    while True:

        frame_copy[:, :, :] = np.array(shared.frame, copy=False)
        frame_copy = frame_copy[:, :, ::-1]
        compressed_frame = cvtools.resize(frame_copy, 1 / CF)

        observed_boxes = face_locator(compressed_frame, model=MODEL)
        observed_boxes = np.array(observed_boxes) * CF

        observed_encodings = face_recognition.face_encodings(frame_copy, observed_boxes, )
        n_faces = shared.n_observed_faces.value = len(observed_encodings)

        for i in range(n_faces):
            np.copyto(shared.box_coords[i, :], observed_boxes[i])
            face_distances = face_recognition.face_distance(known_encodings, observed_encodings[i])
            shared.observed_names[i] = np.argmin(face_distances)

        shared.new_overlay.value = True
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    sys.exit()

if __name__ == '__main__':
    main()
