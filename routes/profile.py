from aiogram import F, html
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.formatting import (
    BlockQuote,
    TextLink,
    Underline,
    as_list,
    as_marked_section,
)

from repositories import user_repository

from . import user_router


@user_router.message(Command("profile"))
@user_router.message(F.text == "Мой профиль")
async def show_profile_handler(message: Message) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    title = BlockQuote(Underline("Мой профиль:"))
    user_link = TextLink(user.full_name, url=f"https://t.me/{user.username}")
    count_channels = user_repository.count_channels(user)
    count_posts = user_repository.count_posts(user)
    await message.answer(
        f"{title.as_html()}\n\n<b>Имя: {user.full_name}</b>\n<b>ID:<code>{user.chat_id}</code></b>\n<b>Cсылка: {user_link.as_html()}</b>\n\n<b>📣 Каналов/чатов: <code>{count_channels}</code></b>\n<b>👥 Постов: <code>{count_posts}</code></b>"
    )
