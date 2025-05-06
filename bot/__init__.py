import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

bot = Bot(
    token=os.getenv("TOKEN", ""),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()

message_ids_list = []
