import argparse
from typing import Union, Tuple
import numpy as np

__COMMON_DIMENSIONS = {
    "480p": (640, 480),
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "1440p": (2560, 1440),
    "4k": (3840, 2160),
    None: None
}


def dimensions_function(dim: Union[str, Tuple[int, int]]) -> Tuple[int, int]:
    """
    convenience function for setting dimensions in CameraPlayer
    Args:
        dim: tuple[int, int] of the form (w, h) or string equal to one of '480p', '720p', '1080p, '1440p', '4k'
            the resolution of the screen in pixels
    Returns: tuple[int, int]
            (w, h) of the screen
    """
    if isinstance(dim, (tuple, list, np.ndarray)):
        return dim
    else:
        try:
            return __COMMON_DIMENSIONS[dim]
        except ValueError:
            raise ValueError(f"Dimensions {dim} not recognized. For string inputs, the dimensions must be one of "
                             f"'480p', '720p', '1440p' ,'1080p, '4k'")


def update_save_attributes_on_write(obj, local_dict, skip=2):
    """
    updates keyword arguments for writing and saved if saved=True
    will not work with functions that use **kwargs
    ===================== use it like =================================
    class AssetWriter:
        ...
        ...
        def write(self, frame, kw1=_kw1, kw2=_kw2, kw3=_kw3, saved=True):
            _kw1, _kw2, _kw3 = update...write(self, locals())
            ...
            ...

            ## this replaces the need to constantly write:
            _kw1 = self.kw1 if kw1 is none else kw1
    """
    variable_keys = list(local_dict.keys())
    output = []
    save_it = local_dict['save']

    for key in variable_keys[skip:-1]:
        value = local_dict[key]

        if value is not None:
            output.append(value)
            if save_it is True:
                obj.__setattribute__(key, value)
        else:
            output.append(obj.__getattribute__(key))

    return output


def update_save_keyword_attributes(self, local_dict, attributes=(), save=False):
    """
    if a keyword argument is None, it will output the classes value
    otherwise it will output the classes saved value
    will not update attributes found in generic **kwargs inputs
    Args:
        self: obj
            self from inside an object - see below
        local_dict: dict
            always locals()
        attributes: tuple of strings
            the list of string attribute names
        save: bool
            if true, will update self with keyword not equal to None
    Returns:
        tuple of values for the attributes in attributes

    note: all keyword values in method must be already defined attributes or properties of the object
    ===================== use it like =================================
    class AssetWriter:
        def __init__(self, *args, **kwargs):
            self.kw1 = ...
            self.kw2 = ...
            self.kw3 = ...
        ...
        ...
        def write(self, frame, kw1=_kw1, kw2=_kw2, kw3=_kw3, saved=True):
            _kw1, _kw2, _kw3 = update_save_keyword_attributes(self,
                                                              locals(),
                                                              attributes=('kw1', 'kw2', 'kw3'),
                                                              save=False,
                                                              )
            ...
            ...

            ## this replaces the need to constantly write:
            _kw1 = self.kw1 if kw1 is none else kw1

    """

    output = []
    # sometimes we don't care about saving or don't have save in the kwargs
    try:
        save_it = local_dict['save']
    except KeyError:
        save_it = False

    for key in attributes:
        # unsure the attribute is available from named keyword arguments
        try:
            value = local_dict[key]
        except KeyError:
            raise KeyError(f"keyword : '{key}' is not a named argument in this function") # should this be a value error

        if value is not None:
            output.append(value)
            # if we're saving, we're saving
            if save_it is True:
                self.__setattribute__(key, value)
        else:
            output.append(self.__getattribute__(key))

    return output


def int_or_float_or_tuple_to_tuple(value):
    """
    Args:
        value: int, float, tuple, list

    Returns:
        return (value, value) ... if value is a scalar
        return value ... if value has more than 1 dimension
    """
    if isinstance(value, (int, float)):
        return value, value
    else:
        return value


def make_parser():
    parser = argparse.ArgumentParser(description='options for this otis project')
    parser.add_argument('-d', '--c_dim', type=tuple, default=(1280, 720),
                        help='set video dimensions. default is (1920, 1080)')
    parser.add_argument('-m', '--max_fps', type=int, default=30,
                        help='set max show_fps Default is 60')
    parser.add_argument('-p', '--port', type=int, default=0,
                        help='camera port default is 0')
    parser.add_argument('-cf', type=float, default=2,
                        help='shrink the frame by a factor of cf before running algo')
    parser.add_argument('--faces', type=int, default=5,
                        help='max number of bboxs to render. default =5')
    parser.add_argument('--device', type=str, default='cpu',
                        help='runs a hog if cpu and cnn if gpu')
    parser.add_argument('--ncpu', type=int, default='1',
                        help='number of cpus')
    parser.add_argument('--servo', type=bool, default=True,
                        help='use servos')
    parser.add_argument('-os', '--output_scale', type=float, default=1.5)
    parser.add_argument('-rs', '--record_scale', type=float, default=.5)
    parser.add_argument('-rec', '--record', type=bool, default=False)
    parser.add_argument('-rec_to', '--record_to', type=str, default='cam.avi')
    parser.add_argument('-cv', type=bool, default=True)
    parser.add_argument('-path2f', '--path_to_faces', type=str, default='./faces')
    return parser


class ArgParser:

    def __init__(self,
                 parser: argparse.ArgumentParser = None,
                 description="this is an otis project",
                 **kwargs):
        if parser is None:
            parser = argparse.ArgumentParser(description=description, **kwargs)

        parser.add_argument('-d', '--c_dim', type=tuple, default=(1280, 720),
                            help='set video dimensions. default is (1280, 720)')
        parser.add_argument('-m', '--max_fps', type=int, default=30,
                            help='set max show_fps Default is 30')
        parser.add_argument('-p', '--port', type=int, default=0,
                            help='camera port default is 0')
        parser.add_argument('-cf', type=float, default=2,
                            help='shrink the frame by a factor of cf before running algo')
        parser.add_argument('--faces', type=int, default=5,
                            help='max number of bboxs to render. default =5')
        parser.add_argument('--device', type=str, default='cpu',
                            help='runs a hog if cpu and cnn if gpu')
        parser.add_argument('--ncpu', type=int, default='1',
                            help='number of cpus')
        parser.add_argument('--servo', type=bool, default=False,
                            help='use servos')
        parser.add_argument('-os', '--output_scale', type=float, default=1.5)
        parser.add_argument('-rs', '--record_scale', type=float, default=.5)
        parser.add_argument('-rec', '--record', type=bool, default=False)
        parser.add_argument('-rec_to', '--record_to', type=str, default='cam.avi')
        parser.add_argument('-cv', type=bool, default=True)
        parser.add_argument('-path2f', '--path_to_faces', type=str, default='./faces')

        self.parser = parser

    def add_argument(self, *args, **kwargs):
        self.parser.add_argument(*args, **kwargs)

    def parse_args(self):
        return self.parser.parse_args()


def crop_image_to_square(img):
    """
    crops a rectangular image into a square with sides equal to the length of the shortest side and
    the same center as the original image
    """
    y, x, _ = img.shape
    if x == y:
        return img

    elif x > y:

        x0 = (x - y) // 2
        x1 = y + x0
        return img[:, x0:x1]

    else:

        y0 = (y - x) // 2
        y1 = x + y0
        return img[y0:y1, :]
