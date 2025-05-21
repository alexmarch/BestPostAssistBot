import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

OWNER_ID = os.getenv("OWNER_ID", None)

bot = Bot(
    token=os.getenv("BOT_TOKEN", ""),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

message_ids_list = []
