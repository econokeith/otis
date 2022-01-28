


class Scene:

    def __init__(self, shard_data_object, *args, capture=None, **kwargs):

        self.completed = False
        self.end_pause = 0
        self.start_pause = 0

    def __call__(self, *args, **kwargs):

        pass

