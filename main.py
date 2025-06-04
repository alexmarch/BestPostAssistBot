import asyncio
import logging
import sys

from aiogram.types import BotCommand
from dotenv import load_dotenv

load_dotenv(".env.app")

from bot import bot, dp
from models import create_all
from routes import base_router, post_router, user_router
from utils.scheduler import start_scheduler


async def main() -> None:
    create_all()
    start_scheduler()
    await bot.set_my_commands(
        commands=[
            BotCommand(command="/start", description="Запутить или перезапустить бота"),
            BotCommand(command="/add_channel", description="Добавить канал/чат"),
            BotCommand(command="/create_post", description="Создать пост"),
            BotCommand(command="/edit_post", description="Изменить пост"),
            BotCommand(command="/templates", description="Шаблоны"),
            BotCommand(command="/profile", description="Ваш профиль"),
            BotCommand(command="/settings", description="Настройки"),
        ]
    )

    dp.include_routers(base_router, post_router, user_router)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, close_bot_session=True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
