import numpy as np

from otis.helpers import maths
from otis.overlay import textwriters

class AssetGroup:

    def __init__(self,
                 position=(50, 50),
                 color='r',
                 scale=1,
                 ):
        super().__init__()

        self.assets = []
        self._position = np.array(position) ## Top Left
        self.color = color
        self.scale = scale

    def __index__(self, i):
        return self.assets[i]

    def add(self, asset):
        if not isinstance(asset, (list, tuple)):
            asset = [asset]

        for a in asset:
            a.ref = self._position
            self.assets.append(a)

        return self

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, pos):
        self._position[:] = pos

    def write(self, frame):
        for asset in self.assets:
            asset.write(frame)


class BasicInfoGroup(AssetGroup):

    def __init__(self,
                 position,
                 manager,
                 show_dim=True,
                 ma=30,
                 spacing=30,
                 color='w',
                 scale=1,
                 offsets = (0, 0), #standard cartesian
                 show_model = True
                 ):

        super().__init__(position)

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
                                             position=(offsets[0], offsets[1]),
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
                                                  position=(offsets[0], offsets[1]-self.spacing * i),
                                                  scale=self.scale,
                                                  color=self.color,
                                                  )
            i += 1
            self.add(model_writer)
        except:
            pass

        if show_dim is True:
            dim_text = f'resolution : {self.args.dim}'
            dim_writer = textwriters.TextWriter(position = (offsets[0], offsets[1]-self.spacing * i),
                                                text=dim_text,
                                                scale = self.scale,
                                                color = self.color
                                                )

            self.add(dim_writer)
