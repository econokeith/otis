"""
test the camera
"""
import robocam.camera as camera
import argparse

parser = argparse.ArgumentParser(description='Test For Camera Capture')
parser.add_argument('-d','--dim',type=tuple, default=(1280, 720),
                    help='set video dimensions. default is (1280, 720)')
parser.add_argument('-m','--max_fps', type=int, default=300, help='set max fps Default is 30')
parser.add_argument('-p', '--port', type=int, default=0, help='camera port default is 0')


args = parser.parse_args()

if __name__=='__main__':
    capture = camera.CameraPlayer(src=args.port, dim=args.dim, max_fps=args.max_fps)
    capture.test(wait=True)