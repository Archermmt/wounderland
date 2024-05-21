"""wounderland.agent"""

import math
import random
from wounderland import memory, utils
from wounderland.memory import Event
from wounderland.model.llm_model import create_llm_model
from .user import get_user


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.maze = maze

        # agent config
        self.percept_config = config["percept"]
        self.think_config = config["think"]
        if self.think_config["mode"] == "llm":
            self._llm = create_llm_model(
                **self.think_config["llm"], keys=get_user().keys
            )
        else:
            self._llm = None

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
            "tile": self.maze.tile_at(self.coord).to_dict(),
            "precept": self.percept_config,
            "think": self.think_config,
        }
        return utils.dump_dict(des)

    def move(self, position):
        if self.coord:
            self.maze.remove_events(self.coord, subject=self.name)
        for event, coord in self.idle_events.items():
            self.maze.update_event(coord, event, "idle")
        self.coord = [int(p / self.maze.tile_size) for p in position]
        self.idle_events = {}
        self.maze.add_event(self.coord, self.get_curr_event())
        self.maze.persona_tiles[self.name] = self.coord
        if not self.planned_path:
            obj_event = self.get_curr_event(False)
            self.idle_events[obj_event] = self.coord
            self.maze.add_event(self.coord, obj_event)
            blank = Event(obj_event.subject, None, None, None)
            self.maze.remove_events(self.coord, event=blank)

    def percept(self):
        curr_tile = self.get_curr_tile()
        scope = self.maze.get_scope(self.coord, self.percept_config)
        print("Perceive: " + str(self))
        # add spatial memory
        for tile in scope:
            if tile.has_address("game_object"):
                self.s_mem.add_leaf(tile.address)
        per_events, arena_path = {}, curr_tile.get_address("arena")
        # gather events
        for tile in scope:
            if not tile.events or tile.get_address("arena") != arena_path:
                continue
            dist = math.dist(tile.coord, self.coord)
            for event in tile.events:
                if dist < per_events.get(event, float("inf")):
                    per_events[event] = dist
        per_events = list(sorted(per_events.keys(), key=lambda k: per_events[k]))
        if self._llm:
            # retention events
            ret_events = []
            for p_event in per_events[: self.percept_config["att_bandwidth"]]:
                print("has percept event " + str(p_event))
                latest_events = self.a_mem.get_recent_events(
                    self.percept_config["retention"]
                )
                print("latest_events " + str(latest_events))
                if p_event not in latest_events:
                    obj_desc = p_event.obj_desc()
                    print("obj_desc " + str(obj_desc))
                    if obj_desc in self.a_mem.embeddings:
                        event_embedding = self.a_mem.embeddings[obj_desc]
                    else:
                        event_embedding = self._llm.embedding(obj_desc)
                    print("event_embedding " + str(event_embedding))
            return ret_events
        return per_events

    def think(self, status, agents):
        self.move(status["position"])
        perceived = self.percept()
        plan = {"name": self.name, "direct": "stop"}
        if self.think_config["mode"] == "random":
            plan["direct"] = random.choice(["left", "right", "up", "down", "stop"])

        """
        perceived = self.perceive(maze)
        retrieved = self.retrieve(perceived)
        plan = self.plan(maze, personas, new_day, retrieved)
        self.reflect()
        """
        return plan

    def get_curr_tile(self):
        return self.maze.tile_at(self.coord)

    def get_curr_event(self, as_sub=True):
        if not self.act_address:
            return Event(self.name if as_sub else "", None, None, None)
        return Event(
            self.act_event[0] if as_sub else self.act_address,
            self.act_event[1],
            self.act_event[2],
            self.act_description,
        )
