import os
import argparse
from simulate_server import SimulateServer

parser = argparse.ArgumentParser(description="Test for village")
parser.add_argument(
    "--statics_dir", type=str, default="../playground/statics", help="The statics dir"
)
parser.add_argument("--step", type=int, default=5, help="The simulate step")
parser.add_argument("--output", type=str, default="village_test", help="The output dir")
args = parser.parse_args()


def get_config(agents=None):
    agents = agents or ["Isabella Rodriguez", "Klaus Mueller", "Maria Lopez"]
    assets_root = os.path.join("assets", "village")
    config = {
        "maze": {"path": os.path.join(assets_root, "maze.json")},
        "agent_base": {"path": os.path.join(assets_root, "agent.json")},
        "agents": {},
    }
    for a in agents:
        config["agents"][a] = {
            "path": os.path.join(
                assets_root, "agents", a.replace(" ", "_"), "agent.json"
            )
        }
    return config


if __name__ == "__main__":
    server = SimulateServer(args.statics_dir, get_config())
    server.simulate(args.step)
