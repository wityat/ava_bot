from datetime import datetime

import pytz

from app import config


class DateTime:
    @staticmethod
    def get_datetime_from_timestamp(timestamp: int) -> datetime:
        return datetime.fromtimestamp(timestamp, tz=config.bot.timezone)

    @staticmethod
    def get_timestamp_from_datetime(date_time: datetime) -> int:
        return int(date_time.timestamp())

    @staticmethod
    def now():
        return datetime.now(tz=pytz.timezone(config.bot.timezone))
