from aiogram import F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.utils.formatting import BlockQuote, Underline, as_list, as_marked_section

from bot import OWNER_ID, bot
from keyboard.keyboard import get_main_keyboard
from repositories import user_repository
from states.post import PostForm
from utils.messages import get_notify_update_version_message

from . import base_router


@base_router.message(Command("admin_message"))
async def admin_message_handler(message: Message, state: FSMContext) -> None:
    if OWNER_ID == str(message.from_user.id):
        await state.set_state(PostForm.admin_message)
        await message.answer(
            "Введите сообщение для отправки всем пользователям бота. "
            "Вы можете использовать HTML-теги, например, <b>bold</b> или <i>italic</i>."
        )


@base_router.message(PostForm.admin_message)
async def send_admin_message_handler(message: Message, state: FSMContext) -> None:
    if OWNER_ID == str(message.from_user.id):
        text = message.text
        users = user_repository.get_all_users()
        if not users:
            await message.answer("Пользователей нет")
            return

        for user in users:
            try:
                message = await bot.send_message(
                    user.chat_id,
                    f"<b>⚜️ Admin:</b>\n\n {text}",
                    disable_web_page_preview=True,
                    parse_mode="HTML",
                )
                await bot.pin_chat_message(
                    user.chat_id,
                    message.message_id,
                    disable_notification=True,
                )
            except Exception as e:
                print(f"Failed to send message to {user.chat_id}: {e}")

        await state.clear()
        await message.answer("Сообщение отправлено всем пользователям.")
    else:
        await message.answer("У вас нет прав для этой команды.")


@base_router.message(Command("users"))
async def users_handler(message: Message) -> None:
    if OWNER_ID == str(message.from_user.id):
        users = user_repository.get_all_users()
        text = message.text
        if not users:
            await message.answer("Пользователей нет")
            return

        user_list = "\n".join(
            f"{user.chat_id} - {user.username} - {user.full_name}" for user in users
        )
        await message.answer(
            f"<b>Список пользователей:</b>\n\n{Underline(text)}\n\n{user_list}",
            parse_mode="HTML",
        )


@base_router.message(Command("version"))
async def version_handler(message: Message) -> None:
    if OWNER_ID == str(message.from_user.id):
        users = user_repository.get_all_users()
        for user in users:
            message = await bot.send_message(
                user.chat_id,
                get_notify_update_version_message(),
                disable_web_page_preview=True,
            )
            await bot.pin_chat_message(
                user.chat_id,
                message.message_id,
                disable_notification=False,
            )


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
    await message.answer(
        f"<b>Бот Автоматизации</b> ведения Telegram Каналов и Чатов \n\n <b>🤖 Бот создает:</b>\n\n{content.as_html()}",
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
