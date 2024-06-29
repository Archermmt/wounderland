"""wounderland.memory.action"""

import datetime
from wounderland import utils
from .event import Event


class Action:
    def __init__(
        self,
        event,
        obj_event,
        act_type="action",
        start=None,
        duration=0,
    ):
        self.event = event
        self.obj_event = obj_event
        self.act_type = act_type
        self.start = start or utils.get_timer().get_date()
        self.duration = duration
        self.end = self.start + datetime.timedelta(minutes=self.duration)

    def abstract(self):
        status = "{}[{}~{}]".format(
            "done" if self.finished() else "doing",
            self.start.strftime("%Y%m%d-%H:%M"),
            self.end.strftime("%Y%m%d-%H:%M"),
        )
        return {
            "status": status,
            "event({})".format(self.act_type): str(self.event),
            "object": str(self.obj_event),
        }

    def __str__(self):
        return utils.dump_dict(self.abstract())

    def finished(self):
        if not self.duration:
            return True
        if not self.event.address:
            return True
        return utils.get_timer().get_date() > self.end

    def to_dict(self):
        return {
            "event": self.event.to_dict(),
            "obj_event": self.obj_event.to_dict(),
            "act_type": self.act_type,
            "start": self.start.strftime("%Y%m%d-%H:%M:%S"),
            "duration": self.duration,
        }

    @classmethod
    def from_dict(cls, config):
        config["event"] = Event.from_dict(config["event"])
        config["obj_event"] = Event.from_dict(config["obj_event"])
        config["start"] = utils.to_date(config["start"])
        return cls(**config)
