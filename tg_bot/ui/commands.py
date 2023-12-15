from aiogram import Bot
from aiogram.types import BotCommand, BotCommandScopeDefault

users_commands = {
    "start": "Начать",
}


async def set_bot_commands(bot: Bot):
    await bot.set_my_commands(
        [
            BotCommand(command=command, description=description)
            for command, description in users_commands.items()
        ],
        scope=BotCommandScopeDefault(),
    )


async def remove_bot_commands(bot: Bot):
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
