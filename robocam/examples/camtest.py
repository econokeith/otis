"""
test the camera
"""
import argparse

import robocam.camera as camera

parser = argparse.ArgumentParser(description='Test For Camera Capture')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=300, help='set max fps Default is 30')
parser.add_argument('-p', '--port', type=int, default=0, help='camera port default is 0')

args = parser.parse_args()

def main(port=0, dim=(1280, 720), max_fps=60):
    capture = camera.CameraPlayer(src=port, dim=dim, max_fps=max_fps)
    capture.test(wait=True, warn=True)

if __name__=='__main__':
    main(args.port, args.dim, args.max_fps)
