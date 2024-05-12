import random
from wounderland import memory


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.position = [int(p / maze.sq_tile_size) for p in config["position"]]

        # attrs
        self.percept_config = config["percept"]
        self.think_config = config["think"]

        # memory
        self.s_mem = memory.MemoryTree(config["spatial_memory"])
        self.a_mem = memory.AssociativeMemory()
        self.scratch = memory.Scratch(config)

        # CURR ACTION
        # <address> is literally the string address of where the action is taking
        # place.  It comes in the form of
        # "{world}:{sector}:{arena}:{game_objects}". It is important that you
        # access this without doing negative indexing (e.g., [-1]) because the
        # latter address elements may not be present in some cases.
        # e.g., "dolores double studio:double studio:bedroom 1:bed"
        self.act_address = None
        # <description> is a string description of the action.
        self.act_description = None
        # <event_form> represents the event triple that the persona is currently
        # engaged in.
        self.act_event = (self.name, None, None)

        # update maze
        p_x, p_y = self.position
        maze.tiles[p_y][p_x]["events"].add(self.get_curr_event())
        maze.persona_tiles[self.name] = self.position

        self.logger = logger

    def __str__(self):
        return "{} @ {}, precept {}, think: {}".format(
            self.name, self.position, self.percept_config, self.think_config
        )

    def think(self, status):
        if self.think_config["mode"] == "random":
            direct = random.choice(["left", "right", "up", "down", "stop"])
        return {"direct": direct}

    def get_curr_event(self, as_obj=False):
        if not self.act_address:
            return ("" if as_obj else self.name, None, None, None)
        return (
            self.act_address if as_obj else self.act_event[0],
            self.act_event[1],
            self.act_event[2],
            self.act_description,
        )
