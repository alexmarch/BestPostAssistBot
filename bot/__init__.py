import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.i18n import FSMI18nMiddleware, I18n

OWNER_ID = os.getenv("OWNER_ID", None)

bot = Bot(
    token=os.getenv("BOT_TOKEN", ""),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

i18n = I18n(path="locales", default_locale="en", domain="messages")

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
dp.message.middleware(FSMI18nMiddleware(i18n))
dp.update.middleware(FSMI18nMiddleware(i18n))

message_ids_list = []
