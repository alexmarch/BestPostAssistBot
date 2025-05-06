from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.formatting import BlockQuote, TextLink, Underline

from keyboard.keyboard import (
    GeneralSettingsButtonData,
    get_general_settings_keyboard,
    get_multiposting_keyboard,
)
from repositories import user_repository
from states.post import PostForm
from utils.scheduler import parse_time_from_str

from . import user_router

timeframe_example = FSInputFile("assets/timeframe_example.png")


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


@user_router.message(Command("settings"))
@user_router.message(F.text == "Настройки")
async def show_settings_handler(
    message: Message,
    state: FSMContext,
) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    multiposting = user_repository.get_multiposting_by_user_id(user.id)
    if multiposting:
        time_frames = multiposting.time_frames.split("|")
        await state.update_data(
            time_frames=time_frames,
            time_frames_active="on" if multiposting.active else "off",
        )
    else:
        await state.update_data(time_frames=None, time_frames_active="off")

    title = BlockQuote("⚙️ Настройки:")
    state_data = await state.get_data()

    await message.answer(
        f"{title.as_html()}\n\n", reply_markup=get_general_settings_keyboard(state_data)
    )


@user_router.callback_query(
    GeneralSettingsButtonData.filter(F.type == "general_settings_action")
)
async def show_general_settings_handler(
    query: CallbackQuery, state: FSMContext, callback_data: GeneralSettingsButtonData
) -> None:
    user = user_repository.find_by_chat_id(query.from_user.id)
    state_data = await state.get_data()

    if callback_data.action == "back":
        title = BlockQuote("⚙️ Настройки:")
        await query.message.answer(
            f"{title.as_html()}\n\n",
            reply_markup=get_general_settings_keyboard(state_data),
        )

    if callback_data.action == "active_multiposting_timeframe":
        status = "on" if state_data.get("time_frames_active") == "off" else "off"
        user_repository.update_multiposting_active_timeframe(user, status)
        await state.update_data(time_frames_active=status)
        state_data = await state.get_data()
        await query.message.edit_reply_markup(
            inline_message_id=query.inline_message_id,
            reply_markup=get_multiposting_keyboard(state_data),
        )

    if callback_data.action == "delete_multiposting_timeframe":
        user_repository.delete_multiposting_timeframe(user)
        await state.update_data(time_frames=None)
        await query.message.answer(
            "⏰ Расписание мультипостинга удалено. Теперь посты будут выходить сразу после создания."
        )
        state_data = await state.get_data()

    if (
        callback_data.action == "show_multiposting_timeframe"
        or callback_data.action == "delete_multiposting_timeframe"
    ):
        await state.set_state(PostForm.time_frames)
        time_frames = state_data.get("time_frames")
        await query.message.answer(
            f"""<b>🗓 Расписание</b>\n\n
<b>Здесь можно установить ежедневное расписание постов в режиме мультипостинга, чтобы в дальнейшем планировать публикации всего одним кликом сразу в несколько каналов.</b>\n\n
Чтобы задать расписание, отправь время выхода постов в виде списка в любом удобном формате.\n\n
{BlockQuote("\n".join(time_frames)).as_html() if time_frames else ""}\n\n
"""
        )
        await query.message.answer_photo(
            timeframe_example,
            parse_mode="HTML",
            reply_markup=get_multiposting_keyboard(state_data),
        )


@user_router.message(PostForm.time_frames)
async def create_time_frames_handler(message: Message, state: FSMContext) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    # state_data = await state.get_data()
    # split text by \n and remove empty strings
    time_frames = message.text.split("\n")
    time_frames = [
        time_frame.strip() for time_frame in time_frames if time_frame.strip()
    ]
    # check if time_frames is empty
    if not time_frames:
        await message.answer("⚠️ Пожалуйста, введите хотя бы одно время.")
        return
    # check if time_frames is valid
    time_frames_list = []
    for time_frame in time_frames:
        try:
            (hours, minutes) = parse_time_from_str(time_frame)
            time_frames_list.append(f"{hours}:{minutes}")

        except Exception as e:
            await message.answer("⚠️ Ошибка формата времяни, повторите ввод.")
            return

    user_repository.create_multiposting(user, time_frames_list)
    await state.update_data(time_frames=time_frames_list)
    state_data = await state.get_data()
    await message.answer(
        f"""🗓 Расписание\n\n {BlockQuote("\n".join(time_frames_list)).as_html()}""",
        parse_mode="HTML",
    )
    await message.answer_photo(
        timeframe_example,
        parse_mode="HTML",
        reply_markup=get_multiposting_keyboard(state_data),
    )
