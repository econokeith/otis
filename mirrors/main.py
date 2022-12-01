"""
Example of putting BBoxes around faces
"""
import multiprocessing
import ctypes
import sys

import numpy as np

from otis.helpers import multitools, otistools
import camera_process, cv_model_process

parser = otistools.make_parser()
pargs = parser.parse_args()
pargs.crop_to = (720, 720)
pargs.f_dim = pargs.crop_to
pargs.video_center = np.array(pargs.crop_to) // 2
pargs.PATH_TO_FACES = './faces'
pargs.output_scale = 1.8
pargs.servo = True
pargs.cf = 2
pargs.max_fps = 30
pargs.record = False
pargs.record_scale = 1


if pargs.servo is True:
    try:
        import servo_process
        use_servo = True
    except:
        use_servo = False
        pargs.servo = False

def main():
    # set up shared data
    shared_data_object = multitools.SharedDataObject()
    # add shared values
    shared_data_object.add_value('model_update_time', 'd', .1)
    shared_data_object.add_value('n_observed_faces', 'i', 0)
    shared_data_object.add_value('n_boxes_active', 'i', 0)
    shared_data_object.add_value('primary_target', 'i', 0)
    shared_data_object.add_value('new_overlay', ctypes.c_bool, False)
    shared_data_object.add_value('scene', 'i', 0)
    shared_data_object.add_value('keyboard_input', 'i', 0)
    shared_data_object.add_value('new_keyboard_input', ctypes.c_bool, False)
    shared_data_object.add_value('servo_tracking', ctypes.c_bool, False)
    shared_data_object.add_array('key_input_receivedv', 'i', 0)

    # add shared arrays
    shared_data_object.add_array('frame', ctypes.c_uint8, (pargs.crop_to[1], pargs.crop_to[0], 3)) # dims are backwards cause numpy
    shared_data_object.add_array('bbox_coords', ctypes.c_int64, (pargs.faces, 4))         # is reversed
    shared_data_object.add_array('error', ctypes.c_double, 2)
    shared_data_object.add_array('observed_names', ctypes.c_uint8, pargs.faces)
    shared_data_object.add_array('servo_target', ctypes.c_uint64, 2)
    shared_data_object.add_array('servo_position', ctypes.c_double, 2)
    shared_data_object.add_array('key_input_received', ctypes.c_bool, 3)

    # define Processes with shared data
    process_modules = [cv_model_process, camera_process]
    # if servos are true, add it to the process list
    if use_servo is True:
        process_modules.append(servo_process)

    processes = []
    # each process module should have a primary_target function called 'target'
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
