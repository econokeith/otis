import multiprocessing
import ctypes
import sys

import numpy as np

import otis.helpers.misc
from otis.helpers import multitools
import camera_process, cv_model_process

class StaticArgs:
    pass

static_args = StaticArgs()
static_args.dim = (1280, 720)
static_args.max_faces = 2
static_args.record_to = 'keith_and_taylor.mp4'

def main():
    # create shared data objects
    dynamic_shared_data = multitools.SharedDataObject()
    # new overlay tag
    dynamic_shared_data.add_value('new_overlay', ctypes.c_bool, False)
    # shared data arrays
    dynamic_shared_data.add_array('bbox_coords', ctypes.c_int64, (static_args.max_faces, 4))
    dynamic_shared_data.add_array('frame', ctypes.c_uint8, (*static_args.dim[::-1], 3))

    # define Processes with shared data
    process_modules = [cv_model_process, camera_process]

    processes = []
    # each process module should have a primary_target function called 'target'
    for module in process_modules:
        process = multiprocessing.Process(target=module.target,
                                          args=(dynamic_shared_data, static_args)
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


if __name__ == '__main__':
    main()