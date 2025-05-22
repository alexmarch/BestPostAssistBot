import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n

OWNER_ID = os.getenv("OWNER_ID", None)

bot = Bot(
    token=os.getenv("BOT_TOKEN", ""),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

i18n = I18n(path="locales", default_locale="en", domain="messages")

dp = Dispatcher()

message_ids_list = []
