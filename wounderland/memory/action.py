"""wounderland.memory.action"""

import datetime
from wounderland import utils


class Action:
    def __init__(
        self,
        act_event,
        obj_event,
        act_type="action",
        address=None,
        duration=None,
        start=None,
    ):
        self.act_event = act_event
        self.obj_event = obj_event
        self.act_type = act_type
        self.address = address
        self.duration = duration
        self.start = start
        if not self.start:
            date = datetime.datetime.now()
            self.start = date.hour * 60 + date.minute

    def __str__(self):
        des = {
            "finished": self.finished(),
            "act_event({})".format(self.act_type): self.act_event,
            "obj_event": self.obj_event,
            "address": ":".join(self.address),
        }
        start = datetime.datetime.strptime("00:00:00", "%H:%M:%S") + datetime.timedelta(
            minutes=self.start
        )
        if self.duration:
            end = start + datetime.timedelta(minutes=self.duration)
            des["duration"] = "{}~{}".format(
                start.strftime("%H:%M"), end.strftime("%H:%M")
            )
        else:
            des["start"] = start.strftime("%H:%M")
        return utils.dump_dict(des)

    def finished(self):
        if not self.address:
            return True
        date = datetime.datetime.now()
        total = date.hour * 60 + date.minute
        return self.start + self.duration <= total
