"""wounderland.agent"""

import os
import math
import random
import datetime
from wounderland import memory, prompt, utils
from wounderland.model.llm_model import create_llm_model
from wounderland.memory.associate import Concept


class Agent:
    def __init__(self, config, maze, logger):
        self.name = config["name"]
        self.maze = maze
        self._llm = None
        self.logger = logger

        # agent config
        self.percept_config = config["percept"]
        self.think_config = config["think"]
        self.chat_iter = config.get("chat_iter", 8)

        # memory
        self.spatial = memory.Spatial(**config["spatial"])
        self.schedule = memory.Schedule(**config["schedule"])
        self.associate = memory.Associate(
            os.path.join(config["storage_root"], "associate"), **config["associate"]
        )
        self.concepts, self.chats = [], config.get("chats", [])

        # prompt
        self.scratch = prompt.Scratch(self.name, config["currently"], config["scratch"])

        # status
        status = {"poignancy": 0}
        self.status = utils.update_dict(status, config.get("status", {}))
        self.plan = config.get("plan", {})

        # record
        self.last_record = utils.get_timer().daily_duration()

        # action and events
        if "action" in config:
            self.action = memory.Action.from_dict(config["action"])
        else:
            tile = self.maze.tile_at(config["coord"])
            address = tile.get_address("game_object", as_list=True)
            self.action = memory.Action(
                memory.Event(self.name, address=address),
                memory.Event(address[-1], address=address),
            )

        # update maze
        self.coord, self.path = None, None
        self.move(config["coord"], config.get("path"))

    def abstract(self):
        des = {
            "name": self.name,
            "currently": self.scratch.currently,
            "tile": self.maze.tile_at(self.coord).abstract(),
            "status": self.status,
            "concepts": {c.node_id: c.abstract() for c in self.concepts},
            "chats": self.chats,
            "action": self.action.abstract(),
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
        return des

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def reset_user(self, user):
        if self.think_config["mode"] == "llm" and not self._llm:
            self._llm = create_llm_model(**self.think_config["llm"], keys=user.keys)
        if self._llm and not self.associate.index.queryable:
            self.associate.enable_index(self._llm)

    def remove_user(self):
        if self.llm_available():
            self._llm.disable()

    def completion(self, func_hint, *args, **kwargs):
        assert hasattr(
            self.scratch, "prompt_" + func_hint
        ), "Can not find func prompt_{} from scratch".format(func_hint)
        func = getattr(self.scratch, "prompt_" + func_hint)
        prompt = func(*args, **kwargs)
        title, msg = "{}.{}".format(self.name, func_hint), {}
        if self.llm_available():
            self.logger.info("{} -> {}".format(self.name, func_hint))
            output = self._llm.completion(**prompt, caller=func_hint)
            responses = self._llm.meta_responses
            msg = {"<PROMPT>": "\n" + prompt["prompt"] + "\n"}
            msg.update(
                {
                    "<RESPONSE[{}/{}]>".format(idx, len(responses)): "\n" + r + "\n"
                    for idx, r in enumerate(responses)
                }
            )
        else:
            output = prompt.get("failsafe")
        msg["<OUTPUT>"] = "\n" + str(output) + "\n"
        self.logger.debug(utils.block_msg(title, msg))
        return output

    def think(self, status, agents):
        events = self.move(status["coord"], status.get("path"))
        plan, _ = self.make_schedule()
        if plan["describe"] == "sleeping" and self.is_awake():
            self.logger.info("{} is going to sleep...".format(self.name))
            address = self.spatial.find_address("sleeping", as_list=True)
            self.action = memory.Action(
                memory.Event(self.name, "is", "sleeping", address=address, emoji="😴"),
                memory.Event(
                    address[-1],
                    "used by",
                    self.name,
                    address=address,
                    emoji="🛌",
                ),
                duration=plan["duration"],
                start=utils.get_timer().daily_time(plan["start"]),
            )
        if self.is_awake():
            self.percept()
            self.make_plan(agents)
            self.reflect()
        emojis = {}
        if self.action:
            emojis[self.name] = {"emoji": self.get_event().emoji, "coord": self.coord}
        for eve, coord in events.items():
            if eve.subject in agents:
                continue
            emojis[":".join(eve.address)] = {"emoji": eve.emoji, "coord": coord}
        self.plan = {
            "name": self.name,
            "path": self.find_path(agents),
            "emojis": emojis,
        }
        return self.plan

    def move(self, coord, path=None):
        events = {}

        def _update_tile(coord):
            tile = self.maze.tile_at(coord)
            if not self.action:
                return {}
            if not tile.update_events(self.get_event()):
                tile.add_event(self.get_event())
            obj_event = self.get_event(False)
            if obj_event:
                self.maze.update_obj(coord, obj_event)
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

    def make_schedule(self):
        if not self.schedule.scheduled():
            self.logger.info("{} is making schedule...".format(self.name))
            # update currently
            if self.associate.index.nodes_num > 0:
                self.associate.cleanup_index()
                focus = [
                    f"{self.name}'s plan for {utils.get_timer().daily_format()}.",
                    f"Important recent events for {self.name}'s life.",
                ]
                retrieved = self.associate.retrieve_focus(focus)
                self.logger.info(
                    "{} retrieved {} concepts".format(self.name, len(retrieved))
                )
                if retrieved:
                    plan = self.completion("retrieve_plan", retrieved)
                    thought = self.completion("retrieve_thought", retrieved)
                    self.scratch.currently = self.completion(
                        "retrieve_currently", plan, thought
                    )
            # make init schedule
            self.schedule.create = utils.get_timer().get_date()
            wake_up = self.completion("wake_up")
            init_schedule = self.completion("schedule_init", wake_up)
            # make daily schedule
            hours = [f"{i}:00 AM" for i in range(12)]
            hours += [f"{i}:00 PM" for i in range(12)]
            seed = [(h, "sleeping") for h in hours[:wake_up]]
            seed += [(h, "") for h in hours[wake_up:]]
            schedule = {}
            for _ in range(self.schedule.max_try):
                schedule = {h: s for h, s in seed[:wake_up]}
                schedule.update(
                    self.completion("schedule_daily", wake_up, seed, init_schedule)
                )
                if len(set(schedule.values())) >= self.schedule.diversity:
                    break

            def _to_duration(date_str):
                return utils.daily_duration(utils.to_date(date_str, "%I:%M %p"))

            schedule = {_to_duration(k): v for k, v in schedule.items()}
            starts = list(sorted(schedule.keys()))
            for idx, start in enumerate(starts):
                end = starts[idx + 1] if idx + 1 < len(starts) else 24 * 60
                self.schedule.add_plan(schedule[start], end - start)
            schedule_time = self.schedule.create.strftime("%A %B %d")
            thought = "This is {}'s plan for {}: {}".format(
                self.name, schedule_time, "; ".join(init_schedule)
            )
            event = memory.Event(
                self.name,
                "plan",
                schedule_time,
                describe=thought,
                address=self.get_tile().get_address(),
            )
            self._add_concept(
                "thought",
                event,
                expire=self.schedule.create + datetime.timedelta(days=30),
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

    def revise_schedule(self, event, start, duration, act_type="event"):
        self.action = memory.Action(
            event, act_type=act_type, start=start, duration=duration
        )
        plan, _ = self.schedule.current_plan()
        plan["decompose"] = self.completion(
            "schedule_revise", self.action, self.schedule
        )

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
        self.concepts, valid_num = [], 0
        for idx, event in enumerate(events[: self.percept_config["att_bandwidth"]]):
            recent_events = set(n.describe for n in self.associate.retrieve_events())
            if event.get_describe() not in recent_events:
                if event.object == "idle":
                    node = Concept.from_event(
                        "idle_" + str(idx), "event", event, poignancy=1
                    )
                else:
                    valid_num += 1
                    node_type = "chat" if event.fit(self.name, "chat with") else "event"
                    node = self._add_concept(node_type, event)
                    self.status["poignancy"] += node.poignancy
                self.concepts.append(node)
        self.concepts = [c for c in self.concepts if c.event.subject != self.name]
        self.logger.info(
            "{} percept {}/{} concepts".format(self.name, valid_num, len(self.concepts))
        )

    def make_plan(self, agents):
        if self._reaction(agents):
            return
        if self.path:
            return
        if self.action.finished():
            self.action = self._determine_action()

    def reflect(self):
        def _add_thought(thought, evidence=None):
            event = self.completion(
                "describe_event",
                self.name,
                thought,
                address=self.get_tile().get_address(),
            )
            return self._add_concept("thought", event, filling=evidence)

        if self.status["poignancy"] < self.think_config["poignancy_max"]:
            return
        nodes = self.associate.retrieve_events() + self.associate.retrieve_thoughts()
        if not nodes:
            return
        self.logger.info(
            "{} reflect(P{}/{}) with {} concepts...".format(
                self.name,
                self.status["poignancy"],
                self.think_config["poignancy_max"],
                len(nodes),
            )
        )
        nodes = sorted(nodes, key=lambda n: n.access, reverse=True)[
            : self.associate.max_importance
        ]
        # summary thought
        focus = self.completion("reflect_focus", nodes, 3)
        retrieved = self.associate.retrieve_focus(focus, reduce_all=False)
        for r_nodes in retrieved.values():
            thoughts = self.completion("reflect_insights", r_nodes, 5)
            for thought, evidence in thoughts:
                _add_thought(thought, evidence)
        # summary chats
        if self.chats:
            recorded, evidence = set(), []
            for name, _ in self.chats:
                if name == self.name or name in recorded:
                    continue
                node = self.associate.retrieve_chats(name)[-1]
                evidence.append(node.node_id)
            thought = self.completion("reflect_chat_planing", self.chats)
            _add_thought(f"For {self.name}'s planning: {thought}", evidence)
            thought = self.completion("reflect_chat_memory", self.chats)
            _add_thought(f"{self.name} {thought}", evidence)
        self.status["poignancy"] = 0
        self.chats = []

    def find_path(self, agents):
        if not self.is_awake():
            return []
        if self.path:
            return self.path
        address = self.get_event().address
        if address == self.get_tile().get_address():
            return []
        if address[0] == "<waiting>":
            return []
        if address[0] == "<persona>":
            target_tiles = self.maze.get_around(agents[address[1]].coord)
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
        self.logger.info("{} is determining action...".format(self.name))
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
            if len(objs) == 1:
                kwargs["address"].append(objs[0])
            elif len(objs) > 1:
                kwargs["address"].append(self.completion("determine_object", **kwargs))
            address = kwargs["address"]

        # create action && object events
        def _make_event(subject, describe):
            emoji = self.completion("describe_emoji", describe)
            return self.completion(
                "describe_event", subject, subject + " is " + describe, address, emoji
            )

        event = _make_event(self.name, describes[-1])
        obj_describe = self.completion("describe_object", address[-1], describes[-1])
        obj_event = _make_event(address[-1], obj_describe)
        return memory.Action(
            event,
            obj_event,
            duration=de_plan["duration"],
            start=utils.get_timer().daily_time(de_plan["start"]),
        )

    def _reaction(self, agents=None, ignore_words=None):
        focus = None
        ignore_words = ignore_words or ["is idle"]

        def _focus(concept):
            return concept.event.subject in agents

        def _ignore(concept):
            return any(i in concept.describe for i in ignore_words)

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
        other, focus = agents[focus.event.subject], self.associate.get_relation(focus)

        if self._chat_with(other, focus):
            return True
        if self._wait_other(other, focus):
            return True
        return False

    def _skip_react(self, other):
        def _skip(event):
            if not event.address or "sleeping" in event.get_describe(False):
                return True
            if event.predicate == "waiting to start":
                return True
            return False

        if utils.get_timer().daily_duration(mode="hour") >= 23:
            return True
        if _skip(self.get_event()) or _skip(other.get_event()):
            return True
        return False

    def _chat_with(self, other, focus):
        if self._skip_react(other):
            return False
        if other.path:
            return False
        if self.action.act_type == "chat" or other.action.act_type == "chat":
            return False
        chats = self.associate.retrieve_chats(other.name)
        if chats and utils.get_timer().get_delta(chats[0].expire) < 60:
            return False
        if not self.completion("decide_chat", self, other, focus, chats):
            return False
        self.logger.info("{} decides chat with {}".format(self.name, other.name))
        start, chats = utils.get_timer().get_date(), []
        relations = [
            self.completion("summarize_relation", self, other.name),
            other.completion("summarize_relation", other, self.name),
        ]
        for _ in range(self.chat_iter):
            utt, end = self.completion(
                "generate_chat", self, other, relations[0], chats
            )
            chats.append((self.name, utt))
            if not end:
                utt, end = other.completion(
                    "generate_chat", other, self, relations[1], chats
                )
                chats.append((other.name, utt))
            if end:
                break
        self.logger.info(
            "{} and {} has chats\n  {}".format(
                self.name,
                other.name,
                "\n  ".join(["{}: {}".format(n, c) for n, c in chats]),
            )
        )
        self.chats.extend(chats)
        chat_summary = self.completion("summarize_chats", chats)
        duration = int(sum([len(c[1]) for c in chats]) / 240)
        self.schedule_chat(
            chat_summary, start, duration, other, ["<persona>", other.name]
        )
        other.schedule_chat(chat_summary, start, duration, self)
        return True

    def _wait_other(self, other, focus):
        if self._skip_react(other):
            return False
        if not self.path:
            return False
        if self.get_event().address != other.get_tile().get_address():
            return False
        if not self.completion("decide_wait", self, other, focus):
            return False
        self.logger.info("{} decides wait to {}".format(self.name, other.name))
        start = utils.get_timer().get_date()
        duration = other.action.end - start
        event = memory.Event(
            self.name,
            "waiting to start",
            self.get_event().get_describe(False),
            address=["<waiting>"] + self.get_event().address,
            emoji="⌛",
        )
        self.revise_schedule(event, start, duration)

    def schedule_chat(self, chats_summary, start, duration, other, address=None):
        event = memory.Event(
            self.name,
            "chat with",
            other.name,
            describe=chats_summary,
            address=address or self.get_tile().get_address(),
            emoji="💬",
        )
        self.revise_schedule(event, start, duration, act_type="chat")

    def _add_concept(
        self,
        e_type,
        event,
        create=None,
        expire=None,
        filling=None,
    ):
        if event.fit(None, "is", "idle"):
            poignancy = 1
        elif e_type == "chat":
            poignancy = self.completion("poignancy_chat", event)
        else:
            poignancy = self.completion("poignancy_event", event)
        return self.associate.add_node(
            e_type,
            event,
            poignancy,
            create=create,
            expire=expire,
            filling=filling,
        )

    def get_tile(self):
        return self.maze.tile_at(self.coord)

    def get_event(self, as_act=True):
        return self.action.event if as_act else self.action.obj_event

    def is_awake(self):
        if not self.action:
            return True
        if self.get_event().fit(self.name, "is", "sleeping"):
            return False
        return True

    def llm_available(self):
        if not self._llm:
            return False
        return self._llm.is_available()

    def to_dict(self, with_action=True):
        info = {
            "status": self.status,
            "schedule": self.schedule.to_dict(),
            "associate": self.associate.to_dict(),
            "chats": self.chats,
            "currently": self.scratch.currently,
        }
        if with_action:
            info.update(
                {
                    "coord": self.coord,
                    "path": self.plan.get("path", []),
                    "action": self.action.to_dict(),
                }
            )
        return info
