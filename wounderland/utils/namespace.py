"""wounderland.utils.namespace"""

from typing import Any, Optional
import copy


class GameMap:
    """Global Namespace map for Land"""

    MAP = {}

    @classmethod
    def set(cls, key: str, value: Any):
        cls.MAP[key] = value

    @classmethod
    def get(cls, key: str, default: Optional[Any] = None):
        return cls.MAP.get(key, default)

    @classmethod
    def clone(cls, key: str, default: Optional[Any] = None):
        return copy.deepcopy(cls.get(key, default))

    @classmethod
    def delete(cls, key: str):
        if key in cls.MAP:
            return cls.MAP.pop(key)
        return None

    @classmethod
    def contains(cls, key: str):
        return key in cls.MAP

    @classmethod
    def reset(cls):
        cls.MAP = {}


class GameKey:
    """Keys for the LandMap"""

    GAME = "game"
