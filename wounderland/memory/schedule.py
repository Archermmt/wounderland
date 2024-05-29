"""wounderland.memory.schedule"""

from datetime import datetime
from wounderland import utils


class Schedule:
    def __init__(self, config):
        self.config = config
        self.created_at = None
        self.hourly_schedule = None
        self.daily_schedule = None

    def __str__(self):
        des = {"hourly": self.hourly_schedule, "daily": self.daily_schedule}
        return utils.dump_dict(des)

    def decompose(self, schedule, duration):
        if "sleep" not in schedule and "bed" not in schedule:
            return True
        if "sleeping" in schedule or "asleep" in schedule or "in bed" in schedule:
            return False
        if "sleep" in schedule or "bed" in schedule:
            return duration <= 60
        return True

    def scheduled(self, date=None):
        if not self.daily_schedule:
            return False
        date = date or datetime.now()
        return date.strftime("%A %B %d") == self.created_at.strftime("%A %B %d")
