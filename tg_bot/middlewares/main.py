from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tg_bot import bot, config, dp, session_maker
from tg_bot.database.models import User
from tg_bot.dialogs.states import MainDialogStates
from tg_bot.exceptions.db import DBException


class MainMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self.config = config
        self.bot = bot
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_maker() as db_session:
            data["config"] = self.config
            data["bot"] = self.bot
            data["db_session"] = db_session
            await handler(event, data)


md = MainMiddleware()
dp.message.middleware(md)
dp.callback_query.middleware(md)
