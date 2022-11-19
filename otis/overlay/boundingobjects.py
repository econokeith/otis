import copy
import abc

import numpy as np

from otis.overlay import bases, shapes
from otis.overlay.textwriters import NameTag
from otis.helpers import coordtools

class BoundingAsset(bases.Writer, abc.ABC):

    @abc.abstractmethod
    def __init__(self,
                 color='r',
                 name = None,
                 name_tagger = None,
                 show_name = False,
                 show_self = True,
                 coord_format = 'rtlb',
                 thickness=1,
                 ltype=None,
                 ):

        super().__init__()
        self._color = color
        self.coords = np.zeros(4, dtype=int)
        self.last_coords = self.coords.copy()
        self.coords_format = coord_format
        self.use_name = show_name
        self.thickness = thickness
        self.ltype = ltype
        self.show_self = show_self

        if name_tagger is None:
            self.name_tag = NameTag(name=name)
        else:
            assert isinstance(name_tagger, NameTag)
            self.name_tag = copy.deepcopy(name_tagger)


class BoundingAssetBox(BoundingAsset):

    def __init__(self,
                 set_dim = None,
                 **kwargs,
                 ):
        super().__init__(**kwargs)
        assert len(set_dim) == 2
        self.set_dim = set_dim
        self.asset =shapes.Rectangle(color=self.color,
                                     thickness=self.thickness,
                                     ltype=self.ltype,
                                     coord_format = self.coords_format
                                     )

    def write(self, frame):
        if self.set_dim is not None:
            cx, cy, _, _ = 1, 2, 3, 4

