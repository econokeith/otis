import cv2
import numpy as np
from robocam.helpers.timers import TimedCycle


if __name__=='__main__':

    frame = np.zeros((720, 1080, 3), dtype='uint8')

    tcycle = TimedCycle(updown=True, cycle_t = 2)

    while True:

        frame[:, :, :] = 0
        frame[:, :, (0,1,2)] = tcycle()
        
        cv2.imshow('test', frame)

        if cv2.waitKey(1)&0xFF == ord('q'):
            break

    cv2.waitKey(1)
    cv2.destroyAllWindows()
    cv2.waitKey(1)
