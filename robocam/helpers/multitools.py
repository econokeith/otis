"""
tools for using the multiprocessing python package
"""

import sys
import multiprocessing as multi
import numpy as np
import ctypes

def close_gracefully(sig, frame):
    """
    ensures child processes are closed when you ctrl+c
    :param sig:
    :param frame:
    :return:
    """
    # print a status message
    print("[INFO] You pressed `ctrl + c`! Exiting...")
    # exit
    sys.exit(0)


class SharedDataObject:

    _ctype_hash = {'uint8': ctypes.c_uint8,
                   'str': ctypes.c_wchar_p,
                   'd': ctypes.c_double}

    def __init__(self):
        """
        A container for shared data with multiprocessing.Process's
        DataShare object has no data attributes upon instantiation.
        Add shared arrays and values as follows:

        shared_data = DataShare()
        shared_data.add_array(array_name, c_type, dim)
        shared_data.add_value(value_name, c_type, value)

        shared arrays are accessed as np.frombuffer arrays
        and must be writen to using slicing i.e.

        shared_data.array_name[:] = some_np_array_of_the_same_size
        or
        np.copyto(shared_data.array_name, some_np_array_of_the_same_size)

        shared_values are type multiprocessing.Value(ctype, value) adn must be accessed for
        reading and writing using the .value method i.e.

        shared_data.value_name.value = 0
        and
        some_parameter = shared_data.value_name.value
        """
        pass

    def add_array(self, array_name, c_type, dim):
        if c_type in self._ctype_hash.keys():
            c_type = self._ctype_hash[c_type]

        l = np.product(dim)

        np_dtype = np.dtype(c_type).name
        new_array = multi.Array(c_type, int(l)).get_obj()
        new_array = np.frombuffer(new_array, dtype=np_dtype).reshape(dim)

        setattr(self, array_name, new_array)

    def add_value(self, value_name, c_type, value):
        new_value = multi.Value(c_type, value)

        setattr(self, value_name, new_value)


class LibraryImportProcess(multi.Process):

    def run(self):
        '''
        Method to be run in sub-process; can be overridden in sub-class
        '''
        ### add imports here
        if self._target:
            self._target(*self._args, **self._kwargs)