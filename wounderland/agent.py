"""wounderland.agent"""

import re
import math
import random
import datetime
from wounderland import memory, utils
from wounderland.model.llm_model import create_llm_model


class Scratch:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.chat = None

    def _base_desc(self, date=None):
        date = date or datetime.datetime.now()
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
            self.config["daily_plan"],
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

    def prompt_schedule_roughly(self, wake_up, date=None):
        date = date or datetime.datetime.now()
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
            plan = []
            for sch in response.split("\n"):
                if ")" in sch:
                    plan.append(sch.split(") ")[1].strip().strip("."))
                else:
                    plan.append(sch.strip().strip("."))
            return plan

        return {"prompt": prompt, "callback": _callback}

    def prompt_schedule_daily(self, wake_up, schedule, daily_schedule, date=None):
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
            left_schedule = {}

            def _add_schedule(line, stamps):
                if len(stamps) == 1:
                    keywords = [
                        "[{}]".format(stamps[0]),
                        "{} is".format(self.name),
                        "{} is".format(self.name.split(" ")[0]),
                        self.name,
                        self.name.split(" ")[0],
                    ]
                    plan = line
                    for key in keywords:
                        if key in plan:
                            plan = plan.split(key)[1].strip()
                    left_schedule[stamps[0]] = plan
                    return True
                return False

            for line in response.split("\n"):
                stamps = re.findall(r"\d{1,2}:00 AM", line)
                if not _add_schedule(line, stamps):
                    stamps = re.findall(r"\d{1,2}:00 PM", line)
                    _add_schedule(line, stamps)
            return left_schedule

        return {"prompt": prompt, "callback": _callback}

    def prompt_schedule_hourly(self, idx, schedule, date=None):
        date = date or datetime.datetime.now()

        def _get_plan(index):
            start, end = schedule.get_period(index, hourly=False)
            plan = schedule.get_plan(index, hourly=False)
            return f"{start} ~ {end}, {self.name} is planning on {plan}"

        prompt = """Describe subtasks in 5 min increments. 
---
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: {kitchen, bedroom, dining, porch, office, bathroom, living room, hallway}.
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.s

Today is Saturday May 10. From 08:00am ~09:00am, Kelly is planning on having breakfast, from 09:00am ~ 12:00pm, Kelly is planning on working on the next day's kindergarten lesson plan, and from 12:00 ~ 13pm, Kelly is planning on taking a break. 
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Kelly is reviewing the kindergarten curriculum standards. (duration in minutes: 15, minutes left: 165)
2) Kelly is brainstorming ideas for the lesson. (duration in minutes: 30, minutes left: 135)
3) Kelly is creating the lesson plan. (duration in minutes: 30, minutes left: 105)
4) Kelly is creating materials for the lesson. (duration in minutes: 30, minutes left: 75)
5) Kelly is taking a break. (duration in minutes: 15, minutes left: 60)
6) Kelly is reviewing the lesson plan. (duration in minutes: 30, minutes left: 30)
7) Kelly is making final changes to the lesson plan. (duration in minutes: 15, minutes left: 15)
8) Kelly is printing the lesson plan. (duration in minutes: 10, minutes left: 5)
9) Kelly is putting the lesson plan in her bag. (duration in minutes: 5, minutes left: 0)
---\n"""
        prompt += self._base_desc(date)
        all_indices = range(max(idx - 1, 0), min(idx + 2, len(schedule.daily_schedule)))
        prompt += f'\nToday is {date.strftime("%B %d, %Y")}. From ' + ", ".join(
            [_get_plan(i) for i in all_indices]
        )
        start, end = schedule.get_period(idx, hourly=False)
        duration = schedule.get_plan(idx, hourly=False)
        plan = schedule.get_duration(idx, hourly=False)
        prompt += f"\nIn 5 min increments, list the subtasks {self.name} does when {self.name} is {duration}"
        prompt += f" from {start} ~ {end} (total duration in minutes {plan}):\n"
        prompt += f"1) {self.name} is"

        def _callback(response):
            hourly_schedule, left = [], schedule.get_duration(idx, hourly=False)
            keywords = [
                "{} is".format(self.name),
                "{} is".format(self.name.split(" ")[0]),
                self.name,
                self.name.split(" ")[0],
            ]
            for line in response.split("\n"):
                stamps = re.findall(r"\(duration in minutes: \d{1,2}", line)
                if len(stamps) == 1:
                    plan = line.split(stamps[0])[0]
                    for key in keywords:
                        if key in plan:
                            plan = plan.split(key)[1]
                    duration = int(stamps[0].split(":")[1].strip())
                    hourly_schedule.append((plan.strip().strip("."), duration))
                    left -= duration
            if left > 0:
                hourly_schedule.append(("idle", left))
            return hourly_schedule

        return {"prompt": prompt, "callback": _callback}

    def prompt_plan_sector(self, plan, spatial, tile, dst_address):
        prompt = """Task -- choose an appropriate area from the area options for a task at hand.\n
Sam Kim lives in {Sam Kim's house} that has Sam Kim's room, bathroom, kitchen.
Sam Kim is currently in {Sam Kim's house} that has Sam Kim's room, bathroom, kitchen.
Area options: {Sam Kim's house, The Rose and Crown Pub, Hobbs Cafe, Oak Hill College, Johnson Park, Harvey Oak Supply Store, The Willows Market and Pharmacy}.
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options", verbatim.
For taking a walk, Sam Kim should go to the following area: {Johnson Park}
---
Jane Anderson lives in {Oak Hill College Student Dormatory} that has Jane Anderson's room.
Jane Anderson is currently in {Oak Hill College} that has a classroom, library.
Area options: {Oak Hill College Student Dormatory, The Rose and Crown Pub, Hobbs Cafe, Oak Hill College, Johnson Park, Harvey Oak Supply Store, The Willows Market and Pharmacy}.
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options", verbatim.
For eating dinner, Jane Anderson should go to the following area: {Hobbs Cafe}
---
"""
        address = spatial.find_address("living_area", as_list=True)[:-1]
        arenas = " ".join(spatial.get_leaves(address))
        prompt += f"{self.name} lives in {{{address[-1]}}} that has {arenas}.\n"
        curr_address = tile.get_address("sector", as_list=True)
        curr_arenas = " ".join(spatial.get_leaves(curr_address))
        prompt += f"{self.name} is currently in {{{curr_address[-1]}}} that has {curr_arenas}.\n"
        prompt += f'{self.config["daily_plan"]}.\n'
        curr_sectors = ", ".join(spatial.get_leaves(dst_address))
        prompt += f"Area options: {{{curr_sectors}}}.\n"
        prompt += """* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options", verbatim.\n"""
        curr_plans = re.findall(r"\((.+?)\)", plan)
        if len(curr_plans) == 1:
            plan = plan.split("(" + curr_plans[0])[0].strip()
        prompt += f"For {plan}, {self.name} should go to the following area: " + "{"
        print("\n\n[TMINFO] sector prompt " + str(prompt))

        def _callback(response):
            print("\nsector response " + str(response))
            key = f"{self.name} should go to the following area: " + "{"
            sectors = spatial.get_leaves(dst_address)
            default = spatial.find_address("living_area", as_list=True)[-2]
            for line in response.split("\n"):
                if key not in line:
                    continue
                sector = line.split(key)[1].strip("}")
                if sector not in sectors:
                    return default
                return sector
            raise Exception("Can not find sector for plan " + str(plan))

        return {"prompt": prompt, "callback": _callback}

    def prompt_plan_arena(self, plan, spatial, tile, dst_address):
        prompt = """Jane Anderson is in kitchen in Jane Anderson's house.
Jane Anderson is going to Jane Anderson's house that has the following areas: {kitchen,  bedroom, bathroom}.
* Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
* Must be one of the given areas, verbatim.
Jane Anderson is making meal. For cooking, Jane Anderson should go to the area in Jane Anderson's house: {kitchen}
---
Tom Watson is in common room in Tom Watson's apartment. 
Tom Watson is going to Hobbs Cafe that has the following areas: {cafe}.
* Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
* Must be one of the given areas, verbatim.
Tom Watson is eating breakfast. For getting coffee, Tom Watson should go to the area in Hobbs Cafe: {cafe}
---
"""
        curr_address = tile.get_address("arena", as_list=True)
        prompt += f"{self.name} is in {curr_address[-1]} in {curr_address[-2]}\n"
        arenas = ", ".join(spatial.get_leaves(dst_address))
        prompt += f"{self.name} is going to {dst_address[-1]} that has the following areas: {{{arenas}}}\n"
        prompt += "* Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.\n"
        prompt += "* Must be one of the given areas, verbatim.\n"
        curr_plans = re.findall(r"\((.+?)\)", plan)
        if len(curr_plans) == 1:
            curr_plan = curr_plans[0]
            plan = plan.split("(" + curr_plan)[0].strip()
        else:
            curr_plan = plan
        prompt += (
            f"{self.name} is {plan}. For {curr_plan}, {self.name} should go to the area in {dst_address[-1]}: "
            + "{"
        )
        print("\n\n[TMINFO] arena prompt " + str(prompt))

        def _callback(response):
            print("\narena response " + str(response))
            key = f"{self.name} should go to the area in {dst_address[-1]}: " + "{"

            arenas = spatial.get_leaves(dst_address)
            print("arenas " + str(arenas))
            default = spatial.find_address("living_area", as_list=True)[-1]
            print("default " + str(default))
            for line in response.split("\n"):
                print("get line " + str(line))
                if key not in line:
                    continue
                arena = line.split(key)[1].strip("}")
                print("get arena " + str(arena))
                if arena not in arenas:
                    return default
                return arena
            raise Exception("Can not find arena for plan " + str(plan))

        return {"prompt": prompt, "callback": _callback}


class Action:
    def __init__(
        self,
        event,
        act_type,
        address=None,
        describe=None,
        start=None,
        duration=None,
    ):
        self.event = event
        self.act_type = act_type
        self.address = address
        self.describe = describe
        self.start = start or datetime.datetime.now()
        self.duration = duration

    def __str__(self):
        des = {
            "finished": self.finished(),
            "event({})".format(self.act_type): self.event,
            "address": self.address,
            "describe": self.describe,
        }
        if self.duration:
            des["duration"] = "{}(from {})".format(
                self.duration, self.start.strftime("%m%d-%H:%M")
            )
        else:
            des["start"] = self.start.strftime("%m%d-%H:%M")
        return utils.dump_dict(des)

    def finished(self):
        if not self.address:
            return True
        if self.act_type == "chat":
            end_time = self.end
        else:
            end_time = self.start + datetime.timedelta(minutes=self.duration)
        return end_time >= datetime.datetime.now()


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

        # action and events
        self.actions = [Action(memory.Event(self.name), "event")]
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
            if self._llm and not self.schedule.scheduled():
                self.make_schedule()

    def remove_user(self):
        self._llm = None

    def make_schedule(self):
        # make daily plan
        self.schedule.created_at = datetime.datetime.now()
        prompt = self.scratch.prompt_wake_up()
        wake_up = self._llm.completion(**prompt)
        prompt = self.scratch.prompt_schedule_roughly(wake_up)
        roughly_schedule = self._llm.completion(**prompt)
        if self.associate.nodes:
            print("should adjust daily schedule!!")
            raise Exception("stop here!!")
        # make hourly schedule
        hours = [str(i) + ":00 AM" for i in range(12)]
        hours += [str(i) + ":00 PM" for i in range(12)]
        daily_schedule = {}
        for _ in range(self.schedule.max_try):
            schedule = [(h, "sleeping") for h in hours[:wake_up]]
            schedule += [(h, "") for h in hours[wake_up:]]
            prompt = self.scratch.prompt_schedule_daily(
                wake_up, schedule, roughly_schedule
            )
            daily_schedule = self._llm.completion(**prompt)
            daily_schedule.update({h: s for h, s in schedule[:wake_up]})
            if len(set(daily_schedule.values())) >= self.schedule.diversity:
                break
        daily_schedule.update({k: "asleep" for k in hours if k not in daily_schedule})
        prev = None
        for hour in hours:
            if daily_schedule[hour] == prev:
                self.schedule.extend_duration(-1, 60, hourly=False)
                continue
            self.schedule.add_schedule(daily_schedule[hour], 60, hourly=False)
            prev = daily_schedule[hour]
        # make daily schedule
        for idx, (plan, duration) in enumerate(self.schedule.daily_schedule):
            if self.schedule.decompose(plan, duration):
                prompt = self.scratch.prompt_schedule_hourly(idx, self.schedule)
                hourly_schedules = self._llm.completion(**prompt)
                hourly_schedules = [
                    ("{} ({})".format(plan, p), d) for p, d in hourly_schedules
                ]
                self.schedule.extend_schedules(hourly_schedules)
            else:
                self.schedule.add_schedule(plan, duration)
        duration = self.schedule.get_duration(-1, 0)
        if duration < 24 * 60:
            if self.schedule.get_plan(-1) == "sleeping":
                self.schedule.extend_duration(-1, 24 * 60 - duration)
            else:
                self.schedule.add_schedule("sleeping", 24 * 60 - duration)
        t_event = memory.Event(
            self.name, "plan", self.schedule.created_at.strftime("%A %B %d")
        )
        thought = f"This is {self.name}'s plan for {t_event.object}: " + "; ".join(
            roughly_schedule
        )
        self._add_concept(
            t_event,
            "thought",
            desc=thought,
            keywords={"plan"},
            expiration=self.schedule.created_at + datetime.timedelta(days=30),
        )

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
        ret_events = []
        for p_event in percept_events[: self.percept_config["att_bandwidth"]]:
            latest_events = self.associate.get_recent_events()
            if p_event not in latest_events:
                chats = []
                if p_event.fit(self.name, "chat with"):
                    node = self._add_concept(
                        self.get_curr_event(), "chat", filling=self.scratch.chat
                    )
                    chats = [node.name]
                node = self._add_concept(p_event, "event", filling=chats)
                self._increase_poignancy(node.poignancy)
                ret_events.append(node)

        # retrieve events
        def _get_info(event):
            return {
                "curr_event": event,
                "events": self.associate.retrieve_events(event),
                "thoughts": self.associate.retrieve_thoughts(event),
            }

        return {e.event.sub_desc: _get_info(e) for e in ret_events}

    def plan(self, agents, retrieved):
        plan = {"name": self.name, "direct": "stop"}
        if self.think_config["mode"] == "random":
            plan["direct"] = random.choice(["left", "right", "up", "down", "stop"])
            return plan
        if self._llm and not self.schedule.scheduled():
            self.make_schedule()

        """
        for k, info in retrieved.items():
            print("\n\nretrieved {}".format(k))
            print("has events:")
            for e in info["events"]:
                print(e)
            print("has thoughts:")
            for e in info["thoughts"]:
                print(e)
        """

        # clean action
        self.actions = [a for a in self.actions if not a.finished()]
        print("plan with schedule:\n" + str(self.schedule))
        # create action
        plan, duration = self.schedule.schedule_at()
        address = self.spatial.find_address(plan, as_list=False)
        print("current plan {}:{}".format(plan, duration))
        if self.actions:
            address = self.actions[-1].address
        elif not address:
            tile = self.get_curr_tile()
            address = tile.get_address("world", as_list=True)
            prompt = self.scratch.prompt_plan_sector(plan, self.spatial, tile, address)
            address.append(self._llm.completion(**prompt))
            print("address " + str(address))
            arenas = self.spatial.get_leaves(address)
            print("arenas " + str(arenas))

            prompt = self.scratch.prompt_plan_arena(plan, self.spatial, tile, address)
            address.append(self._llm.completion(**prompt))
            print("address " + str(address))

            objs = self.spatial.get_leaves(address)
            print("objs " + str(objs))

            raise Exception("stop here!!")
            """
            act_arena = generate_action_arena(
                act_desp, persona, maze, act_world, act_sector
            )
            address = self.spatial.find_address("act_arena")
            act_game_object = generate_action_game_object(
                act_desp, act_address, persona, maze
            )
            """

        raise Exception("stop here!!")
        return plan

    def think(self, status, agents):
        self.move(status["position"])
        retrieved = self.percept()
        plan = self.plan(agents, retrieved)

        """
        plan = self.plan(maze, personas, new_day, retrieved)
        self.reflect()
        """
        return plan

    def _increase_poignancy(self, score):
        self.status["poignancy"]["current"] += score
        self.status["poignancy"]["num_event"] += 1

    def _evaluate_concept(self, event, e_type="event", desc=None):
        desc = desc or event.sub_desc
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

    def _evaluate_event(self, event):
        if event.fit(None, "is", "idle") or not self._llm:
            return 1
        prompt = self.scratch.prompt_poignancy(event)
        print("prompt " + str(prompt))
        response = self._llm.completion(prompt)
        print("response " + str(response))
        raise Exception("stop here!!")

        return 1

    def _evaluate_chat(self, event):
        if not self._llm:
            return 1
        return 1

    def get_curr_tile(self):
        return self.maze.tile_at(self.coord)

    def get_curr_event(self, as_sub=True):
        action = self.actions[-1]
        if as_sub:
            return action.event
        event = action.event
        return memory.Event(
            action.address, event.predicate, event.object, event.describe
        )
