"""

"""
import multiprocessing
import ctypes
import sys

import numpy as np

import otis.helpers.misc
from otis.helpers import multitools
import camera_process, cv_model_process

# using a parser was a bad idea and needs to be changed to something easier
parser = otis.helpers.misc.make_parser()
pargs = parser.parse_args()
pargs.c_dim = (1920, 1080)
pargs.crop_to = (1080, 1080)
pargs.f_dim = pargs.crop_to
pargs.video_center = np.array(pargs.crop_to) // 2
pargs.PATH_TO_FACES = './faces'
pargs.output_scale = 1
pargs.servo = True
pargs.cf = 2 # computer vision compression factor
pargs.max_fps = 30
pargs.record = True
pargs.record_dim= (1080, 1080)
pargs.record_to = 'keith_meets_otis_1.mov'
pargs.servo_address = '192.168.1.115'
pargs.servo_pins = (22, 17)

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
    shared_data_object.add_value('key_input_received', 'i', 0)

    # add shared arrays
    shared_data_object.add_array('frame', ctypes.c_uint8, (pargs.crop_to[1], pargs.crop_to[0], 3)) # dims are backwards
    shared_data_object.add_array('bbox_coords', ctypes.c_int64, (pargs.faces, 4))
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
