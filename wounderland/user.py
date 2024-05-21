"""wounderland.user"""

from wounderland.utils import WounderMap, WounderKey


class User:
    """The Game"""

    def __init__(self, name, keys, email=None):
        self.name = name
        self.keys = keys
        self.email = email


def create_user(name, keys, email=None):
    """Create the user"""

    WounderMap.set(WounderKey.USER, User(name, keys, email=email))


def get_user():
    """Get the gloabl user"""

    return WounderMap.get(WounderKey.USER)


def update_user_keys(keys):
    """Update user keys"""

    get_user().keys = keys
