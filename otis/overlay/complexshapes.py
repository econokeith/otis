import cv2
import numpy as np
import abc
from otis.helpers import shapefunctions, coordtools, misc, maths
from otis.overlay import bases, shapes
from otis.overlay.bases import CircleType, RectangleType, LineType

class CircleWithLineToCenter(shapes.Circle):

    def __init__(self, *args,
                 thickness=2,
                 threshold=1,
                 **kwargs):

        super().__init__(*args,
                         thickness=thickness,
                         **kwargs
                         )

        self.threshold = threshold
        self.line_to_center = shapes.Line(color='c',
                                          thickness=2,
                                          coord_format='points'
                                          )

        self.cross_lines = shapes.Line(color='b',
                                       thickness=1,
                                       coord_format='cal'
                                       )

        self.small_circle = shapes.Circle(color='b',
                                          radius=5,
                                          thickness=-1
                                          )

    def write(self, frame, *args, **kwargs):

        dim = frame.shape[:2][::-1]
        frame_center = dim[0]//2, dim[1]//2
        dist_to_center = maths.linear_distance(frame_center, self.center)

        _color = 'g'

        if dist_to_center > self.radius * self.threshold:
            _color = 'r'

            # line to center
            self.line_to_center.write(frame, coords= tuple(self.center) + frame_center)

            self.small_circle.write(frame, center=self.center, color='r')
            self.small_circle.write(frame, center=frame_center, color='r')

            self.cross_lines.write(frame, (*frame_center, 90, 20))
            self.cross_lines.write(frame, (*frame_center, 0, 20))

            self.cross_lines.write(frame, (*self.center, 45, 2 * self.radius * 1.1))
            self.cross_lines.write(frame, (*self.center, -45, 2 * self.radius * 1.1))

            self.cross_lines.write(frame, (*self.center, 90, 20))
            self.cross_lines.write(frame, (*self.center, 0, 20))

        super().write(frame, color=_color)


if __name__=='__main__':

    frame = np.ones((800, 800, 3), dtype='uint8') * 255
    circle0 = CircleWithLineToCenter(center=(250, 200), radius=75)
    circle1 = CircleWithLineToCenter(center=(420, 420), radius=75)
    while True:
        frame[:, :, :] = 255
        circle0.write(frame)
        circle1.write(frame)
        cv2.imshow('thing', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
