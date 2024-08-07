import os
import copy
import json
from wounderland.game import create_game, get_game
from wounderland import utils


class SimulateServer:
    def __init__(self, static_root, config, ckpt_file, start="", verbose="info"):
        self.static_root = static_root
        self.ckpt = utils.load_dict(ckpt_file)
        self.ckpt.setdefault("agents", {})
        self.start_step = self.ckpt.get("step", 0)
        for name, a_config in self.ckpt["agents"].items():
            if name not in config["agents"]:
                continue
            config["agents"][name]["update"] = a_config
        config["time"] = {"start": start or self.ckpt.get("time", "")}
        config["keep_storage"] = self.ckpt.get("keep_storage", True)
        game = create_game(static_root, config, logger=utils.create_io_logger(verbose))
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
            if name in self.ckpt["agents"]:
                self.agent_status[name].update(
                    {
                        "coord": self.ckpt["agents"][name]["coord"],
                        "path": self.ckpt["agents"][name]["path"],
                    }
                )
            else:
                self.ckpt["agents"][name] = {}
        self.think_interval = max(
            a.think_config["interval"] for a in self.game.agents.values()
        )
        self.logger = self.game.logger

    def simulate(self, step, stride=0):
        timer = utils.get_timer()
        for i in range(self.start_step, self.start_step + step):
            title = "Simulate Step[{}/{}]".format(i, self.start_step + step)
            self.logger.info("\n" + utils.split_line(title, "="))
            for name, status in self.agent_status.items():
                plan = self.game.agent_think(name, status)["plan"]
                agent = self.game.get_agent(name)
                if name not in self.ckpt["agents"]:
                    self.ckpt["agents"][name] = {}
                self.ckpt["agents"][name].update(agent.to_dict())
                if plan.get("path"):
                    status["coord"], status["path"] = plan["path"][-1], []
                self.ckpt["agents"][name].update(
                    {"coord": status["coord"], "path": status["path"]}
                )
            if stride > 0:
                timer.forward(stride)
            self.ckpt.update(
                {
                    "time": timer.get_date("%Y%m%d-%H:%M"),
                    "keep_storage": True,
                    "step": i + 1,
                }
            )
            with open("ckpt_{}.json".format(i), "w") as f:
                f.write(json.dumps(self.ckpt, indent=2))

    def load_static(self, path):
        return utils.load_dict(os.path.join(self.static_root, path))
