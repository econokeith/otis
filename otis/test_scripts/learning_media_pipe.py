import cv2
import mediapipe as mp
import time
from collections import deque
import numpy as np

last_10 = deque(maxlen=10)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_face_mesh = mp.solutions.face_mesh

drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=1, color=(0, 255, 0))
style = mp_drawing.DrawingSpec(color=(0,255,0), thickness=1)
cap = cv2.VideoCapture(0)
tick = time.time()
black_screen = np.zeros((720, 1080, 3), dtype='uint8')

with mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as face_mesh:
    while cap.isOpened():
        success, image = cap.read()
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
        image[:,:,:]=0
        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                mp_drawing.draw_landmarks(
                    image=image,
                    landmark_list=face_landmarks,
                    connections=mp_face_mesh.FACEMESH_TESSELATION,
                    landmark_drawing_spec=drawing_spec,
                    connection_drawing_spec=style)
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

        cv2.imshow('MediaPipe Face Mesh', image)
        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()