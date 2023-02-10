import cv2

from otis.helpers import coordtools

__fonts = (cv2.FONT_HERSHEY_SIMPLEX,
           cv2.FONT_HERSHEY_PLAIN,
           cv2.FONT_HERSHEY_DUPLEX,
           cv2.FONT_HERSHEY_COMPLEX,
           cv2.FONT_HERSHEY_TRIPLEX,
           cv2.FONT_HERSHEY_COMPLEX_SMALL,
           cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
           cv2.FONT_HERSHEY_SCRIPT_COMPLEX,
           )

__keys = ('simplex', 'plain', 'duplex', 'complex', 'triplex', 'c_small', 's_simplex', 's_complex')

FONT_HASH = dict(zip(__keys + __fonts, __fonts + __fonts))

def get_text_size(text, font='simplex', scale=1, thickness=None):
    _font = FONT_HASH[font]
    return cv2.getTextSize(text, _font, scale, thickness)[0]

def find_justified_start(text, coords, font, scale=1, thickness=1, jtype='l', ref=None, dim=None):
    """
    finds the cv2 begin_at position for writing justified text
    Args:
        text:
        coords:
        _font:
        scale:
        thickness:
        jtype: justification type = 'l', 'radius', or 'c_spirals'

    Returns:

    """
    _font = FONT_HASH[font]

    w, h = cv2.getTextSize(text, _font, scale, thickness)[0]
    if jtype == 'radius':
        justified_start =  (int(coords[0] - w), coords[1])

    elif jtype == 'c_spirals':
        justified_start = (int(coords[0] - w / 2), coords[1])
    else:
        justified_start = coords

    return coordtools.absolute_point(justified_start, ref, dim)

def split_text_into_stubs(text,
                          max_line_length=None,
                          n_lines=None,
                          line_length_format='pixels',
                          font=None,
                          scale=1,
                          thickness=1,
                          ):

    if text is None:
        lines_of_text = []

    elif n_lines is None and max_line_length is None:
        lines_of_text = [text]

    elif max_line_length is None and n_lines is not None:
        lines_of_text = split_text_into_n_pieces(text, n_lines)

    elif (max_line_length is not None) and (line_length_format == 'pixels') and (font is not None):
        lines_of_text = split_text_into_lines_pixels(text, font, max_line_length, scale, thickness, n_lines)

    elif max_line_length is not None and (line_length_format == 'chars' or font is None):
        lines_of_text = split_text_into_lines_chars(text, max_line_length, n_lines)

    else:
        lines_of_text = []

    # return [line.strip() for line in lines_of_text]
    return lines_of_text


def split_text_into_lines_pixels(text, font=None, max_pixels_per_line=None, scale=1, thickness=None, max_lines=None):
    """
    breaks text into lines whose length is less than or equal to max_pixels_per line
    Args:
        text: str
            text string to be broken

        font: str
            'simplex', 'plain', 'duplex', 'complex',
            'triplex', 'c_small', 's_simplex', 's_complex'

        max_pixels_per_line: positive int

        scale:
        thickness:

    Returns:
        list of lines

    """

    if max_pixels_per_line is None:
        return [text]

    _font = FONT_HASH[font]

    text_length = cv2.getTextSize(text, _font, scale, thickness)[0][0]
    lines_of_text = []

    while text_length > max_pixels_per_line:

        split_position = int(max_pixels_per_line / text_length * len(text))
        split_proposal = text[:split_position + 1]
        # break at last space in the shortened line
        for i in range(split_position + 1):
            if split_proposal[-1 - i] == ' ':
                break
        line = split_proposal[:split_position - i]

        if line == '':
            raise RuntimeError("max_pixels_per_line is too small relative to character size. "
                               "There are individual words in the text that are longer "
                               "than the specified maximum number of pixels per line")

        lines_of_text.append(line)
        text = text[split_position - i:].strip(' ')
        text_length = cv2.getTextSize(text, _font, scale, thickness)[0][0]

    lines_of_text.append(text)
    if max_lines is not None and len(lines_of_text) > max_lines:
        last_line = " " + " ".join(lines_of_text[max_lines - 1:])
        lines_of_text = lines_of_text[:max_lines-1].append(last_line)

    return lines_of_text

def split_text_into_lines_chars(text, max_character_per_line=None, max_lines=None):
    """
    breaks text into lines <= in length to max_pixels_per_line
    Args:
        text: text string
        _font:
        scale:
        ltype:
        max_pixels_per_line: in pixels

    Returns:
        list of lines of text
    """
    if max_character_per_line is None:
        return [text]

    text_length = len(text)
    lines_of_text = []

    while text_length > max_character_per_line:

        split_position = max_character_per_line
        split_proposal = text[:split_position + 1]
        # break at last space in the shortened line
        for i in range(split_position + 1):
            if split_proposal[-1 - i] == ' ':
                break

        line = split_proposal[:split_position - i]
        lines_of_text.append(line)
        text = text[split_position - i:].strip(' ')
        text_length = len(text)

    lines_of_text.append(text)
    if max_lines is not None and len(lines_of_text) > max_lines:

        last_line = " " + " ".join(lines_of_text[max_lines - 1:])
        lines_of_text = lines_of_text[:max_lines-1] + [last_line]

    return lines_of_text

def split_text_into_n_pieces(text, n_lines, buffer=0):

    lines = split_text_into_lines_chars(text, len(text)//n_lines+buffer)

    if len(lines) > n_lines:
        lines = split_text_into_n_pieces(text, n_lines, buffer+1)

    return lines


if __name__ == '__main__':
    text = 'hello, my name is george'
    lines = split_text_into_lines_chars(text, 6, 3)
    print(lines)
    print(split_text_into_n_pieces(text, 3))



