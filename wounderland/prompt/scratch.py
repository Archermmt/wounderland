"""wounderland.prompt.scratch"""

import random
import datetime
from jinja2 import Template
from wounderland import utils
from wounderland.memory import Event
from wounderland.model import parse_llm_output


class Scratch:
    def __init__(self, name, currently, config):
        self.name = name
        self.currently = currently
        self.config = config

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
            self.currently,
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

    def prompt_poignancy_event(self, event):
        prompt = self._base_desc()
        prompt += f"""\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., brushing teeth, making bed) and 10 is extremely poignant (e.g., a break up, college acceptance), rate the likely poignancy of the following event for {self.name}.
Each event should ONLY be rate with ONE integer on the scale of 1 to 10.
-----
Event: brushing teeth. Rate: 1
-----
Event: making bed. Rate: 1
-----
Event: a break up. Rate: 10
-----
Event: college acceptance. Rate: 10
-----
Event: {event.get_describe()}. Rate: """

        def _callback(response):
            pattern = "Event: .*\. Rate: (\d{1,2})"
            return int(parse_llm_output(response, pattern, "match_last"))

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": random.choice(list(range(10))) + 1,
        }

    def prompt_poignancy_chat(self, event):
        prompt = self._base_desc()
        prompt += f"""\nOn the scale of 1 to 10, where 1 is purely mundane (e.g., routine morning greetings) and 10 is extremely poignant (e.g., a conversation about breaking up, a fight), rate the likely poignancy of the following conversation for {self.name}.
Each Conversation should ONLY be rate with ONE integer on the scale of 1 to 10.
-----
Conversation: routine morning greetings. Rate: 1
-----
Conversation: a conversation about breaking up, a fight. Rate: 10
-----
Conversation: {event.get_describe()}. Rate: """

        def _callback(response):
            pattern = "Conversation: .*\. Rate: (\d{1,2})"
            return int(parse_llm_output(response, pattern, "match_last"))

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
            return int(parse_llm_output(response, ["(\d):00 am+", "(\d) am+"]))

        return {"prompt": prompt, "callback": _callback, "failsafe": 6}

    def prompt_schedule_init(self, wake_up):
        prompt = self._base_desc()
        prompt += """\nIn general, {}""".format(self.config["lifestyle"])
        prompt += "\nToday is {}. Here is {}'s plan today in broad-strokes ".format(
            utils.get_timer().daily_format(), self.name
        )
        prompt += "(with the time of the day. e.g., eat breakfast at 7:00 AM, have a lunch at 12:00 PM, watch TV at 7:00 PM):\n"
        prompt += (
            "1) wake up and complete the morning routine at {}:00 AM.\n2) ".format(
                wake_up
            )
        )
        prompt = self._format_output(
            prompt, "lines", instruction="Each line consist of index and plan"
        )

        def _callback(response):
            patterns = ["\d{1,2}\) (.*)\.", "\d{1,2}\) (.*)", "(.*)\.", "(.*)"]
            return parse_llm_output(response, patterns, mode="match_all")

        failsafe = [
            "wake up and complete the morning routine at 6:00 AM",
            "eat breakfast at 7:00 AM",
            "read a book at 8:00 AM",
            "have lunch at 12:00 PM",
            "take a nap at 1:00 PM",
            "relax and watch TV at 7:00 PM",
            "go to bed at 11:00 PM",
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
        prompt += "; ".join(daily_schedule)
        prompt += "\n\n" + "\n".join(
            [
                "[{}] Activity: {} is {}".format(h, self.name, s)
                for h, s in schedule[: wake_up + 1]
            ]
        )

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

        def _callback(response):
            patterns = [
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " is (.*)\.",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " is (.*)",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " is (.*)\.",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " is (.*)",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " (.*)\.",
                "\[(\d{1,2}:\d{2} AM)\] Activity: " + self.name + " (.*)",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " (.*)\.",
                "\[(\d{1,2}:\d{2} PM)\] Activity: " + self.name + " (.*)",
            ]
            outputs = parse_llm_output(response, patterns, mode="match_all")
            assert len(outputs) >= 5, "less than 5 schedules"
            return {s[0]: s[1] for s in outputs}

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_schedule_decompose(self, plan, schedule):
        def _plan_des(plan):
            start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
            return f'{start} ~ {end}, {self.name} is planning on {plan["describe"]}'

        prompt = """Describe subtasks in 5 min increments.
[Example]
Name: Kelly Bronson
Age: 35
Backstory: Kelly always wanted to be a teacher, and now she teaches kindergarten. During the week, she dedicates herself to her students, but on the weekends, she likes to try out new restaurants and hang out with friends. She is very warm and friendly, and loves caring for others.
Personality: sweet, gentle, meticulous
Location: Kelly is in an older condo that has the following areas: {kitchen, bedroom, dining, porch, office, bathroom, living room, hallway}.
Currently: Kelly is a teacher during the school year. She teaches at the school but works on lesson plans at home. She is currently living alone in a single bedroom condo.
Daily plan requirement: Kelly is planning to teach during the morning and work from home in the afternoon.s
Today is Saturday May 10. From 08:00AM ~ 09:00AM, Kelly is planning on having breakfast, from 09:00AM ~ 10:00PM, Kelly is planning on working on the next day's kindergarten lesson plan, and from 10:00AM ~ 13PM, Kelly is planning on taking a break. 
In 5 min increments, list the subtasks Kelly does when Kelly is working on the next day's kindergarten lesson plan from 09:00am ~ 10:00pm (total duration in minutes: 60):

<subtasks>:
1) Kelly <is> reviewing the kindergarten curriculum standards. (duration: 15, left: 45)
2) Kelly <is> brainstorming ideas for the lesson. (duration: 10, left: 35)
3) Kelly <is> creating the lesson plan. (duration: 10, left: 25)
8) Kelly <is> printing the lesson plan. (duration: 10, left: 15)
9) Kelly <is> putting the lesson plan in her bag. (duration: 15, left: 0)

Given example above, please list the subtasks of the following task.
[TASK]\n"""
        prompt += self._base_desc()
        indices = range(
            max(plan["idx"] - 1, 0), min(plan["idx"] + 2, len(schedule.daily_schedule))
        )
        prompt += f"\nToday is {utils.get_timer().daily_format()}. From "
        prompt += ", ".join([_plan_des(schedule.daily_schedule[i]) for i in indices])
        start, end = schedule.plan_stamps(plan, time_format="%H:%M%p")
        increment = max(int(plan["duration"] / 100) * 5, 5)
        prompt += f'\nIn {increment} min increments, list the subtasks {self.name} does when {self.name} is {plan["describe"]}'
        prompt += (
            f' from {start} ~ {end} (total duration in minutes {plan["duration"]}):\n\n'
        )
        prompt += "<subtasks>:\n"
        prompt += f"1) {self.name} <is> "

        def _callback(response):
            patterns = [
                "\d{1,2}\) .* <is> (.*) \(duration: (\d{1,2}), left: \d*\)",
                ".* <is> (.*) \(duration: (\d{1,2}), left: \d*\)",
            ]
            schedules = parse_llm_output(response, patterns, mode="match_all")
            schedules = [(s[0].strip("."), int(s[1])) for s in schedules]
            left = plan["duration"] - sum([s[1] for s in schedules])
            if left > 0:
                schedules.append((plan["describe"], left))
            return schedules

        failsafe = [(plan["describe"], 10) for _ in range(int(plan["duration"] / 10))]
        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_schedule_revise(self, action, schedule):
        plan, _ = schedule.current_plan()
        start, end = schedule.plan_stamps(plan, time_format="%H:%M")
        act_start_minutes = utils.daily_duration(action.start)
        org_plan, new_plan = [], []

        def _plan_des(start, end, describe):
            if not isinstance(start, str):
                start = start.strftime("%H:%M")
            if not isinstance(end, str):
                end = end.strftime("%H:%M")
            return "[{} ~ {}] {} ({})".format(start, end, plan["describe"], describe)

        for de_plan in plan["decompose"]:
            de_start, de_end = schedule.plan_stamps(de_plan, time_format="%H:%M")
            org_plan.append(_plan_des(de_start, de_end, de_plan["describe"]))
            if de_plan["start"] + de_plan["duration"] <= act_start_minutes:
                new_plan.append(_plan_des(de_start, de_end, de_plan["describe"]))
            elif de_plan["start"] <= act_start_minutes:
                new_plan.extend(
                    [
                        _plan_des(de_start, action.start, de_plan["describe"]),
                        _plan_des(
                            action.start, action.end, action.event.get_describe(False)
                        ),
                    ]
                )
                new_plan.append("[{} ~".format(action.end.strftime("%H:%M")))

        org_plan, new_plan = "\n".join(org_plan), "\n".join(new_plan)
        prompt = f"""Here was {self.name}'s originally planned schedule from {start} to {end}. 
{org_plan}\n
But {self.name} unexpectedly end up with the following event for {action.duration} minutes:\n{action.event.get_describe()}.
\nRevise {self.name}'s schedule from {start} to {end} accordingly (it has to end by {end}). 
The revised schedule:
{new_plan}"""

        def _callback(response):
            patterns = [
                "^\[(\d{1,2}:\d{1,2}) ~ (\d{1,2}:\d{1,2})\] continuing to work at the counter \((.*)\)",
                "^\[(\d{1,2}:\d{1,2}) ~ (\d{1,2}:\d{1,2})\] (.*)",
            ]
            schedules = parse_llm_output(response, patterns, mode="match_all")
            decompose = []
            for start, end, describe in schedules:
                m_start = utils.daily_duration(utils.to_date(start, "%H:%M"))
                m_end = utils.daily_duration(utils.to_date(end, "%H:%M"))
                decompose.append(
                    {
                        "idx": len(decompose),
                        "describe": describe,
                        "start": m_start,
                        "duration": m_end - m_start,
                    }
                )
            return decompose

        return {"prompt": prompt, "callback": _callback, "failsafe": plan["decompose"]}

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

        sectors = spatial.get_leaves(address)
        arenas = {}
        for sec in sectors:
            arenas.update(
                {a: sec for a in spatial.get_leaves(address + [sec]) if a not in arenas}
            )
        failsafe = random.choice(sectors)

        def _callback(response):
            pattern = self.name + " .* area: <(.+?)>"
            sector = parse_llm_output(response, pattern)
            if sector in sectors:
                return sector
            if sector in arenas:
                return arenas[sector]
            for s in sectors:
                if sector.startswith(s):
                    return s
            return failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

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
        failsafe = random.choice(arenas)

        def _callback(response):
            pattern = (
                self.name
                + " should go to the following area in "
                + address[-1]
                + ": <(.+?)>"
            )
            arena = parse_llm_output(response, pattern)
            return arena if arena in arenas else failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_determine_object(self, describes, spatial, address):
        template = Template(
            """\n-----
Current activity: {{ activity }}
Objects: <{{ objects|join(', ') }}>
The most relevant object from the Objects is: {% if answer %}<{{ answer }}>{% else %}<{% endif %}"""
        )

        prompt = "Task -- choose most relevant object from the Objects for a task at hand.\n[Examples]"
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
        failsafe = random.choice(objects)

        def _callback(response):
            pattern = "The most relevant object from the Objects is: <(.+?)>"
            obj = parse_llm_output(response, pattern)
            return obj if obj in objects else failsafe

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_describe_emoji(self, describe):
        prompt = f"""Convert an action description to an emoji (important: use three or less emojis).\n
[Examples]
Action description: waking up and starting her morning routine (taking a shower)
Emoji: 🛁🧖‍♀️
Action description: having breakfast (making coffee)
Emoji: ☕️🥐
Action description: painting (turning on classical music to listen to as she paints)
Emoji: 🎨🎵
Action description: exercising (going for a run)
Emoji: 🏃‍♀️
Action description: having breakfast (putting butter on her toast)
Emoji: 🧈🍞

Given the examples above, please convert the following action to an emoji (important: use three or less emojis):
Action description: {describe}
Emoji: """

        def _callback(response):
            return parse_llm_output(response, "Emoji: (.*)")[:3] or "🦁"

        return {"prompt": prompt, "callback": _callback, "failsafe": "🦁", "retry": 1}

    def prompt_describe_event(self, subject, describe, address, emoji=None):
        prompt = f"""Task: Turn the input into format (<subject>, <predicate>, <object>).\n
[Examples]
Input: Sam Johnson is eating breakfast. 
Output: (<Dolores Murphy>, <eat>, <breakfast>) 
--- 
Input: Joon Park is brewing coffee.
Output: (<Joon Park>, <brew>, <coffee>)
---
Input: Jane Cook is sleeping. 
Output: (<Jane Cook>, <is>, <sleep>)
---
Input: Michael Bernstein is writing email on a computer. 
Output: (<Michael Bernstein>, <write>, <email>)
---
Input: Percy Liang is teaching students in a classroom. 
Output: (<Percy Liang>, <teach>, <students>)
---
Input: Merrie Morris is running on a treadmill. 
Output: (<Merrie Morris>, <run>, <treadmill>)
---

Given the examples above, please turn the input into format (<subject>, <predicate>, <object>):
Input: {describe}.
Output: (<"""

        e_describe = describe
        if e_describe.startswith(subject + " is "):
            e_describe = e_describe.replace(subject + " is ", "")
        failsafe = Event(
            subject, "is", e_describe, describe=describe, address=address, emoji=emoji
        )

        def _callback(response):
            patterns = [
                "\(<(.+?)>, <(.+?)>, <(.*)>\)\,",
                "\(<(.+?)>, <(.+?)>, <(.*)>\)",
                "\((.+?), (.+?), (.*)\)",
            ]
            outputs = parse_llm_output(response, patterns)
            if not outputs[2]:
                return failsafe
            return Event(*outputs, describe=describe, address=address, emoji=emoji)

        return {"prompt": prompt, "callback": _callback, "failsafe": failsafe}

    def prompt_describe_object(self, obj, describe):
        prompt = f"""Task: We want to understand the state of an object that is being used by someone.\n
[Examples]
Let's think step by step to know about oven's state:
Step 1. Sam Johnson is eating breakfast at/using the oven. 
Step 2. Describe the cooking utensils's state: oven is being heated to cook breakfast
---
Let's think step by step to know about computer's state:
Step 1. Michael Bernstein is writing email at/using the computer. 
Step 2. Describe the computer's state: computer is being used to write email
---
Let's think step by step to know about sink's state:
Step 1. Tom Kane is washing his face at/using the sink.
Step 2. Describe the sink's state: sink is running with water
---

Given the examples above, let's think step by step to know about {obj}'s state:
Step 1. {self.name} is {describe} at/using the {obj}.
Step 2. Describe the {obj}'s state: {obj} is """

        def _callback(response):
            patterns = [
                "Describe the " + obj + "'s state: " + obj + " is (.*)\.",
                "Describe the " + obj + "'s state: " + obj + " is (.*)\.",
                "Describe the " + obj + "'s state: .* is (.*)\.",
                "Describe the " + obj + "'s state: .* is (.*)",
            ]
            return parse_llm_output(response, patterns)

        return {"prompt": prompt, "callback": _callback, "failsafe": "idle"}

    def prompt_decide_chat(self, agent, other, focus, chats):
        def _status_des(agent):
            event = agent.get_event()
            if agent.path:
                return f"{agent.name} is on the way to {event.get_describe(False)}"
            return event.get_describe()

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])
        date_str = utils.get_timer().get_date("%B %d, %Y, %H:%M:%S %p")
        chat_history = ""
        if chats:
            chat_history = f" {self.name} and {other.name} last chatted at {chats[0].create} about {chats[0].describe}"
        a_des, o_des = _status_des(agent), _status_des(other)
        prompt = f"""Task -- given context, determine whether the subject will initiate a conversation with another.
Context: {context}
Right now, it is {date_str}.{chat_history}
{a_des}\n{o_des}\n
Question: Would {self.name} initiate a conversation with {other.name}? \n
Reasoning: Let's think step by step.
Answer in "yes" or "no":
"""

        def _callback(response):
            return "yes" in response or "Yes" in response

        return {"prompt": prompt, "callback": _callback, "failsafe": False}

    def prompt_decide_wait(self, agent, other, focus):
        template = Template(
            """\n-----
Context: {{ context }}. 
Right now, it is {{ date }}. 
{{ status }}.
{{ name }} sees {{ o_status }}.
My question: Let's think step by step. Of the following two options, what should {{ name }} do?
Option 1: Wait on {{ action }} until {{ o_name }} is done {{ o_action }}
Option 2: Continue on to {{ action }} now
Reasoning: {{ reason }}
{% if answer %}Answer: <{{ answer }}>{% else %}{% endif %}
"""
        )

        prompt = "Task -- given context and two options that a subject can take, determine which option is the most acceptable.\n[Examples]\n"
        reason = """Both Jane and Liz want to use the bathroom. 
It would be strange for both Jane and Liz to use the bathroom at the same time. 
So, since Liz is already using the bathroom, the best option for Jane is to wait on using the bathroom."""
        prompt += template.render(
            context="Jane is Liz's house mate. Jane and Liz exchanged a conversation about saying good morning at 07:05am, October 25, 2022",
            date="07:09 AM, October 25, 2022",
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
            date="12:40 PM, October 25, 2022",
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
                return f"{agent.name} is already {event.get_describe(False)}{loc}"
            return f"{agent.name} is on the way to {event.get_describe(False)}{loc}"

        context = ". ".join(
            [c.describe for c in focus["events"] if c.event.predicate == "was"]
        )
        context += "\n" + ". ".join([c.describe for c in focus["thoughts"]])

        prompt += "\nGiven the examples above, determine which option is the most acceptable for the following task:"
        prompt += template.render(
            context=context,
            date=utils.get_timer().get_date("%B %d, %Y, %H:%M %p"),
            name=self.name,
            o_name=other.name,
            status=_status_des(agent),
            o_status=_status_des(other),
            action=agent.get_event().get_describe(False),
            o_action=other.get_event().get_describe(False),
        )

        def _callback(response):
            return response

        return {"prompt": prompt, "callback": _callback, "failsafe": False}

    def prompt_summarize_relation(self, agent, other_name):
        nodes = agent.associate.retrieve_focus([other_name], 50)
        prompt = "[Statements]\n"
        prompt += "\n".join(
            ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
        )
        prompt += f"\n\nBased on the statements above, summarize {self.name} and {other_name}'s relationship (e.g., Tom and Jeo are friends, Elin and John are playing games). What do they feel or know about each other?\n"
        # prompt += f"\n{self.name} and {other_name} are "
        prompt = self._format_output(
            prompt,
            "sentence",
            "Jane and Tom are friends",
            "The output should be ONE sentence that describe the relationship.",
        )

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": self.name + " is looking at " + other_name,
        }

    def prompt_generate_chat(self, agent, other, relation, chats):
        focus = [relation, other.get_event().get_describe()]
        if len(chats) > 4:
            focus.append("; ".join("{}: {}".format(n, t) for n, t in chats[-4:]))
        nodes = agent.associate.retrieve_focus(focus, 15)
        chat_nodes = agent.associate.retrieve_chats(other.name)
        pass_context = ""
        for n in chat_nodes:
            delta = utils.get_timer().get_delta(n.create)
            if delta > 480:
                continue
            pass_context += f"{delta} minutes ago, {agent.name} and {other.name} were already {n.describe}. This context takes place after that conversation.\n"

        address = agent.get_tile().get_address()
        curr_context = (
            f"{agent.name} "
            + f"was {agent.get_event().get_describe(False)} "
            + f"when {agent.name} "
            + f"saw {other.name} "
            + f"in the middle of {other.get_event().get_describe(False)}.\n"
            + f"{agent.name} "
            + "is initiating a conversation with "
            + f"{other.name}."
        )

        conversation = "\n".join(["{}: {}".format(n, u) for n, u in chats])
        conversation = (
            conversation or "[The conversation has not started yet -- start it!]"
        )

        prompt = f"Context for the task:\n\nPART 1. Abstract of {agent.name}\nHere is a brief description of {agent.name}:\n"
        prompt += self._base_desc()
        prompt += f"\nHere is the memory that is in {agent.name}'s head:"
        prompt += "\n- " + "\n- ".join([n.describe for n in nodes])
        prompt += "\n\nPART 2. Past Context\n" + pass_context
        prompt += f"\n\nCurrent Location: {address[-1]} in {address[-2]}"
        prompt += f"\n\nCurrent Context: {curr_context}"
        prompt += f"\n\n{agent.name} and {other.name} are chatting. Here is their conversation so far:\n{conversation}"
        prompt += f"\n---\nTask: Given the context above, what should {agent.name} say to {other.name} next in the conversation? And did it end the conversation?"
        prompt += "\n\nOutput a json of the following format:\n"
        prompt += f"""{{
    "{agent.name}": "<{agent.name}'s utterance>",
    "End the conversation": "<json Boolean>"
}}"""

        def _callback(response):
            assert "{" in response and "}" in response
            json_content = utils.load_dict(
                "{" + response.split("{")[1].split("}")[0] + "}"
            )
            end_chat = json_content["End the conversation"]
            if end_chat in ("false", "no", False):
                end_chat = False
            elif end_chat in ("true", "yes", True):
                end_chat = True
            return (json_content[agent.name], end_chat)

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": (
                "It's nice talking with you, looking forward to next time!",
                True,
            ),
        }

    def prompt_summarize_chats(self, chats):
        conversation = "\n".join(["{}: {}".format(n, u) for n, u in chats])
        prompt = f"""Conversation:
{conversation}

Summarize the conversation above in one short sentence without comma:
"""

        def _callback(response):
            return response.strip(".")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": "general chatting between {} and {}".format(
                chats[0][0], chats[1][0]
            ),
        }

    def prompt_reflect_focus(self, nodes, topk):
        prompt = "[Information]\n" + "\n".join(
            ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
        )
        prompt += f"\n\nGiven the information above, what are {topk} most salient high-level questions?\n1. "

        def _callback(response):
            pattern = ["^\d{1}\. (.*)", "^\d{1} (.*)"]
            return parse_llm_output(response, pattern, mode="match_all")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [
                "Who is {}?".format(self.name),
                "Where do {} lives?".format(self.name),
                "What should {} do today?".format(self.name),
            ],
        }

    def prompt_reflect_insights(self, nodes, topk):
        prompt = (
            "[Statements]\n"
            + "\n".join(
                ["{}. {}".format(idx, n.describe) for idx, n in enumerate(nodes)]
            )
            + "\n\n"
        )
        prompt += f"What {topk} high-level insights can you infer from the above statements? (example format: insight (because of 1, 5, 3))\n1."

        def _callback(response):
            patterns = [
                "^\d{1}\. (.*)\. \(Because of (.*)\)",
                "^\d{1}\. (.*)\. \(because of (.*)\)",
            ]
            insights, outputs = [], parse_llm_output(
                response, patterns, mode="match_all"
            )
            if outputs:
                for insight, reason in outputs:
                    indices = [int(e.strip()) for e in reason.split(",")]
                    node_ids = [nodes[i].node_id for i in indices if i < len(nodes)]
                    insights.append([insight, node_ids])
                return insights
            raise Exception("Can not find insights")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [
                [
                    "{} is thinking on what to do next".format(self.name),
                    [nodes[0].node_id],
                ]
            ],
        }

    def prompt_reflect_chat_planing(self, chats):
        all_chats = "\n".join(["{}: {}".format(n, c) for n, c in chats])
        prompt = f"""[Conversation]
{all_chats}\n
Write down if there is anything from the conversation that {self.name} need to remember for her planning, from {self.name}'s perspective, in a full sentence.
"""

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": f"{self.name} had a sonversation",
        }

    def prompt_reflect_chat_memory(self, chats):
        all_chats = "\n".join(["{}: {}".format(n, c) for n, c in chats])
        prompt = f"""[Conversation]
{all_chats}\n
Write down if there is anything from the conversation that {self.name} might have found interesting from {self.name}'s perspective, in a full sentence.
"""

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": f"{self.name} had a sonversation",
        }

    def prompt_retrieve_plan(self, nodes):
        statements = [
            n.create.strftime("%A %B %d -- %H:%M %p") + ": " + n.describe for n in nodes
        ]
        prompt = "[Statements]" + "\n" + "\n".join(statements) + "\n\n"
        prompt += f"Given the statements above, is there anything that {self.name} should remember when planing for {utils.get_timer().get_date('%A %B %d')}?\n"
        prompt += f"If there is any scheduling information, be as specific as possible (include date, time, and location if stated in the statement)\n\n"
        prompt += f"Write the response from {self.name}'s perspective in lines, each line contains ONE thing to remember."

        def _callback(response):
            pattern = "^\d{1,2}\. (.*)\."
            return parse_llm_output(response, pattern, mode="match_all")

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": [r.describe for r in random.choices(nodes, k=10)],
        }

    def prompt_retrieve_thought(self, nodes):
        statements = [
            n.create.strftime("%A %B %d -- %H:%M %p") + ": " + n.describe for n in nodes
        ]
        prompt = "[Statements]" + "\n" + "\n".join(statements) + "\n\n"
        prompt += f"Given the statements above, how might we summarize {self.name}'s feelings up to now?\n\n"
        prompt += f"Write the response from {self.name}'s perspective in ONE sentence."

        def _callback(response):
            return response

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": "{} should follow the schedule of yesterday".format(self.name),
        }

    def prompt_retrieve_currently(self, plan_note, thought_note):
        time_stamp = (
            utils.get_timer().get_date() - datetime.timedelta(days=1)
        ).strftime("%A %B %d")
        prompt = f"{self.name}'s status from {time_stamp}:\n"
        prompt += f"{self.currently}\n\n"
        prompt += f"{self.name} remember these things at the end of {time_stamp}:\n"
        prompt += ". ".join(plan_note) + "\n\n"
        prompt += f"{self.name}'s feeling at the end of {time_stamp}:\n"
        prompt += thought_note + "\n\n"
        prompt += f"It is now {utils.get_timer().get_date('%A %B %d')}. Given the above, write {self.name}'s status for {utils.get_timer().get_date('%A %B %d')} that reflects {self.name}'s thoughts at the end of {time_stamp}.\n"
        prompt += (
            f"Write this in third-person talking about {self.name} in ONE sentence. "
        )
        prompt += "Follow this format below:\nStatus: <new status>"

        def _callback(response):
            pattern = "^Status: (.*)\."
            return parse_llm_output(response, pattern)

        return {
            "prompt": prompt,
            "callback": _callback,
            "failsafe": self.currently,
        }
