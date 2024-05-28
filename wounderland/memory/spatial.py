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

    def get_tree(self, root):
        def _get_tree(root, tree):
            if root in tree:
                return tree[root]
            if not isinstance(tree, dict):
                return None
            for subtree in tree.values():
                c_tree = _get_tree(root, subtree)
                if c_tree:
                    return c_tree
            return None

        return _get_tree(root, self.tree)
