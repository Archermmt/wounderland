"""wounderland.utils.timer"""

import datetime
from .namespace import WounderMap, WounderKey


def to_date(date_str, date_format="%Y%m%d-%H:%M:%S"):
    if date_format == "%I:%M %p" and date_str.startswith("0:00"):
        date_str = date_str.replace("0:00", "12:00")
    return datetime.datetime.strptime(date_str, date_format)


def daily_duration(date, mode="minute"):
    duration = date.hour % 24
    if mode == "hour":
        return duration
    duration = duration * 60 + date.minute
    if mode == "minute":
        return duration
    return datetime.timedelta(minutes=duration)


class Timer:
    def __init__(self, start=None, offset=0, rate=1, mode="on_time"):
        self._mode = mode
        self._start = datetime.datetime.now()
        self._offset = offset
        if start:
            if "-" in start:
                date = to_date(start, "%Y%m%d-%H:%M").replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                today = self._start.replace(hour=0, minute=0, second=0, microsecond=0)
                self._offset += (date - today).days * 24 * 60
                start = start.split("-")[1]
            s_minute = daily_duration(to_date(start, "%H:%M"))
            self._offset += s_minute - daily_duration(self._start)
        self._freeze_offset = None
        self._rate = rate

    def forward(self, offset):
        if self._freeze_offset:
            self._freeze_offset += offset
        else:
            self._offset += offset

    def speedup(self, rate):
        self._rate = rate

    def freeze(self):
        if self._mode == "on_time":
            self._freeze_offset = self._offset
            self._offset = (self.get_date() - self._start).total_seconds() // 60
            self._mode = "step"

    def unfreeze(self):
        if self._mode == "step":
            self._offset, self._freeze_offset = self._freeze_offset, None
            self._mode = "on_time"

    def get_date(self, date_format=""):
        if self._mode == "on_time":
            date = datetime.datetime.now()
            delta = (date - self._start) * self._rate + datetime.timedelta(
                minutes=self._offset
            )
        elif self._mode == "step":
            delta = datetime.timedelta(minutes=self._offset)
        else:
            raise TypeError("Unexpected time mode " + str(self._mode))
        date = delta + self._start
        if date_format:
            return date.strftime(date_format)
        return date

    def get_delta(self, start, end=None, mode="minute"):
        end = end or self.get_date()
        seconds = (end - start).total_seconds() * self._rate
        if mode == "second":
            return seconds
        if mode == "minute":
            return seconds // 60
        if mode == "hour":
            return seconds // 3600
        return (end - start) * self._rate

    def daily_format(self):
        return self.get_date("%A %B %d")

    def daily_duration(self, mode="minute"):
        return daily_duration(self.get_date(), mode)

    def daily_time(self, duration):
        base = self.get_date().replace(hour=0, minute=0, second=0, microsecond=0)
        return base + datetime.timedelta(minutes=duration)

    @property
    def mode(self):
        return self._mode


def set_timer(start=None, offset=0, rate=1, mode="on_time"):
    WounderMap.set(
        WounderKey.TIMER, Timer(start=start, offset=offset, rate=rate, mode=mode)
    )
    return WounderMap.get(WounderKey.TIMER)


def get_timer():
    if not WounderMap.get(WounderKey.TIMER):
        set_timer()
    return WounderMap.get(WounderKey.TIMER)
