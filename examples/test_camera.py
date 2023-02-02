from otis.camera import ThreadedCameraPlayer, CameraPlayer
import cv2

if __name__=='__main__':
    capture = ThreadedCameraPlayer(4, flip=False, max_fps=30, c_dim='720p', f_dim=(720, 720))
    while True:
        success, frame = capture.read()
        if not success:
            continue

        capture.show()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break