from datetime import datetime
from zoneinfo import ZoneInfo

from config import Config


def app_timezone():
    return ZoneInfo(Config.TIMEZONE)


def now_brazil():
    return datetime.now(app_timezone()).replace(tzinfo=None)


def today_brazil():
    return now_brazil().date()


def format_datetime_brazil(value, fmt="%d/%m/%Y %H:%M"):
    if not value:
        return ""
    return value.strftime(fmt)
