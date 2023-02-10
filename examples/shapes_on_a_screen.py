import cv2

from otis import camera
from otis.overlay import shapes

def main():
    # start the camera
    capture = camera.ThreadedCameraPlayer(c_dim='720p')
    # make shapes
    circle = shapes.Circle(center=(0, 0),
                           radius=100,
                           color = 'u',
                           ref = 'c_spirals', # relative to center
                           thickness=-1
                           )

    line = shapes.Line(coords=(1280,0, 0, 720), # (x0, y0, x1, y1)
                       thickness=2
                       )

    rectangle = shapes.Rectangle(coords=(400, 400, 100, 100), # (cx, cy, w, h)
                                 coord_format='cwh',
                                 color='g',
                                 thickness=-1
                                 )

    circle_with_line_to_center = shapes.CircleWithLineToCenter(center=(1000, 600), radius=100)

    shape_list = [circle,
                  line,
                  rectangle,
                  circle_with_line_to_center,
                  ]
    ################################ the loop ############################################
    while True:

        _, frame = capture.read() # get newest frame
        # write shapes on to frame
        for shape in shape_list:
            shape.write(frame)
        #show the frameq
        capture.show()
        # break if you hit 'q' on the keyboard
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    capture.stop()

if __name__=='__main__':
    main()

