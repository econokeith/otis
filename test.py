import argparse


parser = argparse.ArgumentParser(description='Example of the TypeWriter screen object')
parser.add_argument('--dim',type=tuple, required=False, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('--max_fps', type=int, required=False, default=30, 
                    help='set max fps Default is 30')
parser.add_argument('--cam',type=bool, required=False, default=False,
                    help='USE_WEBCAM = True or False. Default is False')

parser.parse_args()

if __name__=='__main__':
    print(parser.dim)
    print(parser.max_fps)
    print(parser.cam)