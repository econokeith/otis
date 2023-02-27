import cv2
import numpy as np
from otis.cvtools.mediapipe.facemesh_utils import FACEMESH_TESSELATION
from otis.helpers import misc
from otis.helpers.timers import SmartSleeper
from otis.rotations.rigidbody import RigidBody3D


class MediaPipe3d(RigidBody3D):

    def __init__(self,
                 points=None,
                 dim = (1920, 1080),
                 hide = False,
                 **kwargs):

        _points = np.load(points)
        # if points is None:
        #     _points = np.zeros((468, 3), dtype=int)
        # elif isinstance(points, np.ndarray):
        #     assert points.shape == (468, 3)
        #     _points = points
        # elif isinstance(points, str):
        #     _points = np.load(str)
            
        super().__init__(points=_points, **kwargs)

        self.hide = hide
        self.connections = FACEMESH_TESSELATION
        self.dim = misc.dimensions_function(dim)
        self._VISIBILITY_THRESHOLD = .5
        self._PRESENCE_THRESHOLD = .5
        self.included = set(range(468))

        self.update_array = np.zeros(self._points.shape, dtype=float)

    def update_from_results(self, results):
        list_landmarks = results.landmark
        self.included = set()
        image_width = self.dim[0]
        image_height = self.dim[1]

        for i, landmark in enumerate(list_landmarks):

            if landmark.HasField('visibility') and landmark.visibility < self._VISIBILITY_THRESHOLD:
                continue
            if landmark.HasField('presence') and landmark.presence < self._PRESENCE_THRESHOLD:
                continue

            self.included.add(i)
            self.update_array[i, 0] = landmark.x
            self.update_array[i, 1] = landmark.y
            self.update_array[i, 2] = landmark.z

        self.points[:, 0] = np.minimum(self.update_array[:, 0] * image_width, image_width - 1)
        self.points[:, 1] = np.minimum(self.update_array[:, 1] * image_height, image_height - 1)
        self.points[:, 2] = np.minimum(self.update_array[:, 2] * image_width, image_width - 1)

        self.original = self.points.copy()

    def write_connections(self, frame):
        for i, connection in enumerate(self.connections):
            start_i = connection[0]
            end_i = connection[1]

            if start_i in self.included and end_i in self.included:
                if self.hide is True and (self._points[start_i, 2]>0 and self._points[end_i, 2]>0):
                    continue

                cv2.line(frame,
                         self._points[start_i, :2],
                         self._points[end_i, :2],
                         self.e_color,
                         self.e_thickness,
                         self.ltype
                         )

    def write_nodes(self, frame):
        for i, point in enumerate(self._points):
            if i in self.included:
                cv2.circle(frame,
                           self.points[i, :2],
                           self.n_radius,
                           self.n_color,
                           self.n_thickness,
                           self.ltype
                           )

class MeshFace(MediaPipe3d):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xc0_landmarks = (234, 454)
        self.xc1_landmarks = (93, 323)
        self.yc_landmarks = (10, 152)
        self.reference_point = (0,0)
        self.center_y_line = (0,0)
        self.center_x0_line = (0,0)
        self.center_x1_line = (0,0)

    def find_rotation_point(self):
        xc00, xc01 = self.xc0_landmarks
        xc10, xc11 = self.xc1_landmarks
        yc0, yc1 = self.yc_landmarks
        xy_pixels = self._points
        self.center_y_line = ((xy_pixels[yc0] + xy_pixels[yc1]) // 2).astype(int)
        self.center_x0_line = ((xy_pixels[xc00] + xy_pixels[xc01]) // 2).astype(int)
        self.center_x1_line = ((xy_pixels[xc11] + xy_pixels[xc10]) // 2).astype(int)
        self.reference_point = (self.center_x1_line + self.center_x0_line) // 2

        self._origin[:] = self.reference_point
        return self.reference_point

    def update_from_results(self, results):
        super().update_from_results(results)
        self.find_rotation_point()

    def move_xy(self, new_xy):
        xy_old = self.origin[:2]
        self._points[:,:2] -= xy_old - new_xy
        self.original = self._points.copy()
        self.origin[:2] = new_xy




def main():
    import otis.camera as camera
    import mediapipe as mp

    mp_face_mesh = mp.solutions.face_mesh
    capture = camera.CameraPlayer(f_dim=(1080, 1080), c_dim=(1920, 1080), max_fps=10)

    mesh_finder = mp_face_mesh.FaceMesh(max_num_faces=1,
                                        refine_landmarks=False,
                                        min_detection_confidence=0.5,
                                        min_tracking_confidence=0.5
                                        )

    mesh_face = MeshFace(dim=(1080, 1080), hide=True)
    i = 0
    j = 0
    while True:
        success, frame = capture.read()
        if success is False:
            continue
        face_results = mesh_finder.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        face_results

        if face_results.multi_face_landmarks:
            mesh_face.update_from_results(face_results.multi_face_landmarks[0])
            mesh_face.resize(2)

            mesh_face.write_connections(frame)
            i+=1
            if i % 15 == 0:
                np.save(f'mesh_face_{j}.npy', mesh_face.points)
                print(f'saved # {j}')
                j+=1

        capture.show()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()

def main1():
    import os
    file_name = 'static_forms/mesh_face/mesh_face_0.npy'
    file_name = os.path.join(os.path.dirname(__file__), file_name)

    PERIOD = 3
    frame = np.zeros((1080, 1080, 3), dtype='uint8')
    mesh_face = MeshFace(points=file_name,
                         dim=(1080, 1080),
                         fps=30,
                         periods=(0, PERIOD, 0),
                         y_range = (-np.pi/4, np.pi/4),
                         hide=True,

                         )

    mesh_face.find_rotation_point()
    mesh_face.move_xy((540, 540))

    mesh_face1 = MeshFace(points=file_name,
                         dim=(1080, 1080),
                         fps=30,
                         periods=(0, PERIOD, 0),
                         y_range = (-np.pi/4, np.pi/4),
                         hide=True,

                         )

    mesh_face1.find_rotation_point()
    mesh_face1.move_xy((540, 540))
    mesh_face1.rotate_by(y=np.pi/2)
    mesh_face1.update_original()

    sleeper = SmartSleeper(1/30)

    while True:
        frame[:,:,:] = 0
        mesh_face.periodic_rotate()
        mesh_face.write_connections(frame)

        mesh_face1.periodic_rotate()
        mesh_face1.write_connections(frame)

        cv2.imshow("", frame)
        sleeper()
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__=='__main__':
    main1()










