import copy
import abc

import numpy as np

from otis.overlay import bases, shapes
from otis.overlay.textwriters import NameTag
from otis.helpers import coordtools

class BoundingAsset(bases.AssetWriter, abc.ABC):

    @abc.abstractmethod
    def __init__(self,
                 name = None,
                 name_tagger = None,
                 show_name = False,
                 show_self = True
                 ):
        """
        Bounding asset functionality to shape assets for use in displaying bounding objects
        Args:
            color:
            name:
            name_tagger:
            show_name:
            show_self:
            coord_format:
            thickness:
            ltype:
        """

        super().__init__()

        self.coords = np.zeros(4, dtype=int)
        self.last_coords = self.coords.copy()
        self.show_name = show_name
        self.show_self = show_self
        self.name = name

        if name_tagger is None:
            self.name_tag = NameTag(name=name,
                                    attached_to=self)
        else:
            assert isinstance(name_tagger, NameTag)
            self.name_tag = copy.deepcopy(name_tagger)
            self.name_tag.attached_to = self

    def write(self, frame):
        self.name_tag.write(frame, name)


class BoundingAssetBox(BoundingAsset, shapes.Rectangle):

    def __init__(self,
                 coords = (0,0,0,0),
                 color='r',
                 thickness=1,
                 ltype=None,
                 ref=None,
                 dim=None,
                 coord_format='rtlb',
                 update_format='rtlb',
                 collisions=False,
                 set_dim = None,
                 name=None,
                 name_tagger=None,
                 show_name=False,
                 show_self=True
                 ):

        BoundingAsset.__init__(self,
                               name=name,
                               name_tagger=name_tagger,
                               show_name=show_name,
                               show_self=show_self
                               )

        shapes.Rectangle.__init__(self,
                                  coords,
                                  color=color,
                                  thickness=thickness,
                                  ltype=ltype,
                                  ref=ref,
                                  dim=dim,
                                  coord_format=coord_format,
                                  update_format=update_format,
                                  collisions=collisions,
                                  )

        assert (set_dim is None or len(set_dim)==2)
        self.set_dim = set_dim

    def write(self, frame):
        if self.set_dim is not None:
            cx, cy, _, _ = 1, 2, 3, 4

