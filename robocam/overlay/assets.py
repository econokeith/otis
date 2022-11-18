import copy
import abc

import cv2
import numpy as np



import robocam.helpers.cvtools as cvtools
import robocam.helpers.timers as timers
from robocam.overlay import bases, textwriters#, shapeobjects
from robocam.helpers import shapefunctions
from robocam.overlay.shapes import Line
from robocam.overlay.textwriters import TextWriter, NameTag


class AssetBase(abc.ABC):
    name_tagger: NameTag
    shape = None

    def __init__(self,
                 coords=None,
                 name=None,
                 name_tagger = None,
                 use_name_tag = False,
                 use_bbox_coords = True, #t, r, b, l  or cy, cx, r/h. w
                 ):

    ############################## DEFINING COORD SYSTEM #######################################
        if coords == None:
            self.coords = np.zeros(4, dtype=int)

        elif isinstance(coords, (list, tuple, np.ndarray)) & len(coords) == 4:
            self.coords = np.array(coords)

        else:
            raise ValueError("box_coords must be list, tuple, nparray of length 4")

        self.use_bbox_coords = use_bbox_coords

        self._center = (100, 100)

        if use_bbox_coords:
            self._set_center_from_coords()
        else:
            self._center = self.coords[:2]



    ################################ NAME TAGGING ############################################

        self.name = name
        self.use_name_tag = use_name_tag

        if name_tagger is None:
            self.name_tagger = NameTag(name=name)
        else:
            assert isinstance(name_tagger, NameTag)
            self.name_tagger = copy.deepcopy(name_tagger)

    ##########################################################################################
    @property
    def center(self):

        if self.use_bbox_coords is True:
            self._set_center_from_coords()

        return self._center

    @center.setter
    def center(self, new_center):

        if self.use_bbox_coords is True:
            dif = np.array(new_center) - self.center
            self.coords[0] += dif[0]
            self.coords[2] += dif[0]
            self.coords[1] += dif[1]
            self.coords[3] += dif[1]

        else:
            self.coords[:2] = new_center

    @property
    def diagonal(self):
        return np.sqrt(self.height**2 + self.width**2)

    @property
    def height(self):
        return self.coords[2] - self.coords[0]

    @property
    def width(self):
        return self.coords[1] - self.coords[3]

    def _set_center_from_coords(self):
        t, r, b, l = self.coords
        return (r + l) // 2, (t + b) // 2


class BoundingBox(bases.Writer):
    shape = "rectangle"
    name_writer: TextWriter
    name: str

    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 font_scale=1,  # font scale,
                 thickness=2,
                 ltype=1,# line type
                 show_me = True,
                 name = "",
                 show_name = True,
                 name_line = True,
                 threshold = 0, #stabilizer threshold
                 ):

        super().__init__()

        self._coords = np.zeros(4, dtype=int) ### stored as top, right, bottom, left
        self.old_coords = self._coords.copy()
        self.color = color
        self.thickness = thickness
        self.font_scale = font_scale
        self.ltype = ltype
        self.name_writer = textwriters.TextWriter(scale=font_scale, ltype=ltype)
        self.name = name
        self.show_name = show_name
        self.name_line = name_line
        self.show_me = show_me
        self.threshold = threshold
        self.constant = None # None or (w, h)
        self.last_update_timer = timers.TimeSinceLast()

    @property
    def center(self):
        t, r, b, l = self.coords
        return int((r+l)/2), int((t+b)/2)

    @property
    def coords(self):
        if self.constant is not None:
            w, h = self.constant
            c = self.center

            t = c[1] + h/2
            b = c[1] - h/2
            l = c[0] - w/2
            r = c[0] + w/2

            return np.array([t, r, b, l])

        else:
            return self._coords

    # note that this setter just writes to the saved numpy array.
    @coords.setter
    def coords(self, new_coords):
        self.old_coords[:] = self._coords
        self._coords[:] = cvtools.box_stabilizer(self._coords, new_coords, threshold=self.threshold)


    @property
    def diagonal(self):
        return np.sqrt(self.height**2 + self.width**2)

    @property
    def height(self):
        return self.coords[2] - self.coords[0]

    @property
    def width(self):
        return self.coords[1] - self.coords[3]

    def update_coords(self, new_coords):
        self.old_coords[:] = self._coords
        self._coords[:] = cvtools.box_stabilizer(self._coords, new_coords, threshold=self.threshold)

    def distance_from_center(self, point):
        """
        :param point:
        :return: distance between center and point
        """
        c = self.center
        return np.sqrt((c[0]-point[0])**2 + (c[1]-point[1])**2)

    def write(self, frame, name=None):
        if self.show_me is False:
            return

        t, r, b, l = self.coords
        cv2.rectangle(frame, (l, t), (r, b), self.color, self.thickness)
        _name = name if name is not None else self.name
        if self.show_name is True and (_name is not None):
            self.name_tag(frame, name)

    def name_tag(self, frame, name=None):
        t, r, b, l = self.coords
        _name = self.name if name is None else name
        self.name_writer.write(frame, position=(0, 20), text=_name, ref=(l, t))
        if self.name_line is True:
            shapefunctions.draw_line(frame, (0, 0), (0, 15), self.color, 1, ref=(l + 15, t))


class BoundingCircle(BoundingBox):

    shape = 'circle'
    def __init__(self,
                 color='r',  # must be either string in color hash or bgr value
                 thickness=2,
                 bbox_coords = True,
                 which_radius = 'diag', # options are 'diag', 'inside_min', inside_max
                 *args, **kwargs# what does this mean?
                 ):

        super().__init__(color=color, thickness=thickness, **kwargs)

        self.bbox_coords = bbox_coords

        self.which_radius = which_radius

        self.name_writer.jtype = 'c'

    @property
    def center(self):
        if self.bbox_coords is True:
            return super().center
        else:
            return self.coords[:2]

    @property
    def radius(self):
        if self.bbox_coords is True and self.which_radius == 'diag':
            return self.diagonal/2
        elif self.bbox_coords is True and self.which_radius == 'inside_max':
            return max(self.height, self.width)/2
        elif self.bbox_coords is True and self.which_radius == 'inside_min':
            return min(self.height, self.width)/2
        else:
            return self.coords[2]


    def write(self, frame, name=None):
        if self.show_me is False:
            return

        _name = self.name if name is None else name
        shapefunctions.draw_circle(frame, self.center, self.radius, self.color, self.thickness)
        if self.show_name is True and (name is not None or self.name is not None):
            self.name_tag(frame, name)

    def name_tag(self, frame, name=None):
        [x, y]  = list(self.center)

        _name = name if name is not None else self.name
        self.name_writer.write(frame, position=(0, self.radius+20), text=_name, ref=(x,y))
        # if self.name_line is True:
        #     shapes.draw_line(frame, (0, 0), (0, 15), self.color, 1, ref=(position[0], position[1]-5))


class CrossHair(BoundingCircle):

    def __init__(self, *args, radius=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        if radius is None:
            self.constant_size = False
            self._radius = 0
        else:
            self.constant_size = True
            self._radius = radius

        self.line_writer = Line(color='b', thickness=self.thickness, wtype='cal')

    @property
    def radius(self):
        if self.constant_size is True:
            return self._radius
        else:
            return super().radius

    @radius.setter
    def radius(self, new_radius):
        self._radius= new_radius
        self.constant_size = True

    def write(self, frame, name=None):
        center = self.center
        radius = self.radius
        r75 = radius*.75

        self.line_writer.write(frame, (0, r75), 0, radius*.2, ref=center, thickness=2)
        self.line_writer.write(frame, (0, -r75), 0, radius * .2, ref=center, thickness=2)
        self.line_writer.write(frame, (r75, 0), 90, radius * .2,  ref=center, thickness=2)
        self.line_writer.write(frame, (-r75, 0), 90, radius * .2, ref=center, thickness=2)
        #
        # shapes.draw_cal_line(frame, center, 90, radius*2.2, color='g', thickness=2)
        # shapes.draw_cal_line(frame, center, 0, radius*2.2, color='g', thickness=2)

        shapefunctions.draw_circle(frame, center, radius, self.color, self.thickness)
        shapefunctions.draw_circle(frame, center, radius / 2, 'b', self.thickness / 2)

        self.line_writer.write(frame, center, 90, radius*2.2, wtype='cal', thickness=1)
        self.line_writer.write(frame, center, 0, radius*2.2, wtype='cal',thickness=1)

        shapefunctions.draw_circle(frame, center, 3, 'g', -1)


