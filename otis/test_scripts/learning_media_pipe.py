import cv2
import mediapipe as mp
import time
from collections import deque
import numpy as np
from otis import camera

last_10 = deque(maxlen=10)

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

dim = (1080, 1080)
drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0,255,0))
style = mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, dim[0])
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, dim[1])

tick = time.time()
black_screen = np.zeros((1080, 1080, 3), dtype='uint8')
BLACK_SCREEN = True

with mp_face_mesh.FaceMesh(

        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:

    while True:
        success, image = cap.read()
        image = image[:,420:1500,:]
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(image)
        # Draw the face mesh annotations on the image.
        image.flags.writeable = True
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        if BLACK_SCREEN is True:
            image[:,:,:]=0
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=style
                )
        #                 mp_drawing.draw_landmarks(
        #                     image=image,
        #                     landmark_list=face_landmarks,
        #                     connections=mp_face_mesh.FACEMESH_CONTOURS,
        #                     landmark_drawing_spec=None,
        #                     connection_drawing_spec=mp_drawing_styles
        #                     .get_default_face_mesh_contours_style())
        #                 mp_drawing.draw_landmarks(
        #                     image=image,
        #                     landmark_list=face_landmarks,
        #                     connections=mp_face_mesh.FACEMESH_IRISES,
        #                     landmark_drawing_spec=None,
        #                     connection_drawing_spec=mp_drawing_styles
        #                     .get_default_face_mesh_iris_connections_style())
        # Flip the image horizontally for a selfie-view display.

        image = cv2.flip(image, 1)
        tock = time.time()
        last_10.append(tock - tick)
        average_frequency = round(len(last_10) / sum(last_10))
        cv2.putText(image,
                    f'fps = {average_frequency}',
                    (100, 100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 1)
        tick = tock
        # cv2.resize(image, (0,0), fx=2, fy=2)

        cv2.imshow('hh', image)

        key_input = cv2.waitKey(1) & 0xFF
        if key_input == ord('1'):
            BLACK_SCREEN = not BLACK_SCREEN
        elif key_input == ord('q'):
            break
        else:
            pass

cap.release()
cv2.destroyAllWindows()