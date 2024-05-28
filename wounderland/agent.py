"""wounderland.agent"""

import re
import math
import random
from datetime import datetime
from wounderland import memory, utils
from wounderland.model.llm_model import create_llm_model


class Scratch:
    def __init__(self, name, config):
        self.name = name
        self.config = config

        # <chat> is a list of list that saves a conversation between two personas.
        # It comes in the form of: [["Dolores Murphy", "Hi"],
        #                           ["Maeve Jenson", "Hi"] ...]
        self.chat = None

        """
        # REFLECTION VARIABLES
        self.concept_forget = 100
        self.daily_reflection_time = 60 * 3
        self.daily_reflection_size = 5
        self.overlap_reflect_th = 2
        self.kw_strg_event_reflect_th = 4
        self.kw_strg_thought_reflect_th = 4

        # New reflection variables
        self.recency_w = 1
        self.relevance_w = 1
        self.importance_w = 1
        self.recency_decay = 0.99
        self.importance_trigger_max = 150
        self.importance_trigger_curr = self.importance_trigger_max
        self.importance_ele_n = 0
        self.thought_count = 5
        """

        """
        # PERSONA PLANNING
        # <daily_req> is a list of various goals the persona is aiming to achieve
        # today.
        # e.g., ['Work on her paintings for her upcoming show',
        #        'Take a break to watch some TV',
        #        'Make lunch for herself',
        #        'Work on her paintings some more',
        #        'Go to bed early']
        # They have to be renewed at the end of the day, which is why we are
        # keeping track of when they were first generated.
        self.daily_req = []
        # <f_daily_schedule> denotes a form of long term planning. This lays out
        # the persona's daily plan.
        # Note that we take the long term planning and short term decomposition
        # appoach, which is to say that we first layout hourly schedules and
        # gradually decompose as we go.
        # Three things to note in the example below:
        # 1) See how "sleeping" was not decomposed -- some of the common events
        #    really, just mainly sleeping, are hard coded to be not decomposable.
        # 2) Some of the elements are starting to be decomposed... More of the
        #    things will be decomposed as the day goes on (when they are
        #    decomposed, they leave behind the original hourly action description
        #    in tact).
        # 3) The latter elements are not decomposed. When an event occurs, the
        #    non-decomposed elements go out the window.
        # e.g., [['sleeping', 360],
        #         ['wakes up and ... (wakes up and stretches ...)', 5],
        #         ['wakes up and starts her morning routine (out of bed )', 10],
        #         ...
        #         ['having lunch', 60],
        #         ['working on her painting', 180], ...]
        self.f_daily_schedule = []
        # <f_daily_schedule_hourly_org> is a replica of f_daily_schedule
        # initially, but retains the original non-decomposed version of the hourly
        # schedule.
        # e.g., [['sleeping', 360],
        #        ['wakes up and starts her morning routine', 120],
        #        ['working on her painting', 240], ... ['going to bed', 60]]
        self.f_daily_schedule_hourly_org = []

        # CURR ACTION
        # <address> is literally the string address of where the action is taking
        # place.  It comes in the form of
        # "{world}:{sector}:{arena}:{game_objects}". It is important that you
        # access this without doing negative indexing (e.g., [-1]) because the
        # latter address elements may not be present in some cases.
        # e.g., "dolores double studio:double studio:bedroom 1:bed"
        self.act_address = None
        # <start_time> is a python datetime instance that indicates when the
        # action has started.
        self.act_start_time = None
        # <duration> is the integer value that indicates the number of minutes an
        # action is meant to last.
        self.act_duration = None
        # <description> is a string description of the action.
        self.act_description = None
        # <pronunciatio> is the descriptive expression of the self.description.
        # Currently, it is implemented as emojis.
        self.act_pronunciatio = None
        # <event_form> represents the event triple that the persona is currently
        # engaged in.
        self.act_event = (self.name, None, None)

        # <obj_description> is a string description of the object action.
        self.act_obj_description = None
        # <obj_pronunciatio> is the descriptive expression of the object action.
        # Currently, it is implemented as emojis.
        self.act_obj_pronunciatio = None
        # <obj_event_form> represents the event triple that the action object is
        # currently engaged in.
        self.act_obj_event = (self.name, None, None)

        # <chatting_with> is the string name of the persona that the current
        # persona is chatting with. None if it does not exist.
        self.chatting_with = None
        # <chat> is a list of list that saves a conversation between two personas.
        # It comes in the form of: [["Dolores Murphy", "Hi"],
        #                           ["Maeve Jenson", "Hi"] ...]
        self.chat = None
        # <chatting_with_buffer>
        # e.g., ["Dolores Murphy"] = self.vision_r
        self.chatting_with_buffer = dict()
        self.chatting_end_time = None

        # <path_set> is True if we've already calculated the path the persona will
        # take to execute this action. That path is stored in the persona's
        # scratch.planned_path.
        self.act_path_set = False
        # <planned_path> is a list of x y coordinate tuples (tiles) that describe
        # the path the persona is to take to execute the <curr_action>.
        # The list does not include the persona's current tile, and includes the
        # destination tile.
        # e.g., [(50, 10), (49, 10), (48, 10), ...]
        self.planned_path = []
        """

    def _base_desc(self, date=None):
        date = date or datetime.now()
        return """Name: {0}
Age: {1}
Innate traits: {2}
Learned traits: {3}
Currently: {4}
Lifestyle: {5}
Daily plan requirement: {6}
Current Date: {7}\n""".format(
            self.name,
            self.config["age"],
            self.config["innate"],
            self.config["learned"],
            self.config["currently"],
            self.config["lifestyle"],
            self.config["daily_plan_req"],
            date.strftime("%A %B %d"),
        )

    def _format_output(self, prompt, style, example="", instruction=""):
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in {style}."
        if instruction:
            prompt += f"{instruction}"
        if example:
            prompt += f"\nExample output {style}:\n{example}"
        return prompt

    def prompt_wake_up(self, date=None):
        prompt = self._base_desc(date)
        prompt += """\nIn general, {}\n{}'s wake up hour:""".format(
            self.config["lifestyle"], self.name
        )
        prompt = self._format_output(
            prompt, "hour", "8:00 am", "The output should ONLY contain ONE hour value."
        )

        def _callback(response):
            response = response.replace("\n", "").strip()
            hours = re.findall(r"\d:00 am+", response)
            if len(hours) == 1:
                return int(hours[0].split(":")[0])
            hours = re.findall(r"\d am+", response)
            if len(hours) == 1:
                return int(hours[0].split(" am")[0])
            raise Exception("Can not find single integer in " + str(response))

        return {"prompt": prompt, "callback": _callback}

    def prompt_daily_schedule(self, wake_up, date=None):
        date = date or datetime.now()
        prompt = self._base_desc(date)
        prompt += """\n\nIn general, {}""".format(self.config["lifestyle"])
        prompt += "\nToday is {}. Here is {}'s plan today in broad-strokes ".format(
            date.strftime("%A %B %d"), self.name
        )
        prompt += "(with the time of the day. e.g., have a lunch at 12:00 pm, watch TV from 7 to 8 pm):"
        prompt += "1) wake up and complete the morning routine at {}:00 am. 2)".format(
            wake_up
        )
        prompt = self._format_output(
            prompt, "lines", instruction="Each line consist of index and plan"
        )

        def _callback(response):
            schedules = []
            for sch in response.split("\n"):
                if ")" in sch:
                    schedules.append(sch.split(") ")[1].strip())
                else:
                    schedules.append(sch.strip())
            return schedules

        return {"prompt": prompt, "callback": _callback}

    def prompt_hourly_schedule(self, wake_up, schedule, daily_schedule, date=None):
        date = date or datetime.now()
        prompt = "Hourly schedule format:\n"
        for hour, _ in schedule:
            prompt += f"[{hour}] Activity: [Fill in]\n"
        prompt += "========\n"
        prompt += self._base_desc(date)
        prompt += "\nHere the originally intended hourly breakdown of {}'s schedule today:\n".format(
            self.name
        )
        prompt += " ".join(
            ["{}) {}".format(idx, sch) for idx, sch in enumerate(daily_schedule)]
        )
        prompt += "\n\n" + "\n".join(
            [
                "[{}] Activity: {} is {}".format(h, self.name, s)
                for h, s in schedule[: wake_up + 1]
            ]
        )

        def _callback(response):
            left_schedule, prefix = {}, "{} is".format(self.name)

            def _add_schedule(line, stamps):
                if len(stamps) == 1:
                    plan = line
                    if "[{}]".format(stamps[0]) in line:
                        plan = line.split("[{}]".format(stamps[0]))[1].strip()
                    if prefix in line:
                        plan = line.split(prefix)[1].strip()
                    left_schedule[stamps[0]] = plan
                    return True
                return False

            for line in response.split("\n"):
                stamps = re.findall(r"\d{1,2}:00 AM", line)
                if _add_schedule(line, stamps):
                    continue
                stamps = re.findall(r"\d{1,2}:00 PM", line)
                if _add_schedule(line, stamps):
                    continue
            return left_schedule

        return {"prompt": prompt, "callback": _callback}

    def prompt_poignancy(self, event, date=None):
        prompt = self._base_desc(date)
        prompt += """\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for {}.

Event: {}
Rate (return a number between 1 to 10):""".format(
            self.name, event.sub_desc
        )
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += "Output the response to the prompt above in number. The output should ONLY contain ONE number value on the scale of 1 to 10.\n"
        prompt += "Example output json:\n"
        prompt += "5"

        def _callback(response):
            if response.isdigit():
                return int(response)
            hours = re.findall(r"\d+", response)
            if len(hours) == 1:
                return int(hours[0])
            raise Exception("Can not find single integer in " + str(response))

        return {"prompt": prompt, "callback": _callback}


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
        self.associate = memory.Associate(config["associate"])
        self.schedule = memory.Schedule(config["schedule"])
        self.scratch = Scratch(self.name, config["scratch"])

        # status
        self.status = {"poignancy": {"current": 0, "num_event": 0}}

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
                self.make_schedule()

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
            blank = memory.Event(obj_event.subject, None, None, None)
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
                self.increase_poignancy(event_poignancy)
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
        if self.think_config["mode"] == "llm" and self._llm:
            self.make_schedule()
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
        prompt = self.scratch.prompt_poignancy(event)
        print("prompt " + str(prompt))
        response = self._llm.completion(prompt)
        print("response " + str(response))
        raise Exception("stop here!!")

        return 1

    def evaluate_chat(self, event):
        if not self._llm:
            return 1
        return 1

    def increase_poignancy(self, score):
        self.status["poignancy"]["current"] += score
        self.status["poignancy"]["num_event"] += 1

    def make_schedule(self):
        if self.schedule.hourly_schedule:
            return
        # make daily schedule
        self.schedule.date = datetime.now()
        prompt = self.scratch.prompt_wake_up()
        wake_up = self._llm.completion(**prompt)
        print("[TMINFO] wake_up " + str(wake_up))
        prompt = self.scratch.prompt_daily_schedule(wake_up)
        self.schedule.daily_schedule = self._llm.completion(**prompt)
        print("self.schedule.daily_schedule " + str(self.schedule.daily_schedule))
        if self.associate.nodes:
            print("should adjust daily schedule!!")
            raise Exception("stop here!!")
        # make hourly schedule
        schedule_diversity = self.schedule.config["schedule_diversity"]
        hours = [str(i) + ":00 AM" for i in range(12)]
        hours += [str(i) + ":00 PM" for i in range(12)]
        hourly_schedule = {}
        for _ in range(self.schedule.config["schedule_max_try"]):
            schedule = [(h, "sleeping") for h in hours[:wake_up]]
            schedule += [(h, "") for h in hours[wake_up:]]
            prompt = self.scratch.prompt_hourly_schedule(
                wake_up, schedule, self.schedule.daily_schedule
            )
            hourly_schedule = self._llm.completion(**prompt)
            hourly_schedule.update({h: s for h, s in schedule[:wake_up]})
            print("hourly_schedule " + str(hourly_schedule))
            if len(set(hourly_schedule.values())) >= schedule_diversity:
                break
        hourly_schedule.update(
            {k: "sleeping" for k in hours if k not in hourly_schedule}
        )
        print("hourly_schedule " + str(hourly_schedule))

        hourly_compressed, prev = [], None
        for hour in hours:
            if hourly_schedule[hour] == prev:
                hourly_compressed[-1][1] += 60
                continue
            hourly_compressed.append([hourly_schedule[hour], 60])
            prev = hourly_schedule[hour]

        print("hourly_compressed " + str(hourly_compressed))
        raise Exception("sop here!!")

    def get_curr_tile(self):
        return self.maze.tile_at(self.coord)

    def get_curr_event(self, as_sub=True):
        if not self.act_address:
            return memory.Event(self.name if as_sub else "", None, None, None)
        return memory.Event(
            self.act_event[0] if as_sub else self.act_address,
            self.act_event[1],
            self.act_event[2],
            self.act_description,
        )
