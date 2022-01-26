import cv2
import numpy as np
import time
import imutils
import camera
import multiprocessing as multi
import signal
import ctypes
import sys

D_SHAPE = (1080, 1920, 3)

def signal_handler(sig, frame):
    # print a status message
    print("[INFO] You pressed `ctrl + c`! Exiting...")
    # exit
    sys.exit(0)


def camera_process(image_multi_array, bbox_multi_array, m_time):
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    cam = camera.CameraPlayer(dim=(1920, 1080))
    img_share = np.frombuffer(image_multi_array.get_obj(), 'uint8').reshape(D_SHAPE)
    bbox = np.frombuffer(bbox_multi_array.get_obj(), 'int64')

    while True:
        timer = cv2.getTickCount()
        cam.read()

        np.copyto(img_share, cam.frame)

        t, r, b, l = bbox
        cv2.rectangle(cam.frame, (l, t), (r, b), (0, 255, 0), 2)

        fps = cv2.getTickFrequency() / (cv2.getTickCount() - timer)

        cv2.putText(cam.frame, f'FPS = {int(fps)}', (10, int(cam.dim[1] - 90)), cam.font, .75, (0, 0, 255), 1)
        cv2.putText(cam.frame, f'm_time = {m_time.value}', (10, int(cam.dim[1] - 60)), cam.font, .75, (0, 0, 255), 1)
        cam.show()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.stop()
    sys.exit()


def detector_process(image_multi_array, bbox_multi_array, m_time):
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    import face_recognition
    share_data = np.frombuffer(image_multi_array.get_obj(), 'uint8').reshape(D_SHAPE)
    bbox = np.frombuffer(bbox_multi_array.get_obj(), 'int64')
    CF=2

    while True:

        tick = time.time()
        small_frame = cv2.resize(share_data, (0, 0), fx=1 / CF, fy=1 / CF)
        rgb_small_frame = small_frame[:, :, ::-1]
        new_bbox = face_recognition.face_locations(rgb_small_frame, model='cnn')
        m_time.value = int(1/(time.time() - tick))

        if new_bbox:
            new_bbox = [b * CF for b in new_bbox[0]]
            np.copyto(bbox, new_bbox)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    sys.exit()


def process_manager():
    m_time = multi.Value('i', 0)

    image_multi_array = multi.Array(ctypes.c_uint8, D_SHAPE[0] * D_SHAPE[1] * 3)
    bbox_multi_array = multi.Array(ctypes.c_int64, 4)

    show_process = multi.Process(target=camera_process,
                                 args=(image_multi_array, bbox_multi_array, m_time)
                                 )
    find_process = multi.Process(target=detector_process,
                                 args=(image_multi_array, bbox_multi_array, m_time)
                                 )

    show_process.start()
    find_process.start()

    show_process.join()
    find_process.join()



if __name__ == '__main__':
    process_manager()
