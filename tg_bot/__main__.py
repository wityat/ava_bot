import asyncio
import logging

import coloredlogs
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.fsm.storage.redis import DefaultKeyBuilder, RedisStorage

from aiogram_dialog import setup_dialogs

import tg_bot
from tg_bot.ui.commands import set_bot_commands, remove_bot_commands


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    # noinspection PyUnresolvedReferences
    from tg_bot import dialogs, filters, handlers, middlewares

    await set_bot_commands(tg_bot.bot)
    bot_info = await tg_bot.bot.get_me()

    logging.info(f"Name - {bot_info.full_name}")
    logging.info(f"Username - @{bot_info.username}")
    logging.info(f"ID - {bot_info.id}")

    states = {
        True: "Enabled",
        False: "Disabled",
    }

    logging.debug(f"Groups Mode - {states[bot_info.can_join_groups]}")
    logging.debug(f"Privacy Mode - {states[not bot_info.can_read_all_group_messages]}")
    logging.debug(f"Inline Mode - {states[bot_info.supports_inline_queries]}")

    logging.error("Bot started!")


async def on_shutdown(dispatcher: Dispatcher, bot: Bot):
    logging.warning("Stopping bot...")
    await remove_bot_commands(bot)
    await dispatcher.fsm.storage.close()
    await tg_bot.bot.session.close()
    await tg_bot.db_engine.dispose()


async def main():
    logging_level = logging.DEBUG if tg_bot.arguments.test else logging.INFO
    coloredlogs.install(level=logging_level)
    logging.warning("Starting bot...")

    token = tg_bot.config.bot.test_token if tg_bot.arguments.test else tg_bot.config.bot.token
    tg_bot.bot = Bot(token)

    if tg_bot.config.storage.use_persistent_storage and not tg_bot.arguments.test:
        storage = RedisStorage.from_url(
            url=tg_bot.config.storage.get_redis_url(),
            key_builder=DefaultKeyBuilder(with_destiny=True),
        )
    else:
        storage = MemoryStorage()

    tg_bot.dp = Dispatcher(storage=storage, events_isolation=SimpleEventIsolation())
    tg_bot.dp.startup.register(on_startup)
    tg_bot.dp.shutdown.register(on_shutdown)
    setup_dialogs(tg_bot.dp)

    await tg_bot.dp.start_polling(tg_bot.bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.error("Bot stopped!")
