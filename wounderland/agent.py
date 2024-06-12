"""wounderland.agent"""

import math
import random
import datetime
from functools import wraps
from wounderland import memory, prompt, utils
from wounderland.model.llm_model import create_llm_model


def check_llm(ret=None):
    def checker(func):
        @wraps(func)
        def inner_checker(agent, *args, **kwargs):
            if not agent.llm_available():
                return ret
            return func(agent, *args, **kwargs)

        return inner_checker

    return checker


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
        self.scratch = prompt.Scratch(self.name, config["scratch"], self.logger)

        # status
        self.status = {"poignancy": {"current": 0, "num_event": 0}}
        self.status = utils.update_dict(self.status, config.get("status", {}))
        self.plan = config.get("plan", {})

        # action and events
        if "actions" in config:
            self.actions = [memory.Action.from_dict(a) for a in config["actions"]]
        else:
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
            "tile": self.maze.tile_at(self.coord).abstract(),
            "concepts": [c.abstract() for c in self.concepts],
            "actions": [a.abstract() for a in self.actions],
            "associate": self.associate.abstract(),
        }
        if self.schedule.scheduled():
            des["schedule"] = self.schedule.abstract()
        if self.llm_available():
            des["llm"] = self._llm.get_summary()
        if self.plan.get("path"):
            des["path"] = "-".join(
                ["{},{}".format(c[0], c[1]) for c in self.plan["path"]]
            )
        return utils.dump_dict(des)

    def reset_user(self, user):
        if self.think_config["mode"] == "llm" and not self._llm:
            self._llm = create_llm_model(**self.think_config["llm"], keys=user.keys)
        self.make_schedule()

    def remove_user(self):
        self._llm = None

    def make_schedule(self):
        if not self.schedule.scheduled():
            # make init schedule
            self.schedule.created_at = utils.get_timer().get_date()
            wake_up = self.completion("wake_up")
            init_schedule = self.completion("schedule_init", wake_up)
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
                daily_schedule = self.completion(
                    "schedule_daily", wake_up, schedule, init_schedule
                )
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
            decompose_schedule = self.completion(
                "schedule_decompose", plan, self.schedule
            )
            decompose, start = [], plan["start"]
            for describe, duration in decompose_schedule:
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
        return self.schedule.current_plan()

    def move(self, coord, path=None):
        events = {}

        def _update_tile(coord):
            tile = self.maze.tile_at(coord)
            if not tile.update_events(self.get_event()):
                tile.add_event(self.get_event())
            self.maze.update_obj(coord, self.get_event(False))
            return {e: coord for e in tile.get_events()}

        if self.is_awake():
            if self.coord and self.coord != coord:
                tile = self.get_tile()
                tile.remove_events(subject=self.name)
                if tile.has_address("game_object"):
                    addr = tile.get_address("game_object")
                    self.maze.update_obj(
                        self.coord, memory.Event(addr[-1], address=addr)
                    )
                events.update({e: self.coord for e in tile.get_events()})
            if not path:
                events.update(_update_tile(coord))
            self.coord = coord
            self.path = path or []
        elif self.coord:
            events.update(_update_tile(self.coord))
        return events

    def think(self, status, agents):
        self.move(status["coord"], status.get("path"))
        plan, _ = self.make_schedule()
        if plan["describe"] == "sleeping" and self.is_awake():
            address = self.spatial.find_address("sleeping", as_list=True)
            action = memory.Action(
                memory.Event(self.name, "is", "sleeping", address=address, emoji="😴"),
                memory.Event(
                    address[-1],
                    "occupied by",
                    self.name,
                    address=address,
                    emoji="🛌",
                ),
                duration=plan["duration"],
                start=utils.daily_time(plan["start"]),
            )
            self.actions = [action]
        if self.is_awake():
            self.percept()
            self.make_plan(agents)
            self.reflect()
        self.plan = {
            "name": self.name,
            "path": self.find_path(agents),
            "emojis": {"agent": self.get_event().emoji},
        }
        return self.plan

    def percept(self):
        scope = self.maze.get_scope(self.coord, self.percept_config)
        # add spatial memory
        for tile in scope:
            if tile.has_address("game_object"):
                self.spatial.add_leaf(tile.address)
        events, arena = {}, self.get_tile().get_address("arena")
        # gather events in scope
        for tile in scope:
            if not tile.events or tile.get_address("arena") != arena:
                continue
            dist = math.dist(tile.coord, self.coord)
            for event in tile.get_events():
                if dist < events.get(event, float("inf")):
                    events[event] = dist
        events = list(sorted(events.keys(), key=lambda k: events[k]))
        # get concepts
        self.concepts = []
        for event in events[: self.percept_config["att_bandwidth"]]:
            recent_events = {n.event: n for n in self.associate.retrieve_events()}
            if event in recent_events:
                self.concepts.append(recent_events[event])
            else:
                chats = []
                if event.fit(self.name, "chat with"):
                    node = self._add_concept(
                        self.get_event(), "chat", filling=self.scratch.chat
                    )
                    chats = [node.name]
                node = self._add_concept(event, "event", filling=chats)
                self._increase_poignancy(node.poignancy)
                self.concepts.append(node)
        self.concepts = [c for c in self.concepts if c.event.subject != self.name]

    def make_plan(self, agents):
        if not self.path:
            self.actions = [a for a in self.actions if not a.finished()]
            if not self.actions:
                self.actions.append(self._determine_action())
        self._reaction(agents)

    def reflect(self):
        if self.status["poignancy"]["current"] >= self.think_config["poignancy_max"]:
            self.status["poignancy"]["current"] = 0
            self.status["poignancy"]["num_event"] = 0
            raise Exception("should reflect!!")

    def find_path(self, agents):
        if not self.is_awake():
            return []
        if self.path:
            return self.path
        address = self.get_event().address
        if address[0] == "<waiting>":
            return []
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
        elif address[-1] == "<random>":
            target_tiles = self.maze.get_address_tiles(address[:-1])
        else:
            target_tiles = self.maze.get_address_tiles(address)

        # filter tile with self event
        def _ignore_target(t_coord):
            if list(t_coord) == list(self.coord):
                return True
            events = self.maze.tile_at(t_coord).get_events()
            if any(e.subject in agents for e in events):
                return True
            return False

        target_tiles = [t for t in target_tiles if not _ignore_target(t)]
        if not target_tiles:
            return []
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
            tile = self.get_tile()
            kwargs = {
                "describes": describes,
                "spatial": self.spatial,
                "address": tile.get_address("world", as_list=True),
            }
            kwargs["address"].append(
                self.completion("determine_sector", **kwargs, tile=tile)
            )
            arenas = self.spatial.get_leaves(kwargs["address"])
            if len(arenas) == 1:
                kwargs["address"].append(arenas[0])
            else:
                kwargs["address"].append(self.completion("determine_arena", **kwargs))
            objs = self.spatial.get_leaves(kwargs["address"])
            if len(objs) == 0:
                kwargs["address"].append("<random>")
            elif len(objs) == 1:
                kwargs["address"].append(objs[0])
            else:
                kwargs["address"].append(self.completion("determine_object", **kwargs))
            address = kwargs["address"]

        # create action && object events
        def _make_event(subject, describe):
            emoji = self.completion("describe_emoji", describe)
            if subject == self.name:
                args = self.completion("describe_event", subject, describe)
                return memory.Event(*args, address=address, emoji=emoji)
            return memory.Event(subject, "is", describe, address=address, emoji=emoji)

        event = _make_event(self.name, describes[-1])
        obj_describe = self.completion("describe_object", address[-1], describes[-1])
        obj_event = _make_event(address[-1], obj_describe)
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
        def _skip(event):
            if not event.address or "sleeping" in event.describe:
                return False
            return True

        if self.actions[-1].act_type == "chat":
            return True
        if "<waiting>" in self.get_event().address:
            return True
        if utils.get_timer().daily_duration(mode="hour") >= 23:
            return True
        if _skip(self.get_event()) or _skip(other.get_event()):
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
        if not self.completion("decide_talk", self, other, focus):
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
        if not self.completion("decide_react", self, other, focus):
            return False

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
        # if self.llm_available():
        #    return (desc, self._llm.embedding(desc)), poignancy
        return (desc, None), poignancy

    def _evaluate_event(self, event):
        if event.fit(None, "is", "idle"):
            return 1
        return self.completion("poignancy_event", event)

    def _evaluate_chat(self, event):
        print("should evaluare chat " + str(event))
        raise Exception("stop here!!")
        return 1

    def _increase_poignancy(self, score):
        self.status["poignancy"]["current"] += score
        self.status["poignancy"]["num_event"] += 1

    def get_tile(self):
        return self.maze.tile_at(self.coord)

    def get_event(self, as_act=True):
        action = self.actions[-1]
        return action.event if as_act else action.obj_event

    def is_awake(self):
        if self.get_event().fit(self.name, "is", "sleeping"):
            return False
        return True

    def llm_available(self):
        if not self._llm:
            return False
        return self._llm.is_available()

    def completion(self, func_hint, *args, **kwargs):
        assert hasattr(
            self.scratch, "prompt_" + func_hint
        ), "Can not find func prompt_{} from scratch".format(func_hint)
        func = getattr(self.scratch, "prompt_" + func_hint)
        prompt = func(*args, **kwargs)
        if self.llm_available():
            ret = self._llm.completion(**prompt, caller=func_hint)
            self.logger.debug("<COMPLETION>:\n{}\n".format(ret))
            return ret
        ret = prompt.get("failsafe")
        title = "{}.{} @ {}".format(
            self.name, func_hint, utils.get_timer().get_date("%H:%M:%S")
        )
        msg = "{}<FAILSAFE>:\n{}\n".format(utils.split_line(title), ret)
        self.logger.debug(msg)
        return ret

    def to_dict(self):
        return {
            "coord": self.coord,
            "status": self.status,
            "schedule": self.schedule.to_dict(),
            "associate": self.associate.to_dict(),
            "actions": [a.to_dict() for a in self.actions],
        }
