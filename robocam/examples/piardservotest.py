"""
Example of putting BBoxes around faces
"""

import multiprocessing as multi
import signal
import ctypes
import sys
import time
import argparse

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.multitools as mtools
import robocam.overlay.textwriters as writers
import robocam.helpers.timers as timers
import robocam.overlay.assets as assets
import robocam.servos.pid as pid
import _piardservo as servo



parser = argparse.ArgumentParser(description='Test For Camera Capture')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=300, help='set max fps Default is 300')
parser.add_argument('-p', '--port', type=int, default=0, help='camera port default is 0')
parser.add_argument('-cf', type=float, default=2, help='shrink the frame by a factor of cf before running algo')
parser.add_argument('--faces', type=int, default=5, help='max number of bboxs to render. default =5')
parser.add_argument('--device', type=str, default='gpu', help='runs a hog if cpu and cnn if gpu')
parser.add_argument('--ncpu', type=int, default='1', help='number of cpus')
parser.add_argument('-scale', type=float, default=2., help='scale output')

args = parser.parse_args()

video_center = np.array(args.dim)
video_center //= 2


def camera_process(shared_data_object):
    #make sure process closes when ctrl+c
    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)
    #start camera
    capture = camera.CameraPlayer(dim=args.dim, )
    #shorten shared name
    shared = shared_data_object
    #set up writers
    fps_writer = writers.FPSWriter((10, int(capture.dim[1] - 40)))
    m_time_write = writers.TypeWriter((10, int(capture.dim[1] - 120)))
    #specify write function so that shared.m_time can be updated
    m_time_write.text_fun = lambda : f'model compute time = {shared.m_time.value} ms'
    n_face_writer = writers.TypeWriter((10, int(capture.dim[1] - 80)))
    n_face_writer.text_fun = lambda : f'{shared.n_faces.value} face(s) detected'

    CrossHairs = []
    for i in range(args.faces):
        crosshair = assets.CrossHair()
        crosshair.coords = shared.bbox_coords[i, :] # reference a line in teh shared array
        CrossHairs.append(crosshair)

    while True:
        #get frame
        capture.read()
        shared.frame[:]=capture.frame #write to share
        #make bbox
        for i in range(shared.n_faces.value):
            CrossHairs[i].write(capture.frame)
        #write other stuff
        n_face_writer.write_fun(capture.frame)
        fps_writer.write(capture.frame)
        m_time_write.write_fun(capture.frame)
        #render
        capture.show(warn=True, scale=1.8)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()
    sys.exit()

def cv_model_process(shared_data_object):
    #import locally to avoid GPU conflicts
    import face_recognition

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)

    shared = shared_data_object
    model = 'cnn' if args.device == 'gpu' else 'hog'

    while True:

        tick = time.time()
        # compress and convert from
        small_frame = cv2.resize(shared.frame, (0, 0), fx=1/args.cf, fy=1/args.cf)[:, :, ::-1]
        new_boxes = face_recognition.face_locations(small_frame, model=model)
        shared.m_time.value = int(1000*(time.time() - tick))
        #write new bbox lcoations to shared array
        shared.n_faces.value = len(new_boxes)

        if shared.n_faces.value > 0:

            for i in range(shared.n_faces.value):
                np.copyto(shared.bbox_coords[i,:], new_boxes[i])
            shared.bbox_coords *= args.cf

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    sys.exit()

def servo_process(shared_data_object):

    signal.signal(signal.SIGTERM, mtools.close_gracefully)
    signal.signal(signal.SIGINT, mtools.close_gracefully)
    shared = shared_data_object

    rpi = servo.RPiWifi(address='192.168.1.28', pins=(22, 17))
    Servos = servo.ServoContainer(n=2, microcontroller=rpi).connect()

    Servos[0].value = -.1
    Servos[1].value = -.5

    xPID = pid.PIDController(.001, 0, .00001)
    yPID = pid.PIDController(.001, 0, .00001)
    servo_update_timer = timers.CallHzLimiter(1 / 5)
    target = np.array(video_center)
    last_coords = np.array(shared.bbox_coords[0,:])

    while True:
        if shared.n_faces.value > 0:
            break

    while True:
        if servo_update_timer() and np.all(shared.bbox_coords[0,:] != last_coords):
            t, r, b, l = shared.bbox_coords[0,:]
            target[0], target[1] = (r+l)//2, (b+t)//2
            error = target - video_center
            x_move = -xPID.update(error[0], sleep=0)
            y_move = yPID.update(error[1], sleep=0)

            Servos[0].value += x_move
            Servos[1].value += y_move


            last_coords = np.array(shared.bbox_coords[0,:])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    Servos.close()


def main():
    #set up shared data

    shared = mtools.SharedDataObject()
    shared.add_value('m_time', 'i', 0)
    shared.add_value('n_faces', 'i', 0)

    shared.add_array('frame', ctypes.c_uint8, (args.dim[1], args.dim[0], 3))
    shared.add_array('bbox_coords', ctypes.c_int64, (args.faces, 4))
    shared.add_value('error', ctypes.c_double, 2)

    #define Processes with shared data
    show_process = multi.Process(target=camera_process, args=(shared,))
    find_process = multi.Process(target=cv_model_process, args=(shared,))
    move_process = multi.Process(target=servo_process, args=(shared,))

    show_process.start()
    find_process.start()
    move_process.start()

    show_process.join()
    find_process.join()
    move_process.join()
    sys.exit()


if __name__ == '__main__':
    main()
