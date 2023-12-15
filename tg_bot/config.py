# sourcery skip: avoid-builtin-shadow
import os
from dataclasses import dataclass, fields, MISSING
from datetime import datetime

import pytz
from dotenv import load_dotenv

load_dotenv()


@dataclass
class KandinskyAPIConfig:
    api_key: str = os.environ.get("KANDINSKY_API_KEY", "")
    secret_key: str = os.environ.get("KANDINSKY_SECRET_KEY", "")


@dataclass
class ConfigBot:
    token: str = os.environ.get("TELEGRAM_TOKEN", "")
    test_token: str = os.environ.get("TEST_TELEGRAM_TOKEN", "")
    timezone: datetime.tzinfo = pytz.timezone(
        os.environ.get("TIME_ZONE", "Europe/Moscow")
    )


@dataclass
class ConfigDatabase:
    user: str = os.environ.get("POSTGRES_USER", "user")
    password: str = os.environ.get("POSTGRES_PASSWORD", "fsdfagfsdy5r")
    database_name: str = os.environ.get("POSTGRES_DB", "db")
    port: str = os.environ.get("POSTGRES_PORT", "5432")
    host: str = os.environ.get("POSTGRES_HOST", "localhost")
    protocol: str = "postgresql+asyncpg"

    def get_db_url(self):
        return f"{self.protocol}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database_name}"


@dataclass
class ConfigStorage:
    use_persistent_storage: bool = True
    user: str = os.environ.get("REDIS_USER", "user")
    password: str = os.environ.get("REDIS_PASSWORD", "fsdfagfsdy5r")
    host: str = os.environ.get("REDIS_HOST", "redis")
    port: str = os.environ.get("REDIS_PORT_NUMBER", "6379")
    database_name: str = os.environ.get("REDIS_DB", "0")

    @classmethod
    def get_redis_url(cls):
        return f"redis://:{cls.password}@{cls.host}:{cls.port}/{cls.database_name}"


@dataclass
class BotSettings:
    throttling_rate: int = 60


@dataclass
class Config:
    """
    Класс для хранения переменных окружения и чувствительных данных.
    Данные подтягиваются из .env файла.
    """

    bot: ConfigBot = ConfigBot()
    database: ConfigDatabase = ConfigDatabase()
    storage: ConfigStorage = ConfigStorage()
    kandinsky: KandinskyAPIConfig = KandinskyAPIConfig()
    settings: BotSettings = BotSettings()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    config = Config()
    print(config)
