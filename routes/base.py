from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote, Underline, as_list, as_marked_section

from keyboard.keyboard import get_main_keyboard
from repositories import user_repository

from . import base_router


@base_router.message(CommandStart())
@base_router.message(F.text == "Главное меню")
async def start_handler(message: Message) -> None:
    content = BlockQuote(
        as_list(
            as_marked_section("", "Отложенные посты", marker="🕓 "),
            as_marked_section("", "Зацикленные посты", marker="🔃 "),
            as_marked_section("", "Мультипостинг в каналы и чаты", marker="📢 "),
            as_marked_section(
                "", "Мультиредактор отложенных и зацикленных постов", marker="✅ "
            ),
            as_marked_section("", "Автоподпись постов прямо в канале", marker="✍️ "),
        )
    )
    subtitle = BlockQuote(Underline("Бот создает:"))
    await message.answer(
        f"<b>Бот Автоматизации</b> ведения Telegram Каналов и Чатов \n\n {subtitle.as_html()}\n{content.as_html()}",
        reply_markup=get_main_keyboard(),
    )

    user = user_repository.find_by_chat_id(message.from_user.id)
    if not user:
        # send dice message
        await message.answer_dice(
            emoji="🎲",
            reply_markup=get_main_keyboard(),
        )
        user_repository.create(
            message.from_user.id,
            message.from_user.username,
            message.from_user.full_name,
        )
