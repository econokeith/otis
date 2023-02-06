import cv2
import time
#import mediapipe
import numpy as np

frame = np.zeros((300, 300, 3), dtype='uint8')
while True:
    time.sleep(1/30)
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        print("you hit 'q'")
        break

print('finished!')