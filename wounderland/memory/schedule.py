"""wounderland.memory.schedule"""

import datetime
from wounderland import utils


class Schedule:
    def __init__(self, config):
        if config.get("created_at"):
            self.created_at = datetime.datetime.strptime(
                config["created_at"], "%Y%m%d %H:%M:%S"
            )
        else:
            self.created_at = None
        self.daily_schedule = config.get("daily_schedule", [])
        self.diversity = config.get("schedule_diversity", 5)
        self.max_try = config.get("schedule_max_try", 3)

    def __str__(self):
        def _to_stamp(plan):
            start, end = self.plan_stamps(plan, time_format="%H:%M")
            return "{}~{}".format(start, end)

        plan_info = {}
        for plan in self.daily_schedule:
            stamp = _to_stamp(plan)
            if plan.get("decompose"):
                s_info = {_to_stamp(p): p["describe"] for p in plan["decompose"]}
                plan_info[stamp + ": " + plan["describe"]] = s_info
            else:
                plan_info[stamp] = plan["describe"]
        return utils.dump_dict(plan_info)

    def add_plan(self, describe, duration, decompose=None):
        if self.daily_schedule:
            last_plan = self.daily_schedule[-1]
            start = last_plan["start"] + last_plan["duration"]
        else:
            start = 0
        self.daily_schedule.append(
            {
                "idx": len(self.daily_schedule),
                "describe": describe,
                "start": start,
                "duration": duration,
                "decompose": decompose or {},
            }
        )
        return self.daily_schedule[-1]

    def plan_at(self, date=None):
        total_minute = utils.get_timer().daily_duration(date)
        for plan in self.daily_schedule:
            if self.plan_stamps(plan)[1] <= total_minute:
                continue
            for de_plan in plan.get("decompose", []):
                if self.plan_stamps(de_plan)[1] <= total_minute:
                    continue
                return plan, de_plan
            return plan, plan
        last_plan = self.daily_schedule[-1]
        return last_plan, last_plan

    def plan_stamps(self, plan, time_format=None):
        def _to_date(minutes):
            date = datetime.datetime.strptime(
                "00:00:00", "%H:%M:%S"
            ) + datetime.timedelta(minutes=minutes)
            return date.strftime(time_format)

        start, end = plan["start"], plan["start"] + plan["duration"]
        if time_format:
            start, end = _to_date(start), _to_date(end)
        return start, end

    def decompose(self, plan):
        if plan.get("decompose"):
            return False
        describe = plan["describe"]
        if "sleep" not in describe and "bed" not in describe:
            return True
        if "sleeping" in describe or "asleep" in describe or "in bed" in describe:
            return False
        if "sleep" in describe or "bed" in describe:
            return plan["duration"] <= 60
        return True

    def scheduled(self, date=None):
        if not self.daily_schedule:
            return False
        return utils.get_timer().daily_format(date) == self.created_at.strftime(
            "%A %B %d"
        )

    def to_dict(self):
        return {
            "created_at": self.created_at.strftime("%Y%m%d %H:%M:%S"),
            "daily_schedule": self.daily_schedule,
        }
