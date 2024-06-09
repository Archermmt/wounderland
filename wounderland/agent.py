"""wounderland.agent"""

import math
import random
import datetime
from wounderland import memory, prompt, utils
from wounderland.model.llm_model import create_llm_model


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.maze = maze
        self._llm = None
        self.logger = logger

        # agent config
        self.percept_config = config["percept"]
        self.think_config = config["think"]

        # memory
        self.spatial = memory.Spatial(config["spatial"])
        self.schedule = memory.Schedule(config["schedule"])
        self.associate = memory.Associate(config["associate"])
        self.concepts = []

        # prompt
        self.scratch = prompt.Scratch(self.name, config["scratch"])

        # status
        self.status = {"poignancy": {"current": 0, "num_event": 0}, "chat_with": {}}
        self.status = utils.update_dict(self.status, config.get("status", {}))

        # action and events
        tile = self.maze.tile_at(config["coord"])
        address = tile.get_address("game_object", as_list=True)
        self.actions = [
            memory.Action(
                memory.Event(self.name, address=address),
                memory.Event(address[-1], address=address),
            )
        ]

        # update maze
        self.coord, self.path = None, None
        self.move(config["coord"])

    def __str__(self):
        des = {
            "name": self.name,
            "tile": self.maze.tile_at(self.coord).to_dict(),
            "actions": [str(a).replace("\n", "\n    ") for a in self.actions],
            "concepts": [str(c).replace("\n", "\n    ") for c in self.concepts],
        }
        if self.schedule.scheduled():
            des["schedule"] = ("\n  " + str(self.schedule).replace("\n", "\n  "),)
        return utils.dump_dict(des)

    def reset_user(self, user):
        if self.think_config["mode"] == "llm" and not self._llm:
            self._llm = create_llm_model(**self.think_config["llm"], keys=user.keys)
            if self._llm:
                self.make_schedule()

    def remove_user(self):
        self._llm = None

    def make_schedule(self):
        if not self.schedule.scheduled():
            # make init schedule
            self.schedule.created_at = utils.get_timer().get_date()
            prompt = self.scratch.prompt_wake_up()
            wake_up = self._llm.completion(**prompt)
            prompt = self.scratch.prompt_schedule_init(wake_up)
            init_schedule = self._llm.completion(**prompt)
            if self.associate.nodes:
                print("should adjust daily schedule!!")
                raise Exception("stop here!!")
            # make daily schedule
            hours = [str(i) + ":00 AM" for i in range(12)]
            hours += [str(i) + ":00 PM" for i in range(12)]
            daily_schedule = {}
            for _ in range(self.schedule.max_try):
                schedule = [(h, "sleeping") for h in hours[:wake_up]]
                schedule += [(h, "") for h in hours[wake_up:]]
                prompt = self.scratch.prompt_schedule_daily(
                    wake_up, schedule, init_schedule
                )
                daily_schedule = self._llm.completion(**prompt)
                daily_schedule.update({h: s for h, s in schedule[:wake_up]})
                if len(set(daily_schedule.values())) >= self.schedule.diversity:
                    break
            daily_schedule.update(
                {k: "asleep" for k in hours if k not in daily_schedule}
            )
            prev = None
            for hour in hours:
                if daily_schedule[hour] == prev:
                    self.schedule.daily_schedule[-1]["duration"] += 60
                    continue
                self.schedule.add_plan(daily_schedule[hour], 60)
                prev = daily_schedule[hour]
            event = memory.Event(
                self.name, "plan", self.schedule.created_at.strftime("%A %B %d")
            )
            thought = f"This is {self.name}'s plan for {event.object}: "
            thought += "; ".join(init_schedule)
            self._add_concept(
                event,
                "thought",
                desc=thought,
                keywords={"plan"},
                expiration=self.schedule.created_at + datetime.timedelta(days=30),
            )
        # decompose current plan
        plan, _ = self.schedule.current_plan()
        if self.schedule.decompose(plan):
            prompt = self.scratch.prompt_schedule_decompose(plan, self.schedule)
            decompose, start = [], plan["start"]
            for describe, duration in self._llm.completion(**prompt):
                decompose.append(
                    {
                        "idx": len(decompose),
                        "describe": describe,
                        "start": start,
                        "duration": duration,
                    }
                )
                start += duration
            plan["decompose"] = decompose

    def move(self, coord, path=None):
        idle_events = {}
        if self.coord and self.coord != coord:
            self.maze.remove_events(self.coord, subject=self.name)
            idle_events = self.maze.update_events(self.coord, "idle")
        if not path:
            self.maze.add_event(coord, self.get_curr_event())
            self.maze.add_event(coord, self.get_curr_event(False))
        self.coord = coord
        self.path = path or []
        return idle_events

    def think(self, status, agents):
        self.move(status["coord"], status["path"])
        self.percept()
        if self.think_config["mode"] == "random" or not self._llm:
            path = [self.coord]
            for _ in range(5):
                path.append(random.choice(self.maze.get_around(path[-1])))
            return {"name": self.name, "path": path[1:], "emojis": {}}
        self.plan(agents)
        self.reflect()
        path = self.find_path(agents)
        return {
            "name": self.name,
            "path": path,
            "emojis": {"agent": self.get_curr_event().emoji},
        }

    def percept(self):
        curr_tile = self.get_curr_tile()
        scope = self.maze.get_scope(self.coord, self.percept_config)
        # add spatial memory
        for tile in scope:
            if tile.has_address("game_object"):
                self.spatial.add_leaf(tile.address)
        percept_events, curr_address = {}, curr_tile.get_address("arena", as_list=False)
        # gather perceived events
        for tile in scope:
            address = tile.get_address("arena", as_list=False)
            if not tile.events or address != curr_address:
                continue
            dist = math.dist(tile.coord, self.coord)
            for event in tile.events:
                if dist < percept_events.get(event, float("inf")):
                    percept_events[event] = dist
        percept_events = list(
            sorted(percept_events.keys(), key=lambda k: percept_events[k])
        )

        # retention events
        self.concepts = []
        for p_event in percept_events[: self.percept_config["att_bandwidth"]]:
            recent_events = {n.event: n for n in self.associate.retrieve_events()}
            if p_event in recent_events:
                self.concepts.append(recent_events[p_event])
            else:
                chats = []
                if p_event.fit(self.name, "chat with"):
                    node = self._add_concept(
                        self.get_curr_event(), "chat", filling=self.scratch.chat
                    )
                    chats = [node.name]
                node = self._add_concept(p_event, "event", filling=chats)
                self._increase_poignancy(node.poignancy)
                self.concepts.append(node)
        self.concepts = [c for c in self.concepts if c.event.subject != self.name]

    def plan(self, agents):
        self.make_schedule()
        self.actions = [a for a in self.actions if not a.finished()]
        if not self.actions:
            self.actions.append(self._determine_action())
        self._reaction(agents)

    def reflect(self):
        if self.status["poignancy"]["current"] >= self.think_config["poignancy_max"]:
            self.status["poignancy"]["current"] = 0
            self.status["poignancy"]["num_event"] = 0
            raise Exception("should reflect!!")
        return None

    def find_path(self, agents):
        address = self.get_curr_event().address
        if address[0] == "<persona>":
            other = agents[address[1]]
            path = self.maze.find_path(self.coord, other.coord)
            if len(path) <= 2:
                target_tiles = [path[0]]
            else:
                targets = [path[len(path) // 2], path[len(path) // 2 + 1]]
                if len(self.maze.find_path(self.coord, targets[0])) <= len(
                    self.maze.find_path(self.coord, targets[1])
                ):
                    target_tiles = [targets[0]]
                else:
                    target_tiles = [targets[1]]
        elif address[0] == "<waiting>":
            target_tiles = [address[1]]
        elif address[-1] == "<random>":
            obj = random.choice(self.spatial.get_leaves(address[:-1]))
            target_tiles = self.maze.get_address_tiles(address[:-1] + [obj])
        else:
            target_tiles = self.maze.get_address_tiles(address)

        # filter tile with self event
        def _ignore_target(t_coord):
            events = self.maze.events_at(t_coord)
            if any(e.subject in agents for e in events):
                return True
            return False

        target_tiles = [t for t in target_tiles if not _ignore_target(t)]
        if len(target_tiles) >= 4:
            target_tiles = random.sample(target_tiles, 4)
        pathes = {t: self.maze.find_path(self.coord, t) for t in target_tiles}
        target = min(pathes, key=lambda p: len(pathes[p]))
        return pathes[target][1:]

    def _determine_action(self):
        plan, de_plan = self.schedule.current_plan()
        describes = [plan["describe"], de_plan["describe"]]
        address = self.spatial.find_address(describes[0], as_list=True)
        if not address:
            tile = self.get_curr_tile()
            kwargs = {
                "describes": describes,
                "spatial": self.spatial,
                "address": tile.get_address("world", as_list=True),
            }
            prompt = self.scratch.prompt_determine_sector(**kwargs, tile=tile)
            kwargs["address"].append(self._llm.completion(**prompt))
            arenas = self.spatial.get_leaves(kwargs["address"])
            if len(arenas) == 1:
                kwargs["address"].append(arenas[0])
            else:
                prompt = self.scratch.prompt_determine_arena(**kwargs)
                kwargs["address"].append(self._llm.completion(**prompt))
            objs = self.spatial.get_leaves(kwargs["address"])
            if len(objs) == 0:
                kwargs["address"].append("random")
            elif len(objs) == 1:
                kwargs["address"].append(objs[0])
            else:
                prompt = self.scratch.prompt_determine_object(**kwargs)
                kwargs["address"].append(self._llm.completion(**prompt))
            address = kwargs["address"]

        # create action && object events
        def _make_event(subject, describe):
            prompt = self.scratch.prompt_describe_emoji(describe)
            emoji = self._llm.completion(**prompt)
            if subject == self.name:
                prompt = self.scratch.prompt_describe_event(subject, describe)
                args = self._llm.completion(**prompt)
                return memory.Event(*args, address=address, emoji=emoji)
            return memory.Event(subject, "is", describe, address=address, emoji=emoji)

        event = _make_event(self.name, describes[-1])
        prompt = self.scratch.promt_describe_object(address[-1], describes[-1])
        obj_event = _make_event(address[-1], self._llm.completion(**prompt))
        return memory.Action(
            event,
            obj_event,
            duration=de_plan["duration"],
            start=utils.daily_time(de_plan["start"]),
        )

    def _reaction(self, agents=None, ignore_words=None):
        focus = None
        ignore_words = ignore_words or ["is idle"]

        def _focus(concept):
            return concept.event.subject in agents

        def _ignore(concept):
            return any(i in concept.event.describe for i in ignore_words)

        if agents:
            priority = [i for i in self.concepts if _focus(i)]
            if priority:
                focus = random.choice(priority)
        if not focus:
            priority = [i for i in self.concepts if not _ignore(i)]
            if priority:
                focus = random.choice(priority)
        if not focus or focus.event.subject not in agents:
            return
        other = agents[focus.event.subject]
        if not self._chat_with(other, focus, agents):
            self._react_to(other, focus)

    def _skip_react(self, other):
        def _skip(action):
            if (
                not action.address
                or not action.event
                or "sleeping" in action.event.describe
            ):
                return False
            return True

        if self.actions[-1].act_type == "chat":
            return True
        if "<waiting>" in self.actions[-1].address:
            return True
        if _skip(self.actions[-1]) or _skip(other.actions[-1]):
            return True
        if utils.get_timer().daily_duration(mode="hour") >= 23:
            return True
        return False

    def _chat_with(self, other, focus, agents):
        if self._skip_react(other):
            return False
        act, o_act = self.actions[-1], other.actions[-1]
        if "<waiting>" in o_act.address:
            return False
        if o_act.act_type == "chat" or act.act_type == "chat":
            return False
        chats = self.associate.retrieve_chats(other.name)
        if chats and utils.get_timer().get_delta(chats[0].expiration) < 60:
            return False
        prompt = self.scratch.prompt_decide_talk(self, other, focus)
        if "yes" not in self._llm.completion(**prompt):
            return False
        print("should chat with " + str(other))
        convo, duration_min = generate_convo(maze, init_persona, target_persona)
        convo_summary = generate_convo_summary(init_persona, convo)
        inserted_act = convo_summary
        inserted_act_dur = duration_min

    def _react_to(self, other, focus):
        if self._skip_react(other):
            return False
        act, o_act = self.actions[-1], other.actions[-1]
        if "waiting" in o_act.description:
            return False
        if not self.path:
            return False
        if act.address != o_act.address:
            return False
        prompt = self.scratch.prompt_decide_react(self, other, focus)
        return self._llm.completion(**prompt)

    def _add_concept(
        self,
        event,
        e_type,
        desc=None,
        keywords=None,
        filling=None,
        created=None,
        expiration=None,
    ):
        embedding_pair, poignancy = self._evaluate_concept(event, e_type, desc)
        if e_type == "event":
            node = self.associate.add_event(
                event,
                embedding_pair,
                poignancy,
                keywords=keywords,
                filling=filling,
                created=created,
                expiration=expiration,
            )
        elif e_type == "chat":
            node = self.associate.add_chat(
                event,
                embedding_pair,
                poignancy,
                keywords=keywords,
                filling=filling,
                created=created,
                expiration=expiration,
            )
        elif e_type == "thought":
            node = self.associate.add_thought(
                event,
                embedding_pair,
                poignancy,
                keywords=keywords,
                filling=filling,
                created=created,
                expiration=expiration,
            )
        return node

    def _evaluate_concept(self, event, e_type="event", desc=None):
        desc = desc or event.describe
        if e_type == "event":
            poignancy = self._evaluate_event(event)
        elif e_type == "chat":
            poignancy = self._evaluate_chat(event)
        elif e_type == "thought":
            poignancy = 5
        else:
            raise Exception("Unexpected event type " + str(e_type))
        if desc in self.associate.embeddings:
            return (desc, self.associate.embeddings[desc]), poignancy
        # TMINFO debug only
        # if self._llm:
        #    return (desc, self._llm.embedding(desc)), poignancy
        return (desc, None), poignancy

    def _evaluate_event(self, event):
        if event.fit(None, "is", "idle") or not self._llm:
            return 1
        prompt = self.scratch.prompt_poignancy_event(event)
        return self._llm.completion(**prompt)

    def _evaluate_chat(self, event):
        if not self._llm:
            return 1
        print("should evaluare chat " + str(event))
        raise Exception("stop here!!")
        return 1

    def _increase_poignancy(self, score):
        self.status["poignancy"]["current"] += score
        self.status["poignancy"]["num_event"] += 1

    def get_curr_tile(self):
        return self.maze.tile_at(self.coord)

    def get_curr_event(self, as_act=True):
        action = self.actions[-1]
        return action.event if as_act else action.obj_event

    def to_dict(self):
        return {
            "status": self.status,
            "schedule": self.schedule.to_dict(),
            "associate": self.associate.to_dict(),
        }
