import argparse


def make_parser():
    parser = argparse.ArgumentParser(description='options for this otis project')
    parser.add_argument('-d', '--c_dim',type=tuple, default=(1280, 720),
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
                 parser:argparse.ArgumentParser=None,
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

