import cv2
import os
from otis.camera import CameraPlayer
from otis.helpers.timers import SmartSleeper

cap_size = (1080, 1080)
capture = CameraPlayer('bouncies.mp4',
                       c_dim=cap_size, # this has to be set with recorded video otherwise we get it won't save the file
                       max_fps=30,
                       record=True,
                       record_to='bounce720.mov',
                       record_dim=(720, 720)
                       )

while True:
    grabbed, frame = capture.read()
    if grabbed is True:
        capture.show()
    else:
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
# TODO - Camera.stop() isn't working for prerecorded video
capture.stop()