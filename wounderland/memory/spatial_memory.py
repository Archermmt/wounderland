from wounderland import utils


class MemoryTree:
    def __init__(self, config):
        self.tree = config

    def __str__(self):
        return utils.dump_dict(self.tree)
