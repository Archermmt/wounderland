"""wounderland.user"""

from wounderland.utils import WounderMap, WounderKey
from wounderland import utils


class User:
    """The Game"""

    def __init__(self, name, keys, email=None):
        self._name = name
        self._keys = keys
        self._email = email

    def __str__(self):
        des = {"name": self._name, "keys": list(self._keys.keys())}
        if self._email:
            des["email"] = self._email
        return utils.dump_dict(des)

    def update_keys(self, keys):
        self._keys.update(keys)

    @property
    def keys(self):
        return self._keys
