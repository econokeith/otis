import argparse
import os
from queue import Queue

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.overlay.colortools as ctools
import robocam.overlay.textwriters as writers

parser = argparse.ArgumentParser(description='Example of the TypeWriter screen object')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=60, help='set max fps Default is 30')
parser.add_argument('-c','--cam',type=bool, default=False,
                    help='USE_WEBCAM = True or False. Default is False')
parser.add_argument('-s','--script',type=str,  default='guy_debord.txt',
                    help='location_of_script.txt, defaults to ')

args = parser.parse_args()

def main():

    abs_dir = os.path.dirname(os.path.abspath(__file__))
    script_address = os.path.join(abs_dir, args.script)
    with open(script_address, 'r') as f:
        _script = f.read().split('\n')

    # try:
    #     with open(args.script,'r') as f:
    #         _script = f.read().split('\n')
    # except:
    #     with open('robocam/otismeetsguysdebord/text_files/' +args.script,'r') as f:
    #         _script = f.read().split('\n')

    script = Queue()
    pauses = Queue()
    for string in _script:
        pause, line = string.split(' ', 1)
        script.put(line)
        pauses.put(float(pause))

    video_width, video_height = args.dim

    if args.cam is True:
        capture = camera.CameraPlayer(dim=(video_width, video_height))
        capture.max_fps = args.max_fps
    else:
        frame = np.empty((video_height, video_width, 3), dtype='uint8')

    fps_writer = writers.FPSWriter((10, 60), scale=2, ltype=2, color='r')
    speaker = writers.TypeWriter((10, 400), scale=2, ltype=2, key_wait=(.02, .08), end_pause=1.5, color='g')
    color_counter = ctools.UpDownCounter(step=1, maxi=100)
    imshow_sleeper = timers.SmartSleeper(1 / args.max_fps)

    while True:
        if args.cam is True:
            grabbed, frame = capture.read()
            if grabbed is False:
                break
            #frame[:, :, :] += color_counter()
        else:
            frame[:, :, :] = color_counter()

        if speaker.stub_complete and not script.empty():
            speaker.line = script.get()
            speaker.end_timer.wait = pauses.get()

        speaker.type_line(frame)
        fps_writer.write(frame)
        if args.cam is False:
            imshow_sleeper()
        cv2.imshow('test', frame)
        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:
            break

    if args.cam is True:
        capture.release()
    cv2.destroyAllWindows()

if __name__=='__main__':
    main()