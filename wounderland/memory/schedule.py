"""wounderland.memory.schedule"""


class Schedule:
    def __init__(self, config):
        self.config = config
        self.date = None
        self.daily_schedule = None
        self.hourly_schedule = None
