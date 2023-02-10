import queue
import signal
import sys
import time
import cv2
import numpy as np
import os

#requires mediapipe
import mediapipe as mp

from otis.helpers import timers
from otis.overlay import textwriters

folder_location = "/home/keith/Dropbox/otis_films/otis_introduces_himself/"
filename = "otis_intro_video.mp4"
script_name = "intro_script"

FPS = 30
DIM = (1080, 1080)
RECORD = False
MAX_I = 80
MIN_I = 15
CYCLE_T = 1.6
s_wait = 1.5

def main():
    with open(os.path.join(folder_location, script_name), "radius") as file:
        lines = [line.rstrip('\n').strip() for line in file.readlines()]

    waits = [s_wait, s_wait, s_wait, s_wait, 2, 1, 1, 3]
    SCRIPT = [(line, wait) for line, wait in zip(lines, waits)]

    sleeper = timers.SmartSleeper(1 / FPS)
    frame = np.zeros((*DIM, 3), dtype="uint8")

    if RECORD is True:
        recorder = cv2.VideoWriter(os.path.join(folder_location, filename),
                                   cv2.VideoWriter_fourcc(*'mp4v'),
                                   FPS,
                                   DIM
                                   )

    counter = timers.TimedCycle(min_i=MIN_I,
                                max_i=MAX_I,
                                direction=1,
                                cycle_t=CYCLE_T,
                                max_ups=FPS,
                                repeat=True,
                                updown=True,
                                end_value=None
                                )

    otis = textwriters.TypeWriter(coords=(0, 20),
                                  ref='cb',
                                  jtype='l',
                                  anchor_point='cb',
                                  scale=1.5,
                                  max_line_length=DIM[0] - 100,
                                  one_border=True,
                                  thickness=2,
                                  border_spacing=(.5, .5),
                                  max_lines=4,
                                  loop=False,
                                  color='g',
                                  transparent_background=.1,
                                  perma_border=True,
                                  key_wait_range=(.045, .0451)
                                  )

    the_script = queue.Queue()

    for line in SCRIPT:
        the_script.put(line)

    ############################################ Face Mesh ###################################################

    mp_drawing = mp.solutions.drawing_utils
    mp_face_mesh = mp.solutions.face_mesh
    drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=0, color=(0, 255, 0))
    style = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)

    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                      refine_landmarks=True,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5
                                      )

    ############################################ While Loop ##################################################

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, DIM[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, DIM[1])
    i = -1
    tick = 0
    while True:

        _, image = cap.read()
        image = image[:, 420:1500, :]
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image)

        frame[:, :, :] = counter()

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=frame,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=style
                )

        frame = cv2.flip(frame, 1)

        if otis.text_complete is True and the_script.empty() is False:
            tock = time.time()
            print(tock - tick - waits[i])
            i += 1
            tick = tock
            new_line = the_script.get()
            otis.text = new_line

        otis.write(frame)
        cv2.imshow('otis', frame)

        if RECORD is True:
            recorder.write(frame)

        sleeper()

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if otis.text_complete is True and the_script.empty() is True and RECORD is True:
            print(time.time() - tick - waits[i])
            break

    if RECORD is True:
        recorder.release()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
