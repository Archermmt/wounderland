import copy
from world import utils
from .maze import Maze
from .agent import Agent


class ReverieServer:
    """Backend server for reverie"""

    def __init__(self, config: dict):
        print("init the ReverieServer with config {}".format(config))
        self.maze = Maze(utils.load_static(config["maze"]["path"]))
        self.agents = {}
        if "base" in config["agents"]:
            agent_base = utils.load_static(config["agents"]["base"]["path"])
        else:
            agent_base = {}
        for name, agent in config["agents"].items():
            if name == "base":
                continue
            agent_config = copy.deepcopy(agent_base)
            agent_config.update(utils.load_static(agent["path"]))
            agent_config.update(agent.get("extra", {}))
            self.agents[name] = Agent(agent_config, self.maze)
