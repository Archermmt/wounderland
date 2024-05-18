import random
from wounderland import memory, utils
from .event import Event


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.maze = maze

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
        self.idle_events = {}

        # plan
        self.planned_path = []

        # update maze
        self.coord = None
        self.move(config["position"])

        self.logger = logger

    def __str__(self):
        des = {
            "name": self.name,
            "tile": self.maze.tile_at(self.coord),
            "precept": self.percept_config,
            "think": self.think_config,
        }
        return utils.dump_dict(des)

    def move(self, position):
        if self.coord:
            self.maze.remove_events(self.coord, subject=self.name)
        for event, coord in self.idle_events.items():
            self.maze.update_event(coord, event, "idle")
        self.coord = [int(p / self.maze.sq_tile_size) for p in position]
        self.idle_events = {}
        self.maze.add_event(self.coord, self.get_curr_event())
        self.maze.persona_tiles[self.name] = self.coord
        if not self.planned_path:
            obj_event = self.get_curr_event(False)
            self.idle_events[obj_event] = self.coord
            self.maze.add_event(self.coord, obj_event)
            blank = Event(obj_event.subject, None, None, None)
            self.maze.remove_events(self.coord, event=blank)

    def plan(self):
        print("Planing: " + str(self))

    def think(self, status):
        self.move(status["position"])
        plan = {"name": self.name, "direct": "stop"}
        if self.think_config["mode"] == "random":
            plan["direct"] = random.choice(["left", "right", "up", "down", "stop"])
        return plan

    def get_curr_event(self, as_sub=True):
        if not self.act_address:
            return Event(self.name if as_sub else "", None, None, None)
        return Event(
            self.act_event[0] if as_sub else self.act_address,
            self.act_event[1],
            self.act_event[2],
            self.act_description,
        )
