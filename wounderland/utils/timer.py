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
    def __init__(self, start=None):
        self._mode = "on_time"
        self._start = datetime.datetime.now()
        self._offset = datetime.timedelta(0)
        self._rate = 1
        self._freeze_at = None
        if start:
            d_format = "%Y%m%d-%H:%M" if "-" in start else "%H:%M"
            self._offset = to_date(start, d_format) - self._start

    def forward(self, offset):
        self._offset += datetime.timedelta(minutes=offset)

    def speedup(self, rate):
        self._rate = rate

    def freeze(self):
        if self._mode == "on_time":
            self._freeze_at = self.get_date()
            self._mode = "freeze"

    def unfreeze(self):
        if self._mode == "freeze":
            self._mode = "on_time"
            self._offset -= self.get_date() - self._freeze_at

    def get_date(self, date_format=""):
        if self._mode == "on_time":
            now = datetime.datetime.now()
            date = self._start + (now - self._start) * self._rate + self._offset
        elif self._mode == "freeze":
            assert self._freeze_at, "Call freeze before use freeze mode"
            date = self._freeze_at
        else:
            raise TypeError("Unexpected time mode " + str(self._mode))
        if date_format:
            return date.strftime(date_format)
        return date

    def get_delta(self, start, end=None, mode="minute"):
        end = end or self.get_date()
        seconds = (end - start).total_seconds()
        if mode == "second":
            return seconds
        if mode == "minute":
            return round(seconds / 60)
        if mode == "hour":
            return round(seconds / 3600)
        return end - start

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


def set_timer(start=None):
    WounderMap.set(WounderKey.TIMER, Timer(start=start))
    return WounderMap.get(WounderKey.TIMER)


def get_timer():
    if not WounderMap.get(WounderKey.TIMER):
        set_timer()
    return WounderMap.get(WounderKey.TIMER)
