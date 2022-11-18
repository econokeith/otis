import cv2


def find_justified_start(text, pos, font, scale, ltype, jtype='l'):
    assert jtype in ['l', 'c', 'r']

    if jtype == 'l':
        return pos

    w, h = cv2.getTextSize(text, font, scale, ltype)[0]
    if jtype == 'c':
        return (int(pos[0]-w/2), pos[1])
    else:
        return (int(pos[0]-w), pos[1])
