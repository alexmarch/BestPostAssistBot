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
from utils.scheduler import parse_time_from_str, remove_job_by_time_interval

from . import user_router

timeframe_example = FSInputFile("assets/timeframe_example.png")


@user_router.message(Command("profile"))
@user_router.message(F.text == "Мой профиль")
async def show_profile_handler(message: Message) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    user_link = TextLink(user.full_name, url=f"https://t.me/{user.username}")
    count_channels = user_repository.count_channels(user)
    count_posts = user_repository.count_posts(user)
    await message.answer(
        text=f"<b>Имя: {user.full_name}</b>\n<b>ID:<code>{user.chat_id}</code></b>\n<b>Cсылка: {user_link.as_html()}</b>\n\n<b>📣 Каналов/чатов: <code>{count_channels}</code></b>\n<b>👥 Постов: <code>{count_posts}</code></b>",
        reply_to_message_id=message.message_id,
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
        remove_job_by_time_interval(state_data.get("time_frames"), user.id)
        await state.update_data(time_frames=None)
        state_data = await state.get_data()
        await query.message.edit_text(
            "⏰ Расписание мультипостинга удалено. Теперь посты будут выходить сразу после создания.",
            eply_markup=get_multiposting_keyboard(state_data),
            inline_message_id=query.inline_message_id,
        )

    if (
        callback_data.action == "show_multiposting_timeframe"
        or callback_data.action == "delete_multiposting_timeframe"
    ):
        await state.set_state(PostForm.time_frames)
        time_frames = state_data.get("time_frames")
        await query.message.edit_text(
            f"""
<b>🗓 Расписание</b>\n
Здесь можно установить ежедневное расписание постов в режиме мультипостинга, чтобы в дальнейшем планировать публикации всего одним кликом сразу в несколько каналов.\n
Чтобы задать расписание, отправь время выхода постов в виде списка в любом удобном формате.\n
🕒 <b>Публикация по времени</b>(отправте время в любом из форматов):\n
{BlockQuote("12:00 - Опубликуется в 12:00\n12 00 - Опубликуется в 12:00\n1200 - Опубликуется в 12:00\n12 00, 15 00, 18 00 - Опубликуется в 12:00, 15:00, 18:00").as_html()}\n
🕒 <b>Настройка интервалов выхода постов:</b>\n
{BlockQuote('30m - Опубликуется каждые 30 минут\n12h - Опубликуется каждые 12часов\n1h 30m - Опубликуется каждый 1 часа 30 минут').as_html()}\n
⚠️ <b>ВАЖНО!</b> Минимальное время автоповтора/зацикленности 15m (минут)\n
{ '⏰ <b>Текущее расписание публикации:</b>\n' if time_frames else "" }
{BlockQuote("\n".join(time_frames)).as_html() if time_frames else ""}\n
""",
            inline_message_id=query.inline_message_id,
            reply_markup=get_multiposting_keyboard(state_data),
        )


@user_router.message(PostForm.time_frames)
async def create_time_frames_handler(message: Message, state: FSMContext) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    state_data = await state.get_data()
    time_frames = message.text.split(",")
    time_frames = [
        time_frame.strip() for time_frame in time_frames if time_frame.strip()
    ]
    # check if time_frames is empty
    if not time_frames:
        await message.answer(
            text="⚠️ Пожалуйста, введите хотя бы одно время.",
            reply_to_message_id=message.message_id,
            reply_markup=get_multiposting_keyboard(state_data),
        )
        return

    # check if time_frames is valid
    time_frames_list = []
    for time_frame in time_frames:
        try:
            time_interval = parse_time_from_str(time_frame)
            time_frames_list.append(time_interval)
        except Exception as e:
            await message.answer(
                text="⚠️ Ошибка формата времяни, повторите ввод.",
                reply_to_message_id=message.message_id,
                reply_markup=get_multiposting_keyboard(state_data),
            )
            return

    user_repository.create_multiposting(user, time_frames_list)
    await state.update_data(time_frames=time_frames_list)
    state_data = await state.get_data()
    await message.answer(
        f"""
        ⏰ <b>Текущее расписание публикации:</b>
        {BlockQuote("\n".join(time_frames_list)).as_html()}
        """,
        reply_to_message_id=message.message_id,
        reply_markup=get_multiposting_keyboard(state_data),
    )
