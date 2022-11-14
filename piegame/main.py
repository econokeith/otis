"""
Example of putting BBoxes around faces
"""
import multiprocessing as multi
import ctypes
import sys
import argparse

import numpy as np

import robocam.helpers.multitools as mtools
from piegame import servo_process
from piegame import cv_model_process
from piegame import camera_process


def make_parser():
    parser = argparse.ArgumentParser(description='Try to avoid the Camera Bot Shooting You')
    parser.add_argument('-d', '--dim',type=tuple, default=(1280, 720),
                        help='set video dimensions. default is (1920, 1080)')
    parser.add_argument('-m', '--max_fps', type=int, default=60,
                        help='set max fps Default is 60')
    parser.add_argument('-p', '--port', type=int, default=0,
                        help='camera port default is 0')
    parser.add_argument('-cf', type=float, default=2,
                        help='shrink the frame by a factor of cf before running algo')
    parser.add_argument('--faces', type=int, default=5,
                        help='max number of bboxs to render. default =5')
    parser.add_argument('--device', type=str, default='gpu',
                        help='runs a hog if cpu and cnn if gpu')
    parser.add_argument('--ncpu', type=int, default='1',
                        help='number of cpus')
    parser.add_argument('--servo', type=bool, default=False,
                        help='use servos')
    parser.add_argument('-s', '--scale', type=float, default=1.5)
    parser.add_argument('-cv', type=bool, default=False)
    return parser


parser = make_parser()
args = parser.parse_args()
args.video_center = np.array(args.dim)//2


def main():
    # set up shared data
    shared_data_object = mtools.SharedDataObject()
    # add shared values
    shared_data_object.add_value('m_time', 'd', .1)
    shared_data_object.add_value('n_faces', 'i', 0)
    shared_data_object.add_value('primary', 'i', 0)
    shared_data_object.add_value('new_overlay', ctypes.c_bool, True)
    shared_data_object.add_value('scene', 'i', 0)
    # add shared arrays
    shared_data_object.add_array('frame', ctypes.c_uint8, (args.dim[1], args.dim[0], 3)) #dims are backwards cause numpy
    shared_data_object.add_array('bbox_coords', ctypes.c_int64, (args.faces, 4))         #is reversed
    shared_data_object.add_array('error', ctypes.c_double, 2)
    shared_data_object.add_array('names', ctypes.c_uint8, args.faces)
    #define Processes with shared data
    process_modules = [camera_process, cv_model_process]
    #if servos are true, add it to the process list
    if args.servo is True:
        process_modules.append(servo_process)

    processes = []
    # each process module should have a primary function called 'target'
    for module in process_modules:
        process = multi.Process(target=module.target,
                                args=(shared_data_object, args))
        processes.append(process)
    # start
    for process in processes:
        process.start()
    # join processes
    for process in processes:
        process.join()
    # exit on break key
    sys.exit()

if __name__ == '__main__':
    main()
