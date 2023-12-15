import argparse

from aiogram import Bot, Dispatcher

from .config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from .services import KandinskyAPI, FaceSwapper


def parse_arguments():
    parser = argparse.ArgumentParser(description="Process app configuration.")
    parser.add_argument("--test", "-t", help="test bot token", action="store_true")
    return parser.parse_args([])  # hot fix for test starting


dp: Dispatcher
bot: Bot
config: Config = Config()
arguments = parse_arguments()
db_engine = create_async_engine(config.database.get_db_url(), echo=True)
session_maker = async_sessionmaker(db_engine)
kandinsky: KandinskyAPI = KandinskyAPI(config.kandinsky.api_key, config.kandinsky.secret_key)
face_swapper: FaceSwapper = FaceSwapper()
