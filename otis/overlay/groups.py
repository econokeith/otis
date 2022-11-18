import numpy as np

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


