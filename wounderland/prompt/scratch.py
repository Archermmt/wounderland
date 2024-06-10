"""wounderland.prompt.scratch"""

import re
import random
from jinja2 import Template
from wounderland import utils


class Scratch:
    def __init__(self, name, config, logger):
        self.name = name
        self.config = config
        self.logger = logger

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
            prompt += f" {instruction}"
        if example:
            prompt += f"\nExample output {style}:\n{example}"
        return prompt

    def _debug_msg(self, title, prompt, response):
        title = "{}.{} @ {}".format(
            self.name, title, utils.get_timer().get_date("%H:%M:%S")
        )
        return "{}<PROMPT>:\n{}\n\n<RESPONSE>:\n{}\n".format(
            utils.split_line(title), prompt, response
        )

    def prompt_poignancy_event(self, event):
        prompt = self._base_desc()
        prompt += """\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for {}.
-----
Event: brushing teeth. Rate (return a number between 1 to 10): 1
-----
Event: making bed. Rate (return a number between 1 to 10): 1
-----
Event: breaking up. Rate (return a number between 1 to 10): 10
-----
Event: college acceptance. Rate (return a number between 1 to 10): 10
-----
Event: {}. Rate (return a number between 1 to 10): """.format(
            self.name, event.describe
        )

        def _callback(response):
            self.logger.debug(self._debug_msg("poignancy_event", prompt, response))
            pattern = "Rate \(return a number between 1 to 10\): (\d{1,2})"
            for line in response.split("\n"):
                if event.describe not in line:
                    continue
                infos = re.findall(pattern, line)
                if len(infos) == 1:
                    return int(infos[0])
            raise Exception("Can not find single integer in " + str(response))

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": random.choice(list(range(10))) + 1,
        }

    def prompt_wake_up(self):
        prompt = self._base_desc()
        prompt += """\nIn general, {}\n{}'s wake up hour:""".format(
            self.config["lifestyle"], self.name
        )
        prompt = self._format_output(
            prompt, "hour", "8:00 am", "The output should ONLY contain ONE hour value."
        )

        def _callback(response):
            self.logger.debug(self._debug_msg("wake_up", prompt, response))
            response = response.replace("\n", "").strip()
            hours = re.findall(r"(\d):00 am+", response)
            if len(hours) == 1:
                return int(hours[0])
            hours = re.findall(r"(\d) am+", response)
            if len(hours) == 1:
                return int(hours[0])
            raise Exception("Can not find single integer in " + str(response))

        return {"prompt": prompt, "callback": _callback, "failsafe": 6}

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
            self.logger.debug(self._debug_msg("schedule_init", prompt, response))
            plan = []
            for sch in response.split("\n"):
                if ")" in sch:
                    plan.append(sch.split(") ")[1].strip().strip("."))
                else:
                    plan.append(sch.strip().strip("."))
            return plan

        failsafe = [
            "wake up and complete the morning routine at 6:00 am",
            "eat breakfast at 7:00 am",
            "read a book from 8:00 am to 12:00 pm",
            "have lunch at 12:00 pm",
            "take a nap from 1:00 pm to 4:00 pm",
            "relax and watch TV from 7:00 pm to 8:00 pm",
            "go to bed at 11:00 pm",
        ]
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

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
            self.logger.debug(self._debug_msg("schedule_daily", prompt, response))
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

        failsafe = {
            "6:00 AM": "wake up and complete the morning routine",
            "7:00 AM": "eat breakfast",
            "8:00 AM": "read a book",
            "9:00 AM": "read a book",
            "10:00 AM": "read a book",
            "11:00 AM": "read a book",
            "0:00 PM": "have lunch",
            "1:00 PM": "take a nap",
            "2:00 PM": "take a nap",
            "3:00 PM": "take a nap",
            "4:00 PM": "continue work",
            "5:00 PM": "continue work",
            "6:00 PM": "go back to home",
            "7:00 PM": "relax and watch TV",
            "8:00 PM": "relax and watch TV",
            "9:00 PM": "read book before go to bed",
            "10:00 PM": "prepare to sleep",
            "11:00 PM": "sleeping",
        }
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

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
            self.logger.debug(self._debug_msg("schedule_decompose", prompt, response))
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

        failsafe = [
            (plan["describe"], increment)
            for _ in range(int(plan["duration"] / increment))
        ]
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

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
            self.logger.debug(self._debug_msg("determine_sector", prompt, response))
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
            self.logger.debug(self._debug_msg("determine_arena", prompt, response))
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
            self.logger.debug(self._debug_msg("determine_object", prompt, response))
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
            self.logger.debug(self._debug_msg("describe_emoji", prompt, response))
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
            self.logger.debug(self._debug_msg("describe_event", prompt, response))
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
            self.logger.debug(self._debug_msg("describe_object", prompt, response))
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

        def _callback(response):
            self.logger.debug(self._debug_msg("decide_talk", prompt, response))
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

        def _callback(response):
            self.logger.debug(self._debug_msg("decide_react", prompt, response))
            return response

        return {"prompt": prompt, "callback": _callback}
