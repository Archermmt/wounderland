import os
import copy
import json
from wounderland.game import create_game, get_game
from wounderland import utils


class SimulateServer:
    def __init__(self, static_root, config, ckpt_file):
        self.static_root = static_root
        self.ckpt = utils.load_dict(ckpt_file)
        self.ckpt.setdefault("agents", {})
        for name, a_config in self.ckpt["agents"].items():
            if name not in config["agents"]:
                continue
            config["agents"][name]["update"] = a_config
        game = create_game(static_root, config)
        game.reset_user("test", keys=self.ckpt["keys"])
        self.game = get_game()
        self.tile_size = self.game.maze.tile_size
        self.agent_status = {}
        if "agent_base" in config:
            agent_base = self.load_static(config["agent_base"]["path"])
        else:
            agent_base = {}
        for name, agent in config["agents"].items():
            agent_config = copy.deepcopy(agent_base)
            agent_config.update(self.load_static(agent["path"]))
            self.agent_status[name] = {
                "direction": agent_config["direction"],
                "coord": agent_config["coord"],
                "speed": agent_config["move"]["speed"],
                "path": [],
            }
            self.ckpt["agents"].setdefault(name, {})
        self.think_interval = max(
            a.think_config["interval"] for a in self.game.agents.values()
        )
        self.logger = self.game.logger

    def simulate(self, step, start=-1, stride=0):
        if start >= 0:
            utils.set_timer(start=start)
        timer = utils.get_timer()
        for i in range(step):
            self.logger.info(
                "Simulate Step[{}/{}] @ {}".format(i, step, timer.get_date("%H:%M:%S"))
            )
            for name, status in self.agent_status.items():
                print("\n\nstatus of {}:{}".format(name, status))
                plan = self.game.agent_think(name, status)
                agent = self.game.get_agent(name)
                if name not in self.ckpt["agents"]:
                    self.ckpt["agents"][name] = {}
                self.ckpt["agents"][name].update(agent.to_dict())
                print("Agent {}\nhas plan {}".format(agent, plan))
                if len(plan["path"]) > 5:
                    status["coord"], status["path"] = plan["path"][5], plan["path"][5:]
                else:
                    status["coord"], status["path"] = plan["path"][-1], []
            with open("ckpt_{}.json".format(i), "w") as f:
                f.write(json.dumps(self.ckpt, indent=2))
            if stride > 0:
                timer.forward(stride)

    def load_static(self, path):
        return utils.load_dict(os.path.join(self.static_root, path))
