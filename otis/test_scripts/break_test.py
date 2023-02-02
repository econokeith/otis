import cv2
import time
import mediapipe
print(mediapipe.__version__)
print(cv2.__version__)

capture = cv2.VideoCapture(0)

while True:
    success, frame = capture.read()
    if success is False:
        continue

    time.sleep(1/30)
    cv2.imshow("frame", frame)
    if cv2.waitKey(1) & 0xFF == 1:
        print("you hit 'q'")
        break

print('finished!')