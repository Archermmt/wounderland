from .maze import Maze
from world.backend.memory import MemoryTree, AssociativeMemory, Scratch


class Agent:
    def __init__(self, config: dict, maze: Maze):
        self.name = config["name"]
        self.position = [int(p / maze.sq_tile_size) for p in config["position"]]
        self.s_mem = MemoryTree(config["spatial_memory"])
        self.a_mem = AssociativeMemory()
        self.scratch = Scratch(config)
        # update maze
        p_x, p_y = self.position
        maze.tiles[p_y][p_x]["events"].add(self.scratch.get_curr_event())
        maze.persona_tiles[self.name] = self.position
