"""wounderland.memory.spatial"""

from wounderland import utils


class Spatial:
    def __init__(self, config):
        self.tree = config

    def __str__(self):
        return utils.dump_dict(self.tree)

    def add_leaf(self, address):
        def _add_leaf(left_address, tree):
            if len(left_address) == 2:
                leaves = tree.setdefault(left_address[0], [])
                if left_address[1] not in leaves:
                    leaves.append(left_address[1])
            elif len(left_address) > 2:
                _add_leaf(left_address[1:], tree.setdefault(left_address[0], {}))

        _add_leaf(address, self.tree)
