from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import BlockQuote, TextLink

from keyboard.keyboard import (
    GeneralSettingsButtonData,
    get_confirm_auto_repeat_keyboard,
    get_general_settings_keyboard,
    get_multiposting_keyboard,
    get_post_jobs_keyboard,
    get_post_multiposting_keyboard,
    get_settings_multiposting_keyboard,
)
from repositories import user_repository
from states.post import PostForm
from utils.messages import get_confirm_auto_repeat_message, get_multiposting_message
from utils.scheduler import (
    get_all_jobs_by_user_id,
    parse_time_from_str,
    remove_job_by_id,
    remove_job_by_time_interval,
)

from . import user_router


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
    await state.set_state(PostForm.settings)
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
        await state.set_state(PostForm.settings)
        await query.message.edit_text(
            f"{title.as_html()}\n\n",
            reply_markup=get_general_settings_keyboard(state_data),
            inline_message_id=query.inline_message_id,
        )

    if callback_data.action == "show_posting_tasks":
        time_frames = state_data.get("time_frames")
        jobs, stop_jobs = get_all_jobs_by_user_id(time_frames, user.id)
        await query.message.edit_text(
            f"📋 <b>Задачи публикации постов:</b>\n\n<b>Всего задач: <code>{len(jobs)}</code></b>",
            reply_markup=get_post_jobs_keyboard(state_data, jobs),
            inline_message_id=query.inline_message_id,
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

    if callback_data.action == "delete_post_job":
        time_frames = state_data.get("time_frames")
        job_index = int(callback_data.data)
        jobs, stop_jobs = get_all_jobs_by_user_id(time_frames, user.id)

        if not len(jobs):
            return

        job = remove_job_by_id(jobs[job_index].id)

        if len(stop_jobs):
            remove_job_by_id(stop_jobs[job_index].id)

        if job:
            # remove element from jobs list
            job_id = jobs[job_index].id
            jobs.pop(job_index)
            await query.message.edit_text(
                f"✅ Задача публикации поста <code>{job_id}</code> удалена.",
                reply_markup=get_post_jobs_keyboard(state_data, jobs),
                inline_message_id=query.inline_message_id,
            )
        else:
            await query.message.edit_text(
                f"⚠️ Задача публикации поста <code>{job_id}</code> не найдена.",
                reply_markup=get_post_jobs_keyboard(state_data, jobs),
                inline_message_id=query.inline_message_id,
            )

    if callback_data.action == "delete_multiposting_timeframe":
        user_repository.delete_multiposting_timeframe(user)
        remove_job_by_time_interval(state_data.get("time_frames"), user.id)

        await state.update_data(time_frames=None)
        state_data = await state.get_data()
        time_frames = state_data.get("time_frames", [])

        await query.message.edit_text(
            get_multiposting_message(time_frames),
            inline_message_id=query.inline_message_id,
            reply_markup=(get_settings_multiposting_keyboard(state_data)),
        )

    if callback_data.action == "show_multi_timeframe":

        state_before = await state.get_state()

        if state_before == PostForm.settings:
            await state.set_state(PostForm.settings_time_frames)
        else:
            await state.set_state(PostForm.time_frames)

        time_frames = state_data.get("time_frames", [])

        await query.message.edit_text(
            get_multiposting_message(time_frames),
            inline_message_id=query.inline_message_id,
            reply_markup=(
                get_post_multiposting_keyboard(state_data)
                if state_before != PostForm.settings
                else get_settings_multiposting_keyboard(state_data)
            ),
        )


@user_router.message(PostForm.settings_time_frames)
async def create_settings_time_frames_start_handler(
    message: Message, state: FSMContext
) -> None:
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

    await state.update_data(time_frames=time_frames_list)

    user_repository.create_multiposting(user, time_frames_list)

    state_data = await state.get_data()

    await message.answer(
        text=get_multiposting_message(state_data.get("time_frames", [])),
        reply_markup=get_multiposting_keyboard(state_data),
    )


@user_router.message(PostForm.time_frames)
async def create_time_frames_handler(message: Message, state: FSMContext) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    state_data = await state.get_data()
    time_frames = message.text.split(",")
    auto_repeat_dates = state_data.get("auto_repeat_dates", [])
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

    await state.update_data(time_frames=time_frames_list)

    user_repository.create_multiposting(user, time_frames_list)

    state_data = await state.get_data()

    if len(auto_repeat_dates):
        confirm_message = get_confirm_auto_repeat_message(state_data, time_frames_list)
        await message.answer(
            text=confirm_message,
            reply_markup=get_confirm_auto_repeat_keyboard(state_data),
        )
    else:
        confirm_message = "<b>⏰ Текущее расписание публикации:</b>\n" + "\n".join(
            [f"<i>{time_frame}</i>" for time_frame in time_frames_list]
        )
        await message.answer(
            text=confirm_message,
            reply_markup=get_multiposting_keyboard(state_data, "back"),
        )
