"""wounderland.utils.timer"""

import datetime
from .namespace import WounderMap, WounderKey


class Timer:
    def __init__(self, start=None, rate=1):
        self._start = start or datetime.datetime.now()
        self._rate = rate

    def get_date(self, date=None):
        date = date or datetime.datetime.now()
        return (date - self._start) * self._rate + self._start

    def get_delta(self, start, end=None, mode="minute"):
        end = end or datetime.datetime.now()
        seconds = (end - start).total_seconds() * self._rate
        if mode == "second":
            return seconds
        if mode == "minute":
            return seconds // 60
        if mode == "hour":
            return seconds // 3600
        return (end - start) * self._rate

    def format_date(self, f_str, date=None):
        return self.get_date(date).strftime(f_str)

    def daily_format(self, date=None):
        return self.format_date("%A %B %d", date)

    def daily_duration(self, date=None, mode="minute"):
        date = self.get_date(date)
        duration = date.hour % 24
        if mode == "hour":
            return duration
        duration = duration * 60 + date.minute
        if mode == "minute":
            return duration
        return datetime.timedelta(minutes=duration)


def set_timer(start=None, rate=1):
    WounderMap.set(WounderKey.TIMER, Timer(start=start, rate=rate))
    return WounderMap.get(WounderKey.TIMER)


def get_timer():
    if not WounderMap.get(WounderKey.TIMER):
        set_timer()
    return WounderMap.get(WounderKey.TIMER)
