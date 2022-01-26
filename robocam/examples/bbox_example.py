import multiprocessing as multi
import signal
import ctypes
import sys
import time

import cv2
import numpy as np

import robocam.camera as camera

from robocam.helpers.multitools import close_gracefully, ProcessDataSharer
from robocam.overlay.textwriters import FPSWriter, TypeWriter

D_SHAPE = (1920, 1080)
CF = 2

def camera_process(shared_data_object):
    #make sure process closes when ctrl+c
    signal.signal(signal.SIGTERM, close_gracefully)
    signal.signal(signal.SIGINT, close_gracefully)
    #start camera
    cam = camera.CameraPlayer(dim=D_SHAPE)
    #shorten shared name
    shared = shared_data_object
    #set up writers
    fps_writer = FPSWriter((10, int(cam.dim[1] - 90)))
    m_time_write = TypeWriter((10, int(cam.dim[1] - 60)))
    #specify write function so that shared.m_time can be updated
    m_time_write.text_function = lambda : f'model time = {shared.m_time.value} ms'

    while True:
        #get frame
        cam.read()
        shared.frame[:]=cam.frame #write to share
        #make bbox
        t, r, b, l = shared.bbox
        cv2.rectangle(cam.frame, (l, t), (r, b), (0, 255, 0), 2)
        #write other stuff
        fps_writer.write(cam.frame)
        m_time_write.write_fun(cam.frame)
        #render
        cam.show()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.stop()
    sys.exit()

def cv_model_process(shared_data_object):
    import face_recognition

    signal.signal(signal.SIGTERM, close_gracefully)
    signal.signal(signal.SIGINT, close_gracefully)

    shared = shared_data_object

    while True:

        tick = time.time()
        small_frame = cv2.resize(shared.frame, (0, 0), fx=1 / CF, fy=1 / CF)[:, :, ::-1]
        new_bbox = face_recognition.face_locations(small_frame, model='cnn')
        shared.m_time.value = int(1/(time.time() - tick))

        if new_bbox:
            new_bbox = [b * CF for b in new_bbox[0]]
            np.copyto(shared.bbox, new_bbox)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    sys.exit()


def main():

    shared = ProcessDataSharer()
    shared.add_value('m_time', 'i', 0)
    shared.add_array('frame', ctypes.c_uint8, (D_SHAPE[1], D_SHAPE[0], 3))
    shared.add_array('bbox', ctypes.c_int64, 4)

    show_process = multi.Process(target=camera_process, args=(shared,))
    find_process = multi.Process(target=cv_model_process, args=(shared,))

    show_process.start()
    find_process.start()

    show_process.join()
    find_process.join()


if __name__ == '__main__':
    main()
