from world import utils
from .maze import Maze


class ReverieServer:
    """Backend server for reverie"""

    def __init__(self, config: dict):
        print("init the ReverieServer with config {}".format(config))
        self.maze = Maze(utils.static_path(config["maze"]["path"]))
