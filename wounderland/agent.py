"""wounderland.agent"""

import math
import random
from wounderland import memory, utils
from wounderland.memory import Event, ConceptNode
from wounderland.model.llm_model import create_llm_model


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.maze = maze

        # agent config
        self.percept_config = config["percept"]
        self.think_config = config["think"]
        self._llm = None

        # memory
        self.spatial = memory.Spatial(config["spatial"])
        self.associate = memory.Associate(config["associate"])
        self.scratch = memory.Scratch(self.name, config["scratch"])

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

    def reset_user(self, user):
        if self.think_config["mode"] == "llm" and not self._llm:
            self._llm = create_llm_model(**self.think_config["llm"], keys=user.keys)
            if self._llm:
                prompt = self.scratch.wakeup_prompt()
                self.scratch.wake_up = self._llm.completion(**prompt)

    def remove_user(self):
        self._llm = None

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
        # add spatial memory
        for tile in scope:
            if tile.has_address("game_object"):
                self.spatial.add_leaf(tile.address)
        percept_events, arena_path = {}, curr_tile.get_address("arena")
        # gather perceived events
        for tile in scope:
            if not tile.events or tile.get_address("arena") != arena_path:
                continue
            dist = math.dist(tile.coord, self.coord)
            for event in tile.events:
                if dist < percept_events.get(event, float("inf")):
                    percept_events[event] = dist
        percept_events = list(
            sorted(percept_events.keys(), key=lambda k: percept_events[k])
        )

        # gather concept nodes
        def _get_embedding(event, e_type="event"):
            desc = event.sub_desc
            if e_type == "event":
                poignancy = self.evaluate_event(event)
            elif e_type == "chat":
                poignancy = self.evaluate_chat(event)
            else:
                raise Exception("Unexpected event type " + str(e_type))
            if desc in self.associate.embeddings:
                return (desc, self.associate.embeddings[desc]), poignancy
            if self._llm:
                return (desc, self._llm.embedding(desc)), poignancy
            return (desc, None), poignancy

        # retention events
        ret_events = []
        for p_event in percept_events[: self.percept_config["att_bandwidth"]]:
            latest_events = self.associate.get_recent_events()
            if p_event not in latest_events:
                event_embedding_pair, event_poignancy = _get_embedding(p_event)
                chats = []
                if p_event.fit(self.name, "chat with"):
                    curr_event = self.get_curr_event()
                    chat_embedding_pair, chat_poignancy = _get_embedding(curr_event)
                    chat_node = self.associate.add_chat(
                        curr_event,
                        chat_embedding_pair,
                        chat_poignancy,
                        filling=self.scratch.chat,
                    )
                    chats = [chat_node.name]

                # Finally, we add the current event to the agent's memory.
                event_node = self.associate.add_event(
                    p_event, event_embedding_pair, event_poignancy, filling=chats
                )
                ret_events.append(event_node)
                self.scratch.importance_decrease(event_poignancy)
        return ret_events

    def retrieve(self, events):
        def _get_info(event):
            return {
                "curr_event": event,
                "events": self.associate.retrieve_events(event),
                "thoughts": self.associate.retrieve_thoughts(event),
            }

        return {e.event.sub_desc: _get_info(e) for e in events}

    def plan(self, agents, retrieved):
        plan = {"name": self.name, "direct": "stop"}
        if self.think_config["mode"] == "random":
            plan["direct"] = random.choice(["left", "right", "up", "down", "stop"])
            return plan
        if self.think_config["mode"] == "llm":
            print("should really think!!")
            raise Exception("stop here!!")
        return plan

    def think(self, status, agents):
        self.move(status["position"])
        events = self.percept()
        retrieved = self.retrieve(events)
        for k, info in retrieved.items():
            print("\n\nretrieved {}".format(k))
            print("events " + str([str(e) for e in info["events"]]))
            print("thoughts " + str([str(e) for e in info["thoughts"]]))
        plan = self.plan(agents, retrieved)

        """
        plan = self.plan(maze, personas, new_day, retrieved)
        self.reflect()
        """
        return plan

    def evaluate_event(self, event):
        if event.fit(None, "is", "idle") or not self._llm:
            return 1
        prompt = self.scratch.poignant_prompt(event)
        print("prompt " + str(prompt))
        response = self._llm.completion(prompt)
        print("response " + str(response))
        raise Exception("stop here!!")

        return 1

    def evaluate_chat(self, event):
        if not self._llm:
            return 1
        return 1

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
