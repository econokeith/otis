import cv2
import numpy as np
import abc
from otis.helpers import coordtools, misc, maths, colortools
from otis.overlay import bases, shapes, textwriters
from otis.overlay.shapes import shapefunctions
from otis.overlay.bases import CircleType, RectangleType, LineType


class CircleWithLineToCenter(shapes.Circle):

    def __init__(self,
                 *args,
                 thickness=2,
                 ltc_thickness=2,
                 **kwargs
                 ):
        """
        it's a circle with a line to the center
        Args:
            *args:
            thickness:
            ltc_thickness:
            **kwargs:
        """

        super().__init__(*args,
                         thickness=thickness,
                         **kwargs
                         )

        self.line_to_center = shapes.Line(color='c',
                                          thickness=ltc_thickness,
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
        frame_center = dim[0] // 2, dim[1] // 2
        dist_to_center = maths.linear_distance(frame_center, self.center)

        _color = 'g'

        if dist_to_center > self.radius:
            _color = 'r'

            # line to center
            self.line_to_center.write(frame, coords=tuple(self.center) + frame_center)

            # small circles on frame and box centers
            self.small_circle.write(frame, center=self.center, color='r')
            self.small_circle.write(frame, center=frame_center, color='r')

            # little up/down lines on the tiny circles
            self.cross_lines.write(frame, (*frame_center, 90, 20))
            self.cross_lines.write(frame, (*frame_center, 0, 20))
            self.cross_lines.write(frame, (*self.center, 90, 20))
            self.cross_lines.write(frame, (*self.center, 0, 20))

            # longer lines across the bounding circle
            self.cross_lines.write(frame, (*self.center, 45, 2 * self.radius * 1.1))
            self.cross_lines.write(frame, (*self.center, -45, 2 * self.radius * 1.1))

        # print bounding circle
        super().write(frame, color=_color)


class ServoFaceTracker(shapes.Circle):

    def __init__(self,
                 *args,
                 thickness=2,
                 ltc_thickness=1,
                 **kwargs
                 ):
        """
        it's a circle with a line to the center
        Args:
            *args:
            thickness:
            ltc_thickness:
            **kwargs:
        """

        super().__init__(*args,
                         thickness=thickness,
                         **kwargs
                         )

        self.line_to_center = shapes.Line(color='c',
                                          thickness=1,
                                          coord_format='points',
                                          ltype=cv2.LINE_AA
                                          )

        self.cross_lines = shapes.Line(color='b',
                                       thickness=1,
                                       coord_format='cal',
                                       ltype=cv2.LINE_AA
                                       )

        self.cross_lines2 = shapes.Line(color='w',
                                        thickness=1,
                                        coord_format='cal',
                                        ltype=cv2.LINE_AA
                                        )

        self.up_down_lines = shapes.Line(color='b',
                                         thickness=1,
                                         ltype=cv2.LINE_AA
                                         )

        self.small_circle = shapes.Circle(color='b',
                                          radius=5,
                                          thickness=-1,
                                          ltype=cv2.LINE_AA
                                          )

        self.small_circle_nf = shapes.Circle(color='b',
                                             radius=3,
                                             thickness=1,
                                             ltype=cv2.LINE_AA
                                             )

        self.small_circle_nf2 = shapes.Circle(color='b',
                                              radius=15,
                                              thickness=1,
                                              ltype=cv2.LINE_AA
                                              )

        self.x_error = 0
        self.y_error = 0
        SCALE = 1

        self.vert_color = colortools.color_function('r')
        self.hor_color = colortools.color_function('g')
        self.diag_color = colortools.color_function('u')

        self.x_error_writer = textwriters.InfoWriter(text_fun=lambda x: f"{x}",
                                                     color=self.hor_color,
                                                     ref='c',
                                                     ltype=cv2.LINE_AA,
                                                     border=True,
                                                     scale=SCALE,
                                                     background=True,
                                                     transparent_background=True,
                                                     border_spacing=(.3, .5),
                                                     )

        self.y_error_writer = textwriters.InfoWriter(text_fun=lambda x: f"{x}",
                                                     color=self.vert_color,
                                                     ref='c',
                                                     ltype=cv2.LINE_AA,
                                                     scale=SCALE,
                                                     border=True,
                                                     background=True,
                                                     back_color='w',
                                                     border_spacing=(.3, .5),
                                                     transparent_background=True,
                                                     )

    def write(self, frame, *args, **kwargs):

        dim = frame.shape[:2][::-1]
        frame_center = dim[0] // 2, dim[1] // 2
        dist_to_center = maths.linear_distance(frame_center, self.center)

        center = self.center

        vert_point = frame_center[0], center[1]
        hor_point = center[0], frame_center[1]

        self.x_error = frame_center[0] - center[0]
        self.y_error = center[1] - frame_center[1]
        CROSS_COLOR = 'w'
        CIRCLE_COLOR = 'g'
        ARROW_THICKNESS = 2
        if dist_to_center > self.radius:
            CIRCLE_COLOR = 'c'

        super().write(frame, color=CIRCLE_COLOR)

        if dist_to_center > self.radius:

            self.up_down_lines.thickness = 2
            self.up_down_lines.write(frame, (center[0], 0, center[0], dim[1]), color=CROSS_COLOR)
            self.up_down_lines.write(frame, (0, center[1], dim[0], center[1]), color=CROSS_COLOR)
            self.up_down_lines.thickness = 1
            self.up_down_lines.write(frame, (center[0], 0, center[0], dim[1]), color='b')
            self.up_down_lines.write(frame, (0, center[1], dim[0], center[1]), color='b')
            self.cross_lines.write(frame, (*self.center, 0, 2.05 * self.radius))
            self.cross_lines.write(frame, (*self.center, 90, 2.05 * self.radius))


            # line to center
            # small circles on frame and box centers
            self.small_circle_nf2.write(frame, center=self.center)

            # little up/down lines on the tiny circles

            self.cross_lines.write(frame, (*self.center, 90, 20))
            self.cross_lines.write(frame, (*self.center, 0, 20))

            # #############################################

            self.small_circle_nf2.write(frame, center=self.center)
            self.cross_lines.write(frame, (*self.center, 90, self.small_circle_nf2.radius * 2.1))
            self.cross_lines.write(frame, (*self.center, 0, self.small_circle_nf2.radius * 2.1))

            self.up_down_lines.write(frame, (*self.center, *vert_point), color='w')
            self.up_down_lines.write(frame, (*self.center, *hor_point), color='w')

            self.cross_lines.write(frame, (*frame_center, 90, self.small_circle_nf2.radius * 2.1))
            self.cross_lines.write(frame, (*frame_center, 0, self.small_circle_nf2.radius * 2.1))

            # self.small_circle_nf2.write(frame, center=frame_center)

            cv2.arrowedLine(frame, frame_center, vert_point, self.vert_color, ARROW_THICKNESS, tipLength=.05,
                            line_type=cv2.LINE_AA)
            cv2.arrowedLine(frame, frame_center, hor_point, self.hor_color, ARROW_THICKNESS, tipLength=.05,
                            line_type=cv2.LINE_AA)
            cv2.arrowedLine(frame, frame_center, center,self.diag_color, ARROW_THICKNESS, tipLength=.05,
                            line_type=cv2.LINE_AA)

            self.small_circle_nf2.write(frame, center=frame_center)

            self.small_circle_nf.write(frame, center=vert_point, color='b')
            self.small_circle_nf.write(frame, center=hor_point, color='b')
            self.small_circle_nf.write(frame, center=center, color='b')

            self.small_circle.write(frame, center=frame_center, color='r')
            self.cross_lines.write(frame, (*frame_center, 90, 20))
            self.cross_lines.write(frame, (*frame_center, 0, 20))

            if self.y_error > 0:
                self.x_error_writer.anchor_point = 'cb'
                self.x_error_writer.coords = (0, 25)

            else:
                self.x_error_writer.anchor_point = 'ct'
                self.x_error_writer.coords = (0,-25)

            self.x_error_writer.write(frame, -self.x_error)

            if self.x_error < 0:
                self.y_error_writer.anchor_point = 'cr'
                self.y_error_writer.coords = (-20,0)

            else:
                self.y_error_writer.anchor_point = 'cl'
                self.y_error_writer.coords = (20 ,0 )

            self.y_error_writer.write(frame, -self.y_error)


        # print bounding circle


if __name__ == '__main__':

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
