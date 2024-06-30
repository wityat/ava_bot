from aiogram import F, Bot, types
from aiogram.filters.command import CommandStart, CommandObject
from aiogram.types import Message
from aiogram_dialog import DialogManager, StartMode
from sqlalchemy.ext.asyncio import AsyncSession

from tg_bot import dp
from tg_bot.database import User
from tg_bot.dialogs.states import MainDialogStates
from tg_bot.exceptions.db import DBException


@dp.message(CommandStart())
async def cmd_start(message: types.Message, dialog_manager: DialogManager, db_session: AsyncSession):
    try:
        user: User = await User.get(db_session, message.from_user.id)
    except DBException:
        user: User = User(tg_id=message.from_user.id)
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    if await user.awaitable_attrs.accepted_terms:
        await dialog_manager.start(MainDialogStates.photo_upload)
    else:
        await dialog_manager.start(MainDialogStates.greeting)
