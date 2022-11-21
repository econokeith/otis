import numpy as np

from otis.helpers import maths
from otis.overlay import textwriters

class AssetGroup:

    def __init__(self,
                 coords=(50, 50),
                 color='r',
                 scale=1,
                 ):
        super().__init__()

        self.assets = []
        self._coords = np.array(coords) ## Top Left
        self.color = color
        self.scale = scale

    def __index__(self, i):
        return self.assets[i]

    def add(self, asset):
        if not isinstance(asset, (list, tuple)):
            asset = [asset]

        for a in asset:
            a.ref = self._coords
            self.assets.append(a)

        return self

    @property
    def coords(self):
        return self._coords

    @coords.setter
    def coords(self, pos):
        self._coords[:] = pos

    def write(self, frame):
        for asset in self.assets:
            asset.write(frame)


class BasicInfoGroup(AssetGroup):

    def __init__(self,
                 coords,
                 manager,
                 show_dim=True,
                 ma=30,
                 spacing=30,
                 color='w',
                 scale=1,
                 offsets = (0, 0),  #standard cartesian
                 show_model = True
                 ):

        super().__init__(coords)

        self.scale = scale
        self.color = color
        self.shared = manager.shared
        self.args = manager.pargs
        self.ma = ma
        self.show_dim = show_dim
        self.show_model = show_model
        self.spacing = spacing * scale
        self.offsets = offsets

        fps_writer = textwriters.TimerWriter(title="screen fps",
                                             timer_type='last',
                                             coords=(offsets[0], offsets[1]),
                                             roundw=0,
                                             per_second=True,
                                             moving_average=self.ma,
                                             scale=self.scale,
                                             color=self.color,
                                             )

        self.add(fps_writer)
        i = 1
        try:
            self.model_ma = maths.MovingAverage(self.ma)
            ma_text_fun = lambda: f'model updates per second : {int(1 / self.model_ma.update(self.shared.m_time.value))}'
            model_writer = textwriters.InfoWriter(text_fun=ma_text_fun,
                                                  coords=(offsets[0], offsets[1] - self.spacing * i),
                                                  scale=self.scale,
                                                  color=self.color,
                                                  )
            i += 1
            self.add(model_writer)
        except:
            pass

        if show_dim is True:
            dim_text = f'resolution : {self.args.dim}'
            dim_writer = textwriters.TextWriter(coords= (offsets[0], offsets[1] - self.spacing * i),
                                                line=dim_text,
                                                scale = self.scale,
                                                color = self.color
                                                )

            self.add(dim_writer)
