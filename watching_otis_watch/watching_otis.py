import cv2
import mediapipe as mp

from mediapipe_default_changes import get_default_pose_landmarks_style, draw_pose_landmarks

def main():
    mp_drawing = mp.solutions.drawing_utils
    mp_drawing_styles = mp.solutions.drawing_styles
    mp_pose = mp.solutions.pose

    mp_face_mesh = mp.solutions.face_mesh
    face_drawing_spec = mp_drawing.DrawingSpec(thickness=1, circle_radius=0, color=(0, 255, 0))
    face_style = mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=1)

    cap = cv2.VideoCapture(0)
    pose = mp_pose.Pose(min_detection_confidence=0.5,
                        min_tracking_confidence=0.5
                        )

    face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1,
                                      refine_landmarks=True,
                                      min_detection_confidence=0.5,
                                      min_tracking_confidence=0.5
                                      )

    while cap.isOpened():
        success, image = cap.read()
        if not success:
            print("Ignoring empty camera frame.")
            # If loading a video, use 'break' instead of 'continue'.
            continue
        # To improve performance, optionally mark the frame as not writeable to
        image.flags.writeable = False
        image = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        pose_results = pose.process(image)
        face_results = face_mesh.process(image)
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        image.flags.writeable = True

        draw_pose_landmarks(image=image,
                            landmark_list=pose_results.pose_landmarks,
                            connections=mp_pose.POSE_CONNECTIONS,
                            landmark_drawing_spec=get_default_pose_landmarks_style()
                            )

        if face_results.multi_face_landmarks:
            for face_landmarks in face_results.multi_face_landmarks:
                mp_drawing.draw_landmarks(image=image,
                                          landmark_list=face_landmarks,
                                          connections=mp_face_mesh.FACEMESH_TESSELATION,
                                          landmark_drawing_spec=face_drawing_spec,
                                          connection_drawing_spec=face_style
                                          )

        cv2.imshow('MediaPipe Pose', image)

        if cv2.waitKey(5) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


