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

__fonts = (cv2.FONT_HERSHEY_SIMPLEX,
          cv2.FONT_HERSHEY_PLAIN,
          cv2.FONT_HERSHEY_DUPLEX,
          cv2.FONT_HERSHEY_COMPLEX,
          cv2.FONT_HERSHEY_TRIPLEX,
          cv2.FONT_HERSHEY_COMPLEX_SMALL,
          cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
          cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
          )

__keys = ('simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small','s_simplex', 's_complex')

TEXT_HASH = dict(zip(__keys, __fonts))
