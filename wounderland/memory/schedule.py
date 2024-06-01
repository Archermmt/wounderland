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
        self.hourly_schedule = config.get("hourly_schedule", [])
        self.diversity = config.get("schedule_diversity", 5)
        self.max_try = config.get("schedule_max_try", 3)

    def __str__(self):
        des = {"daily": {}, "hourly": {}}
        schedules = {"daily": self.daily_schedule, "hourly": self.hourly_schedule}
        for key, sch in schedules.items():
            duration = datetime.datetime.strptime("00:00:00", "%H:%M:%S")
            for plan, dur in sch:
                start, duration = duration, duration + datetime.timedelta(minutes=dur)
                start, end = start.strftime("%H:%M"), duration.strftime("%H:%M")
                des[key]["{}~{}".format(start, end)] = plan
        return utils.dump_dict(des)

    def decompose(self, schedule, duration):
        if "sleep" not in schedule and "bed" not in schedule:
            return True
        if "sleeping" in schedule or "asleep" in schedule or "in bed" in schedule:
            return False
        if "sleep" in schedule or "bed" in schedule:
            return duration <= 60
        return True

    def get_duration(self, end, start=-1, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        if end < 0:
            end = len(sch) + end
        if start == -1:
            duration = sch[end][1]
        else:
            duration = sum([sch[i][1] for i in range(start, end + 1)])
        return duration

    def extend_duration(self, index, duration, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        sch[index] = (sch[index][0], sch[index][1] + duration)
        return sch[index]

    def get_plan(self, index, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        return sch[index][0]

    def get_period(self, index, hourly=True, time_format="%H:%M%p"):
        def _to_date(minutes):
            date = datetime.datetime.strptime(
                "00:00:00", "%H:%M:%S"
            ) + datetime.timedelta(minutes=minutes)
            return date.strftime(time_format)

        start = self.get_duration(index - 1, 0, hourly=hourly)
        end = start + self.get_duration(index, hourly=hourly)
        if time_format:
            start, end = _to_date(start), _to_date(end)
        return start, end

    def add_schedule(self, plan, duration, index=-1, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        if index == -1:
            sch.append((plan, duration))
        else:
            sch.insert(index, (plan, duration))
        return sch[index]

    def extend_schedules(self, schedules, index=-1, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        if index == -1:
            sch.extend(schedules)
        else:
            sch[index : index + 1] = schedules
        return sch[index]

    def schedule_at(self, date=None, hourly=True):
        sch = self.hourly_schedule if hourly else self.daily_schedule
        date = date or datetime.datetime.now()
        total_minute, duration = date.hour * 60 + date.minute, 0
        for plan, dur in sch:
            duration += dur
            if duration >= total_minute:
                return plan, dur
        return sch[-1]

    def scheduled(self, date=None):
        if not self.daily_schedule:
            return False
        date = date or datetime.datetime.now()
        return date.strftime("%A %B %d") == self.created_at.strftime("%A %B %d")
