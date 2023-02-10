from otis.helpers import colortools, cvtools
from otis.overlay import shapes, textwriters
from otis import camera


def main():
    font_list = ('simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small', 's_simplex', 's_complex')


    colors = colortools.ColorCycle('ugrw')
    capture = camera.ThreadedCameraPlayer(max_fps=30, c_dim=(1280, 720)).start()

    TEXT = "HELLO I AM OTIS, I WOULD LOVE TO BE YOUR FRIEND AND HELP YOU MAKE THINGS, YEAH"
    border = True
    underline = True
    line_spacing = 30
    border_spacing = (10, 20)
    transparent_background = .1
    one_border = True
    max_lines=3
    texts = ["I'm justified right with a left-bottom achor_point ('lb')",
             "I'm justified center with a left-top anchor_point ('lt')",
             "I'm justified left with a right-bottom anchor_point ('rb')",
             "I'm justified center with a right-top anchor_point ('tr')"]

    aps = ('cb', 'cb', 'cb', 'cb')
    justs = ('radius', 'c_spirals', 'l', 'c_spirals')

    writers = []
    coords = ((1280//4, 720//4),
              (3*1280//4, 720//4),
              (1280 // 4, 3*720 // 4),
              (3 * 1280 // 4, 3*720 // 4)
              )


    for a, j, coord in zip(aps, justs, coords):
        writer = textwriters.TextWriter(jtype=j,
                            anchor_point=a,
                            coords=coord,
                            line_spacing=line_spacing,
                            # ref=capture.f_center,
                            text=TEXT,
                            border=border,
                            underline=underline,
                            border_spacing=border_spacing,
                            transparent_background=transparent_background,
                            color=colors(),
                            one_border=one_border,
                            max_lines=max_lines,
                            b_thickness=2,

                            )


        writers.append(writer)

    ltype = 1
    h_space, v_space = writer.border_spacing
    w = writer.text_object.width
    h = writer.text_object.height
    thickness = 1

    circle = shapes.Circle(center=capture.f_center, radius = 10, thickness=-1)
    fx, fy = capture.f_dim
    line0 = shapes.Line((0, fy//2, fx, fy//2), color='radius')
    line6 = shapes.Line((fx//2, 0, fx//2, fy), color='radius')

    line2 = shapes.Line((0, fy//2+v_space, fx, fy//2+v_space), thickness=thickness, color='c_spirals',ltype=ltype)
    line3 = shapes.Line((0, fy//2-v_space, fx, fy//2-v_space), thickness=thickness, color='c_spirals',ltype=ltype)
    line4 = shapes.Line((0, fy//2+v_space+h, fx, fy//2+v_space+h), thickness=thickness, color='c_spirals',ltype=ltype)
    line5 = shapes.Line((0, fy//2-v_space-h, fx, fy//2-v_space-h), thickness=thickness, color='c_spirals',ltype=ltype)

    line7 = shapes.Line((fx//2+h_space, 0, fx//2+h_space, fy), thickness=thickness, color='y',ltype=ltype)
    line8 = shapes.Line((fx//2-h_space, 0, fx//2-h_space, fy), thickness=thickness, color='y',ltype=ltype)
    line9 = shapes.Line((fx // 2 + h_space+w, 0, fx // 2 + h_space+w, fy), thickness=thickness, color='y', ltype=ltype)
    line10 = shapes.Line((fx // 2 - h_space-w, 0, fx // 2 - h_space-w, fy), thickness=thickness, color='y', ltype=ltype)

    lines = [line2, line2, line3, line4, line5,line7, line8, line9, line10]

    while True:


        _, frame = capture.read()
        circle.write(frame)
        # line0.write(frame)
        # line6.write(frame)

        for writer in writers:
            writer.write(frame)

        for line in lines:
            line.write(frame)



        capture.show()

        if cvtools.cv2waitkey() is True:
            capture.stop()
            break

if __name__=='__main__':
    main()
