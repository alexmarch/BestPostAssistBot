from aiogram import F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.formatting import BlockQuote, TextLink, Underline
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __

from keyboard.keyboard import (
    GeneralSettingsButtonData,
    get_general_settings_keyboard,
    get_multiposting_keyboard,
    get_post_jobs_keyboard,
)
from repositories import user_repository
from states.post import PostForm
from utils.scheduler import (
    get_all_jobs_by_user_id,
    parse_time_from_str,
    remove_job_by_id,
    remove_job_by_time_interval,
)

from . import user_router


@user_router.message(Command("profile"))
@user_router.message(F.text == __("My profile"))
async def show_profile_handler(message: Message) -> None:
    user = user_repository.find_by_chat_id(message.from_user.id)
    user_link = TextLink(user.full_name, url=f"https://t.me/{user.username}")
    count_channels = user_repository.count_channels(user)
    count_posts = user_repository.count_posts(user)
    await message.answer(
        text=_(
            "<b>Name: {name}</b>\n<b>ID:<code>{id}</code></b>\n<b>Link: {link}</b>\n\n<b>📣 Channels/chats: <code>{channels}</code></b>\n<b>👥 Posts: <code>{posts}</code></b>"
        ).format(
            name=user.full_name,
            id=user.chat_id,
            link=user_link.as_html(),
            channels=count_channels,
            posts=count_posts,
        ),
        reply_to_message_id=message.message_id,
    )


@user_router.message(Command("settings"))
@user_router.message(F.text == __("Settings"))
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

    title = BlockQuote(_("⚙️ Settings:"))
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
        title = BlockQuote(_("⚙️ Settings:"))
        await query.message.edit_text(
            f"{title.as_html()}\n\n",
            reply_markup=get_general_settings_keyboard(state_data),
            inline_message_id=query.inline_message_id,
        )

    if callback_data.action == "show_posting_tasks":
        time_frames = state_data.get("time_frames")
        jobs, stop_jobs = get_all_jobs_by_user_id(time_frames, user.id)
        await query.message.edit_text(
            _(
                "📋 <b>Post publishing tasks:</b>\n\n<b>Total tasks: <code>{count}</code></b>"
            ).format(count=len(jobs)),
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
        job = remove_job_by_id(jobs[job_index].id)
        remove_job_by_id(stop_jobs[job_index].id)
        if job:
            # remove element from jobs list
            job_id = jobs[job_index].id
            jobs.pop(job_index)
            await query.message.edit_text(
                _("✅ Post publishing task <code>{job_id}</code> deleted.").format(
                    job_id=job_id
                ),
                reply_markup=get_post_jobs_keyboard(state_data, jobs),
                inline_message_id=query.inline_message_id,
            )
        else:
            await query.message.edit_text(
                _("⚠️ Post publishing task <code>{job_id}</code> not found.").format(
                    job_id=job_id
                ),
                reply_markup=get_post_jobs_keyboard(state_data, jobs),
                inline_message_id=query.inline_message_id,
            )

    if callback_data.action == "delete_multiposting_timeframe":
        user_repository.delete_multiposting_timeframe(user)
        remove_job_by_time_interval(state_data.get("time_frames"), user.id)
        await state.update_data(time_frames=None)
        state_data = await state.get_data()
        await query.message.edit_text(
            _(
                "⏰ Multiposting schedule deleted. Now posts will be published immediately after creation."
            ),
            reply_markup=get_multiposting_keyboard(state_data),
            inline_message_id=query.inline_message_id,
        )

    if (
        callback_data.action == "show_multiposting_timeframe"
        or callback_data.action == "delete_multiposting_timeframe"
    ):
        await state.set_state(PostForm.time_frames)
        time_frames = state_data.get("time_frames")
        await query.message.edit_text(
            _(
                """
<b>🗓 Schedule</b>\n
Here you can set a daily schedule for posts in multiposting mode, so you can plan publications in several channels with one click.\n
To set a schedule, send the post times as a list in any convenient format.\n
🕒 <b>Time-based publishing</b> (send time in any of the formats):\n
{time_examples}\n🕒 <b>Interval-based publishing:</b>\n
{interval_examples}\n⚠️ <b>IMPORTANT!</b> The minimum auto-repeat/loop interval is 15m (minutes)\n{current_schedule}
{schedule_block}
"""
            ).format(
                time_examples=BlockQuote(
                    "12:00 - Will be published at 12:00\n12 00 - Will be published at 12:00\n1200 - Will be published at 12:00\n12 00, 15 00, 18 00 - Will be published at 12:00, 15:00, 18:00"
                ).as_html(),
                interval_examples=BlockQuote(
                    "30m - Will be published every 30 minutes\n12h - Will be published every 12 hours\n1h 30m - Will be published every 1 hour 30 minutes"
                ).as_html(),
                current_schedule=(
                    "⏰ <b>Current publishing schedule:</b>\n" if time_frames else ""
                ),
                schedule_block=(
                    BlockQuote("\n".join(time_frames)).as_html() if time_frames else ""
                ),
            ),
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
            text=_("⚠️ Please enter at least one time."),
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
                text=_("⚠️ Time format error, please try again."),
                reply_to_message_id=message.message_id,
                reply_markup=get_multiposting_keyboard(state_data),
            )
            return

    user_repository.create_multiposting(user, time_frames_list)
    await state.update_data(time_frames=time_frames_list)
    state_data = await state.get_data()
    await message.answer(
        _(
            """
        ⏰ <b>Current publishing schedule:</b>
        {schedule}
        """
        ).format(schedule=BlockQuote("\n".join(time_frames_list)).as_html()),
        reply_to_message_id=message.message_id,
        reply_markup=get_multiposting_keyboard(state_data),
    )
