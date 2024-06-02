"""wounderland.memory.action"""

import datetime
from wounderland import utils


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
