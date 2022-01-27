"""
test the camera
"""
import argparse
import time

import cv2

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.textwriters as writers

parser = argparse.ArgumentParser(description='Test For Camera Capture')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=300, help='set max fps Default is 30')
parser.add_argument('-p', '--port', type=int, default=0, help='camera port default is 0')

args = parser.parse_args()

def main(port=0, dim=(1280, 720), max_fps=60):
    capture = camera.CameraPlayer(src=port, dim=dim)
    fps_counter = writers.FPSWriter((10, 40))
    show_time = writers.TextWriter((10, 100))
    show_time.text_function = lambda time: f'show time = {round(1/time)}'
    read_time = writers.TextWriter((10, 160))
    read_time.text_function = lambda time: f'read time = {round(1/time)}'
    stime = 1
    ftime2 = 1
    while True:
        rtick = time.time()
        capture.read()
        rtime = time.time() - rtick

        read_time.write_fun(capture.frame, rtime)
        fps_counter.write(capture.frame)
        show_time.write_fun(capture.frame, stime)
        tick = time.time()
        capture.show()
        stime = time.time() - tick
        ftime2 = time.time() - rtick

        if cv2.waitKey(1)&0xFF == ord('q'):
            break

    capture.stop()

if __name__=='__main__':
    main(args.port, args.dim, args.max_fps)
