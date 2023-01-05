from otis.helpers import colortools, cvtools
from otis.overlay import shapes, textwriters
from otis import camera


def main():

    colors = colortools.ColorCycle('ugrw')
    capture = camera.ThreadedCameraPlayer(max_fps=30,
                                          c_dim=(1280, 720),
                                          f_dim=(720, 400)).start()
    TEXT = "HELLO I AM OTIS, I WOULD LOVE TO BE YOUR FRIEND"
    anchor_points = ('lb', 'lt', 'rb', 'rt')
    justifications = ('r', 'c', 'l', 'c')

    writers = []
    for anchor, justi in zip(anchor_points, justifications):
        writer = textwriters.TextWriter(
                            scale=.7,
                            coords = (0,0),
                            jtype=justi,
                            anchor_point=anchor,
                            line_spacing=30,
                            ref=capture.f_center,
                            text=TEXT,
                            border=True,
                            underline=True,
                            border_spacing=(10,5),
                            transparent_background=.1,
                            color=colors(),
                            one_border=True,
                            max_lines=2,
                            b_thickness=2,
                            )


        writers.append(writer)

    ### # create lines to check if there are issues in border / line spacing ##############################
    h_space, v_space = writer.border_spacing
    w = writer.text_object.width
    h = writer.text_object.height
    thickness = 1
    ltype = 1

    circle = shapes.Circle(center=capture.f_center, radius = 10, thickness=-1)
    fx, fy = capture.f_dim


    line2 = shapes.Line((0, fy//2+v_space, fx, fy//2+v_space), thickness=thickness, color='c',ltype=ltype)
    line3 = shapes.Line((0, fy//2-v_space, fx, fy//2-v_space), thickness=thickness, color='c',ltype=ltype)
    line4 = shapes.Line((0, fy//2+v_space+h, fx, fy//2+v_space+h), thickness=thickness, color='c',ltype=ltype)
    line5 = shapes.Line((0, fy//2-v_space-h, fx, fy//2-v_space-h), thickness=thickness, color='c',ltype=ltype)

    line7 = shapes.Line((fx//2+h_space, 0, fx//2+h_space, fy), thickness=thickness, color='y',ltype=ltype)
    line8 = shapes.Line((fx//2-h_space, 0, fx//2-h_space, fy), thickness=thickness, color='y',ltype=ltype)
    line9 = shapes.Line((fx // 2 + h_space+w, 0, fx // 2 + h_space+w, fy), thickness=thickness, color='y', ltype=ltype)
    line10 = shapes.Line((fx // 2 - h_space-w, 0, fx // 2 - h_space-w, fy), thickness=thickness, color='y', ltype=ltype)

    lines = [line2, line3, line4, line5,line7, line8, line9, line10]

    ############## WHILE LOOP#############################################

    while True:
        # read camera frame
        _, frame = capture.read()
        # draw small center circle
        circle.write(frame)

        # write text
        for writer in writers:
            writer.write(frame)
        # write check lines
        for line in lines:
            line.write(frame)
        # show
        capture.show()
        # if q break
        if cvtools.cv2waitkey() is True:
            capture.stop()
            break

if __name__=='__main__':
    main()
