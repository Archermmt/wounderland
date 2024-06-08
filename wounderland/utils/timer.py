"""wounderland.utils.timer"""

import datetime
from .namespace import WounderMap, WounderKey


def to_date(date_str, date_format="%Y%m%d-%H:%M:%S"):
    return datetime.datetime.strptime(date_str, date_format)


def daily_time(duration):
    return datetime.datetime.strptime("00:00:00", "%H:%M:%S") + datetime.timedelta(
        minutes=duration
    )


class Timer:
    def __init__(self, start=None, offset=0, rate=1):
        if start:
            self._start = daily_time(start)
        else:
            self._start = datetime.datetime.now()
        self._offset = offset
        self._rate = rate

    def forward(self, offset):
        self._offset += offset

    def speedup(self, rate):
        self._rate = rate

    def get_date(self, date_format=""):
        date = datetime.datetime.now()
        delta = (date - self._start) * self._rate + datetime.timedelta(
            minutes=self._offset
        )
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
        date = self.get_date()
        duration = date.hour % 24
        if mode == "hour":
            return duration
        duration = duration * 60 + date.minute
        if mode == "minute":
            return duration
        return datetime.timedelta(minutes=duration)


def set_timer(start=None, offset=0, rate=1):
    WounderMap.set(WounderKey.TIMER, Timer(start=start, offset=offset, rate=rate))
    return WounderMap.get(WounderKey.TIMER)


def get_timer():
    if not WounderMap.get(WounderKey.TIMER):
        set_timer()
    return WounderMap.get(WounderKey.TIMER)
