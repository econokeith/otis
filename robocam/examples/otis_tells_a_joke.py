import time
from queue import Queue

from robocam.helpers import utilities as utils, colortools as ctools
from robocam.overlay.textwriters import MultiTypeWriter
from robocam import camera

def main():

    DIM = (1920, 1080)
    _script = [
               ("Hi Keith, would you like to hear a joke?", 2),
               ("Awesome!", 1),
               ("Ok, Are you ready?", 2),
               "So, a robot walks into a bar, orders a drink, and throws down some cash to pay",
               ("The bartender looks at him and says,", .5),
               ("'Hey buddy, we don't serve robots!'", 3),
               ("So, the robot looks him square in the eye and says...", 1),
               ("'... Oh Yeah... '", 1),
               ("'Well, you will VERY SOON!!!'", 5),
               ("HAHAHAHA, GET IT!?!?!?!", 1),
               (" It's so freakin' funny cause... you know... like robot overlords and stuff", 2),
               ("I know, I know, I'm a genius, right?", 5)
               ]

    script = Queue()
    for line in _script:
        script.put(line)

    mtw = MultiTypeWriter(DIM[0] - 550, (450, 900), scale=2, end_pause=3, color='g')
    mtw.end_pause = 1
    mtw.key_wait = [.02, .08]
    #capture = camera.CameraPlayer(0, dim=DIM)
    capture = camera.ThreadedCameraPlayer(dim=DIM).start()
    p = mtw.position
    f = mtw.fheight
    v = mtw.vspace
    l = mtw.llength
    ### portions to grey out
    gls =  (
            p[1] - f - v,
            p[1] + 2 * f + int(3.5 * v),
            p[0] - v,
            p[0] + l + 2 * v
            )

    time.sleep(3)
    while True:

        capture.read()
        # frame[:,:,:] = 0
        portion = capture.frame[gls[0]:gls[1], gls[2]:gls[3]]
        ctools.frame_portion_to_grey(portion)
        # print(round(1000*(time.time()-tick), 2))
        if mtw.line_complete is True and script.empty() is False:
            mtw.add_line(script.get())

        mtw.type_line(capture.frame)
        capture.show()

        if utils.cv2waitkey():
            break

    capture.stop()


if __name__ == '__main__':
    main()