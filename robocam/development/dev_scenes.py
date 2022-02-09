import argparse

import cv2
import numpy as np

import robocam.camera as camera
import robocam.helpers.timers as timers
import robocam.helpers.colortools as ctools
import robocam.overlay.textwriters as writers

from queue import Queue

parser = argparse.ArgumentParser(description='Example of the TypeWriter screen object')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=24, help='set max fps Default is 30')
parser.add_argument('-c','--cam',type=bool, default=False,
                    help='USE_WEBCAM = True or False. Default is False')
parser.add_argument('-s','--script',type=str,  default='script.txt',
                    help='location_of_script.txt, defaults to ')

args = parser.parse_args()

try:
    with open(args.script, 'r') as f:
        _script = f.read().split('\n')
except:
    with open('robocam/development/' + args.script, 'r') as f:
        _script = f.read().split('\n')

TheScript = Queue()
for s in _script:
    TheScript.put(s)

video_width, video_height = args.dim

clock = timers.TimeSinceFirst(rnd=2)
clock_writer = writers.TextWriter((10, 60), scale=2, ltype=2, color='r').add_fun(lambda: f'{clock()}')
speaker = writers.TypeWriter((10, 200), scale=2, ltype=2, key_wait=(.02, .08), end_pause=1.5, color='g', ref='bl')

color_counter = ctools.UpDownCounter(step=1, maxi=100)
imshow_sleeper = timers.SmartSleeper(1 / args.max_fps)
frame = np.zeros((video_height, video_width, 3), dtype='uint8')

capture = camera.CameraPlayer(dim=(video_width, video_height), name='the script')
capture.max_fps = args.max_fps

def scene_0():

    frame = np.zeros((video_height, video_width, 3), dtype='uint8')
    speaker.add_lines([TheScript.get() for _ in range(2)])
    start_timer = timers.SinceFirstBool(5)
    end_timer = timers.SinceFirstBool(3)

    while True:
        frame[:,:,:] = 0
        if start_timer() is True:
            speaker.type_line(frame)

        clock_writer.write_fun(frame)
        imshow_sleeper()
        print('awake!')
        cv2.imshow('the script', frame)

        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:
            break

        if speaker.script.empty() and speaker.stub_complete:
            if end_timer() is True:
                break

def scene_1():

    speaker.add_lines([TheScript.get() for _ in range(3)])
    start_timer = timers.SinceFirstBool(3)
    end_timer = timers.SinceFirstBool(2)

    while True:
        frame[:, :, :] = color_counter()
        if start_timer() is True:
            speaker.type_line(frame)

        clock_writer.write_fun(frame)
        imshow_sleeper()
        cv2.imshow('the script', frame)

        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:
            break

        if speaker.is_done:
            if end_timer() is True:
                break

def scene_2():

    start_timer = timers.SinceFirstBool(3)
    end_timer = timers.SinceFirstBool(2)

    while TheScript.empty() is False:
        speaker.add_lines(TheScript.get())

    while True:
        capture.read()
        if start_timer() is True:
            speaker.type_line(capture.frame)
        clock_writer.write_fun(capture.frame)
        capture.show()

        if cv2.waitKey(1) & 0xFF in [ord('q'), ord('Q'), 27]:
            break

        if speaker.is_done is True and end_timer() is True:
            break

def main():
    scene_manager = Queue()

    for scene in [scene_0, scene_1, scene_2]:
        scene_manager.put(scene)

    while scene_manager.empty() is False:
        next_scene = scene_manager.get()
        next_scene()

    capture.stop()

if __name__=='__main__':
    main()