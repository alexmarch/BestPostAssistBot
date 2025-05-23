from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from bot import OWNER_ID, bot
from keyboard.keyboard import get_main_keyboard
from repositories import user_repository

from . import base_router


@base_router.message(CommandStart())
@base_router.message(F.text == __("Main menu"))
async def start_handler(message: Message) -> None:
    content = BlockQuote(
        as_list(
            as_marked_section("", _("Scheduled posts"), marker="🕓 "),
            as_marked_section("", _("Looped posts"), marker="🔃 "),
            as_marked_section(
                "", _("Multiposting to channels and chats"), marker="📢 "
            ),
            as_marked_section(
                "", _("Multi-editor for scheduled and looped posts"), marker="✅ "
            ),
            as_marked_section(
                "", _("Auto-signature of posts directly in the channel"), marker="✍️ "
            ),
        )
    )
    await message.answer(
        _(
            "<b>Automation Bot</b> for managing Telegram Channels and Chats \n\n <b>🤖 The bot creates:</b>\n\n{content}"
        ).format(content=content.as_html()),
        reply_markup=get_main_keyboard(),
    )

    user = user_repository.find_by_chat_id(message.from_user.id)

    if not user:
        # todo: get timezone from url parameter
        timezone = "UTC"
        user_repository.create(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
            timezone,
        )
        if OWNER_ID:
            await bot.send_message(
                OWNER_ID,
                f"New user: {message.from_user.id} {message.from_user.username} {message.from_user.full_name}",
            )
