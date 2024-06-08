"""wounderland.agent"""

import re
import math
import random
import datetime
from jinja2 import Template
from wounderland import memory, utils
from wounderland.model.llm_model import create_llm_model


class Scratch:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.chat = None

    def _base_desc(self):
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
            utils.get_timer().daily_format(),
        )

    def _format_output(self, prompt, style, example="", instruction=""):
        prompt = '"""\n' + prompt + '\n"""\n'
        prompt += f"Output the response to the prompt above in {style}."
        if instruction:
            prompt += f"{instruction}"
        if example:
            prompt += f"\nExample output {style}:\n{example}"
        return prompt

    def prompt_poignancy_event(self, event):
        prompt = self._base_desc()
        prompt += """\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for {}.

Event: {}
Rate (return a number between 1 to 10):""".format(
            self.name, event.describe
        )
        prompt = self._format_output(
            prompt, "number", "5", "The output should ONLY contain ONE number."
        )

        print("\n[TMINFO] prompt_poignancy_event prompt " + str(prompt))

        def _callback(response):
            print("[TMINFO] prompt_poignancy_event response " + str(response))
            if response.isdigit():
                return int(response)
            hours = re.findall(r"\d+", response)
            if len(hours) == 1:
                return int(hours[0])
            raise Exception("Can not find single integer in " + str(response))

        return {"prompt": prompt, "callback": _callback}

    def prompt_wake_up(self):
        prompt = self._base_desc()
        prompt += """\nIn general, {}\n{}'s wake up hour:""".format(
            self.config["lifestyle"], self.name
        )
        prompt = self._format_output(
            prompt, "hour", "8:00 am", "The output should ONLY contain ONE hour value."
        )

        def _callback(response):
            response = response.replace("\n", "").strip()
            hours = re.findall(r"(\d):00 am+", response)
            if len(hours) == 1:
                return int(hours[0])
            hours = re.findall(r"(\d) am+", response)
            if len(hours) == 1:
                return int(hours[0])
            raise Exception("Can not find single integer in " + str(response))

        return {"prompt": prompt, "callback": _callback}

    def prompt_schedule_init(self, wake_up):
        prompt = self._base_desc()
        prompt += """\n\nIn general, {}""".format(self.config["lifestyle"])
        prompt += "\nToday is {}. Here is {}'s plan today in broad-strokes ".format(
            utils.get_timer().daily_format(), self.name
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

    def prompt_schedule_daily(self, wake_up, schedule, daily_schedule):
        prompt = "Hourly schedule format:\n"
        for hour, _ in schedule:
            prompt += f"[{hour}] Activity: [Fill in]\n"
        prompt += "========\n"
        prompt += self._base_desc()
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

    def prompt_schedule_decompose(self, plan, schedule):
        def _plan_des(plan):
            start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
            return f'{start} ~ {end}, {self.name} is planning on {plan["describe"]}'

        prompt = """Describe subtasks in 5 min increments. 
---
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: {kitchen, bedroom, dining, porch, office, bathroom, living room, hallway}.
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.s

Today is Saturday May 10. From 08:00AM ~ 09:00AM, Kelly is planning on having breakfast, from 09:00AM ~ 12:00PM, Kelly is planning on working on the next day's kindergarten lesson plan, and from 12:00AM ~ 13PM, Kelly is planning on taking a break. 
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 12:00pm (total duration in minutes: 180):
1) Kelly is reviewing the kindergarten curriculum standards. (duration: 15, left: 165)
2) Kelly is brainstorming ideas for the lesson. (duration: 30, left: 135)
3) Kelly is creating the lesson plan. (duration: 30, left: 105)
4) Kelly is creating materials for the lesson. (duration: 30, left: 75)
5) Kelly is taking a break. (duration: 15, left: 60)
6) Kelly is reviewing the lesson plan. (duration: 30, left: 30)
7) Kelly is making final changes to the lesson plan. (duration: 15, left: 15)
8) Kelly is printing the lesson plan. (duration: 10, left: 5)
9) Kelly is putting the lesson plan in her bag. (duration: 5, left: 0)
---\n"""
        prompt += self._base_desc()
        indices = range(
            max(plan["idx"] - 1, 0), min(plan["idx"] + 2, len(schedule.daily_schedule))
        )
        prompt += f"\nToday is {utils.get_timer().daily_format()}. From "
        prompt += ", ".join([_plan_des(schedule.daily_schedule[i]) for i in indices])
        start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
        increment = max(int(plan["duration"] / 150) * 5, 5)
        prompt += f'\nIn {increment} min increments, list the subtasks {self.name} does when {self.name} is {plan["describe"]}'
        prompt += (
            f' from {start} ~ {end} (total duration in minutes {plan["duration"]}):\n'
        )
        prompt += f"1) {self.name} is"

        def _callback(response):
            decompose, left = [], plan["duration"]
            pattern = self.name + " is (.+?) \(duration: (\d{1,2})"
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    describe, duration = infos[0][0], int(infos[0][1])
                    decompose.append((describe.strip(".").strip(), duration))
                    left -= duration
                if left <= 0:
                    break
            if left > 0:
                decompose.append((plan["describe"], left))
            return decompose

        return {"prompt": prompt, "callback": _callback}

    def prompt_determine_sector(self, describes, spatial, address, tile):
        template = Template(
            """\n-----
{{ name }} lives in <{{ live_sector }}> that has {{ live_arenas|join(', ') }}.
{{ name }} is currently in <{{ curr_sector }}> that has {{ curr_arenas|join(', ') }}.
{{ daily_plan }}
Area options: <{{ areas|join(', ') }}>.
* Stay in the current area if the activity can be done there. Only go out if the activity needs to take place in another place.
* Must be one of the "Area options", verbatim.
{{ name }} is {{ describes[0] }}. For {{ describes[1] }}, {{ name }} should go to the following area: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose an appropriate area from the area options for a task at hand."
        prompt += template.render(
            name="Sam Kim",
            live_sector="Sam Kim's house",
            live_arenas=["Sam Kim's room", "bathroom", "kitchen"],
            curr_sector="Sam Kim's house",
            curr_arenas=["Sam Kim's room", "bathroom", "kitchen"],
            daily_plan="Sam Kim enjoy walking around from 8am to 12am.",
            areas=[
                "Sam Kim's house",
                "The Rose and Crown Pub",
                "Hobbs Cafe",
                "Oak Hill College",
                "Johnson Park",
                "Harvey Oak Supply Store",
                "The Willows Market and Pharmacy",
            ],
            describes=["relax in park", "taking a walk"],
            answer="Johnson Park",
        )
        prompt += template.render(
            name="Jane Anderson",
            live_sector="Oak Hill College Student Dormatory",
            live_arenas=["Jane Anderson's room"],
            curr_sector="Oak Hill College",
            curr_arenas=["classroom", "library"],
            daily_plan="Jane Anderson usually stays in dormitory and read books.",
            areas=[
                "Oak Hill College Student Dormatory",
                "The Rose and Crown Pub",
                "Hobbs Cafe",
                "Oak Hill College",
                "Johnson Park",
                "Harvey Oak Supply Store",
                "The Willows Market and Pharmacy",
            ],
            describes=["eating dinner", "eating dinner"],
            answer="Hobbs Cafe",
        )
        live_address = spatial.find_address("living_area", as_list=True)[:-1]
        curr_address = tile.get_address("sector", as_list=True)
        prompt += template.render(
            name=self.name,
            live_sector=live_address[-1],
            live_arenas=spatial.get_leaves(live_address),
            curr_sector=curr_address[-1],
            curr_arenas=spatial.get_leaves(curr_address),
            daily_plan=self.config["daily_plan"],
            areas=spatial.get_leaves(address),
            describes=describes,
        )

        sectors, default = spatial.get_leaves(address), live_address[-1]

        def _callback(response):
            pattern = self.name + " should go to the following area: <(.+?)>"
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return infos[0] if infos[0] in sectors else default
            raise Exception("Can not find sector for plan " + str(describes))

        return {"prompt": prompt, "callback": _callback, "failsafe": default}

    def prompt_determine_arena(self, describes, spatial, address):
        template = Template(
            """\n-----
{{ name }} is going to {{ dst_sector }} that has the following areas: <{{ dst_arenas|join(', ') }}>.
{{ daily_plan }}
* Stay in the current area if the activity can be done there. Never go into other people's rooms unless necessary.
* Must be one of the given areas, verbatim.
{{ name }} is {{ describes[0] }}. For {{ describes[1] }}, {{ name }} should go to the following area in {{ dst_sector }}: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose an appropriate area from the areas for a task at hand."
        prompt += template.render(
            name="Jane Anderson",
            dst_sector="Jane Anderson's house",
            dst_arenas=["kitchen", "bedroom", "bathroom"],
            daily_plan="Jane Anderson usually stays in dormitory and read books.",
            describes=["making meal", "cooking"],
            answer="kitchen",
        )
        prompt += template.render(
            name="Tom Watson",
            dst_sector="Hobbs Cafe",
            dst_arenas=["cafe"],
            daily_plan="Tom Watson visit cafe around 8am and go to campus for classes.",
            describes=["eating breakfast", "getting coffee"],
            answer="cafe",
        )
        prompt += template.render(
            name=self.name,
            dst_sector=address[-1],
            dst_arenas=spatial.get_leaves(address),
            daily_plan=self.config["daily_plan"],
            describes=describes,
        )

        arenas = spatial.get_leaves(address)
        default = spatial.find_address("living_area", as_list=True)[-1]

        def _callback(response):
            pattern = (
                self.name
                + " should go to the following area in "
                + address[-1]
                + ": <(.+?)>"
            )
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return infos[0] if infos[0] in arenas else default
            raise Exception("Can not find arena for plan " + str(describes))

        return {"prompt": prompt, "callback": _callback, "failsafe": default}

    def prompt_determine_object(self, describes, spatial, address):
        template = Template(
            """\n-----
Current activity: {{ activity }}
Objects available: <{{ objects|join(', ') }}>
Pick ONE most relevant object from the Objects available: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose most relevant object from the Objects available for a task at hand."
        prompt += template.render(
            activity="sleep in bed",
            objects=["bed", "easel", "closet", "painting"],
            answer="bed",
        )
        prompt += template.render(
            activity="painting",
            objects=["easel", "closet", "sink", "microwave"],
            answer="easel",
        )
        prompt += template.render(
            activity="painting",
            objects=["easel", "closet", "sink", "microwave"],
            answer="easel",
        )
        prompt += template.render(
            activity="cooking",
            objects=["stove", "sink", "fridge", "counter"],
            answer="stove",
        )
        prompt += template.render(
            activity="watch TV",
            objects=["couch", "TV", "remote", "coffee table"],
            answer="TV",
        )
        prompt += template.render(
            activity="study",
            objects=["desk", "computer", "chair", "bookshelf"],
            answer="desk",
        )
        prompt += template.render(
            activity="talk on the phone",
            objects=["phone", "charger", "bed", "nightstand"],
            answer="phone",
        )
        prompt += template.render(
            activity=describes[1], objects=spatial.get_leaves(address)
        )

        objects = spatial.get_leaves(address)
        default = random.choice(objects)

        def _callback(response):
            pattern = (
                "Pick ONE most relevant object from the Objects available: <(.+?)>"
            )
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return infos[0] if infos[0] in objects else default
            raise Exception("Can not find object for plan " + str(describes[1]))

        return {"prompt": prompt, "callback": _callback, "failsafe": default}

    def prompt_describe_emoji(self, describe):
        prompt = f"""Convert an action description to an emoji (important: use three or less emojis).\n
Action description: waking up and starting her morning routine (taking a shower)
Emoji: <🛁🧖‍♀️>
Action description: having breakfast (making coffee)
Emoji: <☕️🥐>
Action description: painting (turning on classical music to listen to as she paints)
Emoji: <🎨🎵>
Action description: exercising (going for a run)
Emoji: <🏃‍♀️>
Action description: having breakfast (putting butter on her toast)
Emoji: <🧈🍞>
Action description: {describe}
Emoji: <"""

        def _callback(response):
            pattern = "Emoji: <(.+?)>"
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return infos[0][:3]
            raise Exception("Can not make emoji for " + str(describe))

        return {"prompt": prompt, "callback": _callback}

    def prompt_describe_event(self, subject, describe):
        prompt = f"""Task: Turn the input into (~subject~, =predicate=, -object-).\n
Input: Sam Johnson is eating breakfast. 
Output: (~Dolores Murphy~, =eat=, -breakfast-) 
--- 
Input: Joon Park is brewing coffee.
Output: (~Joon Park~, =brew=, -coffee-)
---
Input: Jane Cook is sleeping. 
Output: (~Jane Cook~, =is=, -sleep-)
---
Input: Michael Bernstein is writing email on a computer. 
Output: (~Michael Bernstein~, =write=, -email-)
---
Input: Percy Liang is teaching students in a classroom. 
Output: (~Percy Liang~, =teach=, -students-)
---
Input: Merrie Morris is running on a treadmill. 
Output: (~Merrie Morris~, =run=, -treadmill-)
---
Input: {subject} is {describe}. 
Output: (~{subject}~,"""

        def _callback(response):
            patterns = ["\(~(.+?)~, =(.+?)=, -(.+?)-\)", "\(~(.+?)~, =(.+?)="]
            for line in response.split("\n"):
                for p in patterns:
                    infos = re.findall(p, line)
                    if len(infos) == 1 and infos[0][0] == subject:
                        return infos[0]
            raise Exception("Can not make event for " + str(describe))

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": (subject, "is", describe),
        }

    def promt_describe_object(self, obj, describe):
        prompt = f"""Task: We want to understand the state of an object that is being used by someone.\n
Let's think step by step. 
We want to know about oven's state. 
Step 1. Sam Johnson is eating breakfast at/using the oven. 
Step 2. Describe the cooking utensils's state: oven is <being heated to cook breakfast>
---
Let's think step by step. 
We want to know about computer's state. 
Step 1. Michael Bernstein is writing email at/using the computer. 
Step 2. Describe the computer's state: computer is <being used to write email>
---
Let's think step by step. 
We want to know about sink's state. 
Step 1. Tom Kane is washing his face at/using the sink.
Step 2. Describe the sink's state: sink is <running with water>
---
Let's think step by step. 
We want to know about {obj}'s state. 
Step 1. {self.name} is {describe} at/using the {obj}.
Step 2. Describe the {obj}'s state: {obj} is <"""

        def _callback(response):
            pattern = "Describe the " + obj + "'s state: " + obj + " is <(.+?)>"
            for line in response.split("\n"):
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return infos[0]
            raise Exception("Can not describe object {}: {}".format(obj, describe))

        return {"prompt": prompt, "callback": _callback}

    def prompt_decide_talk(self, agent, other, focus):
        def _status_des(agent):
            act_desc = agent.get_curr_event().describe
            if not agent.path and "waiting" not in act_desc:
                return f"{agent.name} is already {act_desc}"
            if "waiting" in act_desc:
                return f"{agent.name} is {act_desc}"
            return f"{agent.name} is on the way to {act_desc}"

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])
        date_str = utils.get_timer().get_date("%B %d, %Y, %H:%M:%S %p")
        chat_history = ""
        last_chats = agent.associate.retrieve_chats(other.name)
        if last_chats:
            chat_history = f" {self.name} and {other.name} last chatted at {last_chats[0].created} about {last_chats[0].describe}"
        a_des, o_des = _status_des(agent), _status_des(other)
        prompt = f"""Task -- given context, determine whether the subject will initiate a conversation with another. 
Format: 
Context: []
Question: []
Reasoning: []
Answer in "yes" or "no": []
---
Context: {context}
Right now, it is {date_str}.{chat_history}
{a_des}\n{o_des}\n
Question: Would {self.name} initiate a conversation with {other.name}? \n
Reasoning: Let's think step by step.
"""
        print("\n[TMINFO] prompt_decide_talk prompt " + str(prompt))

        def _callback(response):
            print("\n[TMINFO] prompt_decide_talk response " + str(response))
            return response

        return {"prompt": prompt, "callback": _callback}

    def prompt_decide_react(self, agent, other, focus):
        template = Template(
            """\n-----
Context: {{ context }}. 
Right now, it is {{ date }}. 
{{ status }}.
{{ name }} sees {{ o_status }}.
My question: Let's think step by step. Of the following three options, what should {{ name }} do?
Option 1: Wait on {{ action }} until {{ o_name }} is done {{ o_action }}
Option 2: Continue on to {{ action }} now
Reasoning: {{ reason }}
{% if answer %}Answer: <{{ answer }}>{% else %}{% endif %}
"""
        )

        prompt = "Task -- given context and three options that a subject can take, determine which option is the most acceptable."
        reason = """Both Jane and Liz want to use the bathroom. 
It would be strange for both Jane and Liz to use the bathroom at the same time. 
So, since Liz is already using the bathroom, the best option for Jane is to wait on using the bathroom."""
        prompt += template.render(
            context="Jane is Liz's house mate. Jane and Liz exchanged a conversation about saying good morning at 07:05am, October 25, 2022",
            date="07:09 am, October 25, 2022",
            name="Jane",
            o_name="Liz",
            status="Jane was on her way to using the bathroom right now",
            o_status="Liz already using the bathroom",
            action="using the bathroom",
            o_action="using the bathroom",
            reason=reason,
            answer="Option 1",
        )
        reason = """Sam is likely going to be in his room studying. Sarah, on the other hand, is likely headed to the laundry room for doing the laundry.
Since Sam and Sarah need to use different areas, their actions do not conflict. 
So, since Sam and Sarah are going to be in different areas, Sam mcan continue on to eating his lunch now."""
        prompt += template.render(
            context="Sam is Sarah's friend. Sam and Sarah exchanged a conversation about favorite movies at 11pm, October 24, 2022",
            date="12:40 pm, October 25, 2022",
            name="Sam",
            o_name="Sarah",
            status="Sam is on the way to study for his test",
            o_status="Sarah heading to do her laundry",
            action="eating his lunch",
            o_action="doing her laundry",
            reason=reason,
            answer="Option 2",
        )

        def _status_des(agent):
            event, loc = agent.get_curr_event(), ""
            if event.address:
                loc = " at {} in {}".format(event.address[-1], event.address[-2])
            if not agent.path:
                return f"{agent.name} is already {event.describe}{loc}"
            return f"{agent.name} is on the way to {event.describe}{loc}"

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])

        prompt += template.render(
            context=context,
            date=utils.get_timer().get_date("%B %d, %Y, %H:%M:%S %p"),
            name=self.name,
            o_name=other.name,
            status=_status_des(agent),
            o_status=_status_des(other),
            action=agent.get_curr_event().describe,
            o_action=other.get_curr_event().describe,
        )

        print("\n[TMINFO] prompt_decide_react prompt " + str(prompt))

        def _callback(response):
            print("\n[TMINFO] prompt_decide_react response " + str(response))
            return response

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
        self.schedule = memory.Schedule(config["schedule"])
        self.associate = memory.Associate(config["associate"])
        self.concepts = {}

        # prompt
        self.scratch = Scratch(self.name, config["scratch"])

        # status
        self.status = {"poignancy": {"current": 0, "num_event": 0}, "chat_with": {}}
        self.status = utils.update_dict(self.status, config.get("status", {}))

        # action and events
        tile = self.maze.tile_at(config["coord"])
        address = tile.get_address("game_object", as_list=True)
        self.actions = [
            memory.Action(memory.Event(self.name), memory.Event(address[-1]))
        ]

        # update maze
        self.coord, self.path = None, None
        self.move(config["coord"])

    def __str__(self):
        des = {
            "name": self.name,
            "tile": self.maze.tile_at(self.coord).to_dict(),
            "schedule": str(self.schedule).replace("\n", "\n  "),
            "actions": [str(a).replace("\n", "\n  ") for a in self.actions],
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
        if self.coord and self.coord != coord:
            self.maze.remove_events(self.coord, subject=self.name)
            self.maze.update_events(self.coord, "idle")
        self.coord = coord
        self.path = path or []
        self.maze.add_event(self.coord, self.get_curr_event())
        self.maze.persona_tiles[self.name] = self.coord
        if not self.path:
            self.maze.add_event(self.coord, self.get_curr_event(False))

    def think(self, status, agents):
        self.move(status["coord"], status["path"])
        self.percept()
        if self.think_config["mode"] == "random" or not self._llm:
            path = [self.coord]
            for _ in range(5):
                coord = path[-1]
                next_coords = [
                    (coord[0] - 1, coord[1]),
                    (coord[0] + 1, coord[1]),
                    (coord[0], coord[1] - 1),
                    (coord[0], coord[1] + 1),
                ]
                path.append(random.choice(next_coords))
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
        concepts = []
        for p_event in percept_events[: self.percept_config["att_bandwidth"]]:
            recent_events = set([n.event for n in self.associate.retrieve_events()])
            if p_event not in recent_events:
                chats = []
                if p_event.fit(self.name, "chat with"):
                    node = self._add_concept(
                        self.get_curr_event(), "chat", filling=self.scratch.chat
                    )
                    chats = [node.name]
                node = self._add_concept(p_event, "event", filling=chats)
                self._increase_poignancy(node.poignancy)
                concepts.append(node)

        # retrieve events
        def _get_info(concept):
            return {
                "concept": concept,
                "events": self.associate.retrieve_events(concept),
                "thoughts": self.associate.retrieve_thoughts(concept),
            }

        self.concepts = {
            c.event.describe: _get_info(c)
            for c in concepts
            if c.event.subject != self.name
        }

    def plan(self, agents):
        self.make_schedule()
        # get last action
        self.actions = [a for a in self.actions if not a.finished()]
        if not self.actions:
            self.actions.append(self._determine_action())
        # print("get action " + str(self.actions[-1]))
        # print("schedule " + str(self.schedule))
        """
        for k, info in self.concepts.items():
            print("\nconcept {}".format(k))
            print("has events:")
            for e in info["events"]:
                print(e)
            print("has thoughts:")
            for e in info["thoughts"]:
                print(e)
        """
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
            priority = [i for i in self.concepts.values() if _focus(i["concept"])]
            if priority:
                focus = random.choice(priority)
        if not focus:
            priority = [i for i in self.concepts.values() if not _ignore(i["concept"])]
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
        if other.name in self.status["chat_with"]:
            if utils.get_timer().get_delta(self.status["chat_with"][other.name]) < 60:
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
        print("prompt " + str(prompt))
        response = self._llm.completion(prompt)
        print("response " + str(response))
        raise Exception("stop here!!")

        return 1

    def _evaluate_chat(self, event):
        if not self._llm:
            return 1
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
            "schedule": self.schedule.to_dict(),
            "associate": self.associate.to_dict(),
        }
