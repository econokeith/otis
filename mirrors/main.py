"""
Example of putting BBoxes around faces
"""
import multiprocessing
import ctypes
import sys

import numpy as np

from otis.helpers import multitools, otistools
import mirror_camera, mirror_vision, mirror_servo

parser = otistools.make_parser()
pargs = parser.parse_args()
pargs.video_center = np.array(pargs.dim) // 2
pargs.PATH_TO_FACES = './faces'

if pargs.servo is True:
    pass

def main():
    # set up shared data
    shared_data_object = multitools.SharedDataObject()
    # add shared values
    shared_data_object.add_value('m_time', 'd', .1)
    shared_data_object.add_value('n_faces', 'i', 0)
    shared_data_object.add_value('primary', 'i', 0)
    shared_data_object.add_value('new_overlay', ctypes.c_bool, True)
    shared_data_object.add_value('scene', 'i', 0)
    # add shared arrays
    shared_data_object.add_array('frame', ctypes.c_uint8, (pargs.dim[1], pargs.dim[0], 3)) #dims are backwards cause numpy
    shared_data_object.add_array('bbox_coords', ctypes.c_int64, (pargs.faces, 4))         #is reversed
    shared_data_object.add_array('error', ctypes.c_double, 2)
    shared_data_object.add_array('names', ctypes.c_uint8, pargs.faces)
    # define Processes with shared data
    process_modules = [mirror_camera, mirror_vision]
    #if servos are true, add it to the process list
    if pargs.servo is True:
        process_modules.append(mirror_servo)

    processes = []
    # each process module should have a primary function called 'target'
    for module in process_modules:
        process = multiprocessing.Process(target=module.target,
                                          args=(shared_data_object, pargs)
                                          )
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
