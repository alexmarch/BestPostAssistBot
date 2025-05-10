from typing import Any

from aiogram import F, html
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram_calendar import (
  DialogCalendar,
  DialogCalendarCallback,
  SimpleCalendar,
  SimpleCalendarCallback,
  get_user_locale,
)

from bot import bot, message_ids_list
from keyboard.keyboard import (
  ChannelData,
  EmojiButtonData,
  PostButtonData,
  get_add_media_keyboard,
  get_back_to_post_keyboard,
  get_channel_list_keyboard,
  get_chat_channel_keyboard,
  get_confirm_calendar_keyboard,
  get_confirm_post_keyboard,
  get_created_post_keyboard,
  get_post_buttons_keyboard,
  get_post_publish_settings_keyboard,
  get_reaction_buttons_keyboard,
  get_remove_post_interval_keyboard,
  get_settings_post_keyboard,
)
from repositories import post_repository, user_repository
from states.post import PostForm
from utils.media import remove_media_file
from utils.scheduler import create_jod, create_remove_post_jod

from . import post_router


async def clear_message_ids(message: Message) -> None:
    """
    Удаляет все сообщения из списка message_ids_list
    """
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)

    for msg_id in message_ids_list:
        try:
            await bot.delete_message(chat_id=message.chat.id, message_id=msg_id)
        except Exception as e:
            pass

    message_ids_list.clear()  # Clear the list of message IDs


async def answer_with_post(message: Message, state_data: dict[str, Any]) -> None:
    """
    Отправляет ответ с постом и клавиатурой настроек
    """
    ikb = InlineKeyboardBuilder()
    text = state_data.get("text")
    media_file_position = state_data.get("media_file_position")
    media_file_path = state_data.get("media_file_path")
    media_file_name = state_data.get("media_file_name")
    media_file_type = state_data.get("media_file_type")
    reactions = state_data.get("reactions")
    buttons = state_data.get("buttons")

    await clear_message_ids(message)  # Clear previous messages

    # Remove last message
    if reactions:
        ikb.attach(
            InlineKeyboardBuilder.from_markup(get_reaction_buttons_keyboard(state_data))
        )

    if buttons:
        ikb.attach(
            InlineKeyboardBuilder.from_markup(get_post_buttons_keyboard(state_data))
        )

    ikb.attach(
        InlineKeyboardBuilder.from_markup(get_settings_post_keyboard(state_data))
    )

    if media_file_type == "photo":
        photo = FSInputFile(path=media_file_path, filename=media_file_name)
        if media_file_position == "top_preview":
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=ikb.as_markup(),
            )
        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text)
            msg2 = await message.answer_photo(
                photo=photo,
                reply_markup=ikb.as_markup(),
            )
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)

    elif media_file_type == "video":
        video = FSInputFile(path=media_file_path, filename=media_file_name)
        if media_file_position == "top_preview":
            await message.answer_video(
                video=video,
                caption=text,
                reply_markup=ikb.as_markup(),
            )
        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text)
            msg2 = await message.answer_video(video, reply_markup=ikb.as_markup())
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)
    else:
        await message.answer(
            text,
            reply_markup=ikb.as_markup(),
        )


@post_router.message(Command("add_channel"))
@post_router.message(F.text == "Добавить канал/чат")
async def add_channel_handler(message: Message) -> None:
    content = BlockQuote(
        as_list(
            as_marked_section("", "Отправка сообщений", marker="✅ "),
            as_marked_section("", "Удаление сообщений", marker="✅ "),
            as_marked_section("", "Изменение сообщений", marker="✅ "),
            as_marked_section("", "Пригласительные ссылки", marker="✅ "),
        )
    )
    await message.answer(
        f"Для подключения бота назначьте его Администратором в нужный вам канал/чат, выдав следующие права:\n\n{content.as_html()}\n\nЗатем перешлите пост из вашего канала/чата прямо сюда и можно создавать посты ✈️",
        reply_markup=get_chat_channel_keyboard(),
    )


@post_router.message(Command("edit_post"))
@post_router.message(F.text == "Изменить пост")
async def edit_post_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик изменения поста
    """
    state_data = await state.get_data()
    await state.set_state(PostForm.edit_post)
    await message.answer(
        text="⬇️ Отправьте сюда пост, который хотите изменить",
        reply_markup=get_back_to_post_keyboard(state_data),
    )


@post_router.message(PostForm.edit_post)
async def edit_post_text_handler(message: Message, state: FSMContext) -> None:
    state_data = await state.get_data()
    if message.forward_from_chat and message.forward_from_message_id:
        user = user_repository.find_by_chat_id(message.from_user.id)
        forward_from_chat_id = message.forward_from_chat.id
        forward_from_message_id = message.forward_from_message_id
        post = post_repository.get_post_by_forward_message(
            user.id, str(forward_from_chat_id), forward_from_message_id
        )
        if not post:
            await message.answer(
                text="⚠️ Пост не найден. Отправьте корректный пост.",
                reply_markup=get_back_to_post_keyboard(state_data),
            )
            return

        await state.update_data(
            {
                "text": post.text,
                "post_id": post.id,
                "channel_id": forward_from_chat_id,
                "sound": "on" if post.sound else "off",
                "comments": "on" if post.comments else "off",
                "pin": "on" if post.pin else "off",
                "forward_from_message_id": forward_from_message_id,
                "signature": "on" if post.signature else "off",
                # "chat_channel_list": post.chat_channel_list,
                "is_confirm": True,
                "media_file_path": post.post_media_file.media_file_path,
                "media_file_name": post.post_media_file.media_file_name,
                "media_file_position": post.post_media_file.media_file_position,
                "media_file_type": post.post_media_file.media_file_type,
            }
        )
        state_data = await state.get_data()
        await answer_with_post(
            message=message,
            state_data=state_data,
        )


@post_router.message(Command("create_post"))
@post_router.message(F.text == "Создать пост")
async def create_post_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик создания поста
    """
    await state.clear()
    await state.set_state(PostForm.text)
    msg1 = await message.answer("⬇️ Создайте или перешлите нужный вам пост")
    message_ids_list.append(msg1.message_id)


@post_router.message(
    PostForm.text,
    lambda msg: msg.text.lower()
    not in [
        "настройки",
        "добавить канал/чат",
        "мой профиль",
        "шаблоны",
        "контент-план",
        "изменить пост",
    ],
)
async def create_post_text_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик добавленя текста поста
    """
    user = user_repository.find_by_chat_id(message.from_user.id)
    channels = user_repository.get_all_user_channels(user)
    multiposting = user_repository.get_multiposting_by_user_id(user.id)
    time_frames = None
    time_frames_active = "on"
    if multiposting:
        time_frames = multiposting.time_frames.split("|")
        time_frames_active = "on" if multiposting.active else "off"

    chat_channel = [
        {
            "id": channel.id,
            "title": channel.title,
            "chat_id": channel.chat_id,
            "checked": "on",
        }
        for channel in channels
    ]

    state_data = await state.get_data()

    # if state_data.get("media_file_path"):
    #     remove_media_file(state_data.get("media_file_path"))

    await state.update_data(
        text=message.text,
        sound="on",
        comments="on",
        pin="off",
        signature="off",
        chat_channel_list=chat_channel,
        is_confirm=True,
        # media_file_path=None,
        # media_file_name=None,
        # media_file_position=None,
        # media_file_type=None,
        time_frames=time_frames,
        time_frames_active=time_frames_active,
    )

    await state.set_state(PostForm.chat_channel_list)
    state_data = await state.get_data()
    await answer_with_post(
        message=message,
        state_data=state_data,
    )


@post_router.message(PostForm.recipient_report_chat_id)
async def create_post_recipient_report_chat_id_handler(
    message: Message, state: FSMContext
) -> None:
    """
    Обработчик добавления ID чата для отчета
    """
    state_data = await state.get_data()

    if message.text.isdigit():
        user = user_repository.find_by_chat_id(message.text)
    else:
        user = user_repository.find_by_username(message.text)

    if not user:
        await message.answer(
            text="⚠️ Пользователь не найден. Введите корректный ID/юзернейм клиента",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        return

    await state.update_data(
        {
            "recipient_report_chat_id": user.chat_id,
        }
    )

    await message.answer(
        text="✅ Клиент успешно добавлен",
        reply_markup=get_back_to_post_keyboard(state_data),
    )


@post_router.message(PostForm.recipient_post_chat_id)
async def create_post_recipient_post_chat_id_handler(
    message: Message, state: FSMContext
) -> None:
    """
    Обработчик добавления ID чата для копии поста
    """
    state_data = await state.get_data()

    if message.text.isdigit():
        user = user_repository.find_by_chat_id(message.text)
    else:
        user = user_repository.find_by_username(message.text)

    if not user:
        await message.answer(
            text="⚠️ Пользователь не найден. Введите корректный ID/юзернейм клиента",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        return

    await state.update_data(
        {
            "recipient_post_chat_id": user.chat_id,
        }
    )

    await message.answer(
        text="✅ Клиент успешно добавлен",
        reply_markup=get_back_to_post_keyboard(state_data),
    )


@post_router.callback_query(ChannelData.filter(F.action == "check"))
async def channel_check_action_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    state_data = await state.get_data()
    channel_list = state_data.get("chat_channel_list")

    if not channel_list:
        await query.answer(text="⚠️ Сначала выберите каналы/чаты!", show_alert=True)
        return

    # Получаем список каналов/чатов
    channels = list(filter(lambda c: c["id"] == callback_data.channel_id, channel_list))

    for ch in channels:
        ch["checked"] = "on" if ch["checked"] == "off" else "off"

    channel_selected = list(filter(lambda c: c["checked"] == "on", channel_list))

    if not len(channel_selected):
        await state.update_data(is_confirm=False)

    await state.update_data(chat_channel_list=channel_list)
    state_data = await state.get_data()
    reply_markup = get_channel_list_keyboard(state_data)

    await query.message.edit_reply_markup(
        inline_message_id=query.inline_message_id, reply_markup=reply_markup
    )


# dialog calendar usage
@post_router.callback_query(DialogCalendarCallback.filter())
async def process_dialog_calendar(
    callback_query: CallbackQuery, state: FSMContext, callback_data: CallbackData
):
    state_data = await state.get_data()
    selected, date = await DialogCalendar(
        locale=await get_user_locale(callback_query.from_user)
    ).process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(
            f'You selected {date.strftime("%d/%m/%Y")}',
            reply_markup=get_confirm_calendar_keyboard(state_data),
        )


@post_router.callback_query(SimpleCalendarCallback.filter())
async def process_simple_calendar(
    callback_query: CallbackQuery, state: FSMContext, callback_data: CallbackData
):
    state_data = await state.get_data()
    simplecalendar = SimpleCalendar(
        locale=await get_user_locale(callback_query.from_user)
    )

    # calendar.set_dates_range(datetime(2022, 1, 1), datetime(2025, 12, 31))
    selected, date = await simplecalendar.process_selection(
        callback_query, callback_data
    )

    if selected:
        await state.update_data(
            {
                "date_frames": date.strftime("%d/%m/%Y"),
            }
        )
        state_data = await state.get_data()
        builder = InlineKeyboardBuilder()
        builder.attach(
            InlineKeyboardBuilder.from_markup(
                await simplecalendar.start_calendar(
                    year=date.year,
                    month=date.month,
                )
            )
        )
        builder.attach(
            InlineKeyboardBuilder.from_markup(get_confirm_calendar_keyboard(state_data))
        )
        await callback_query.message.edit_text(
            f'<b>Дата:</b>\n {BlockQuote(date.strftime("%d/%m/%Y")).as_html()}',
            inline_message_id=callback_query.inline_message_id,
            reply_markup=builder.as_markup(),
        )


@post_router.callback_query(PostButtonData.filter(F.type == "post_settings_action"))
async def set_post_settings_action_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    """
    Обработчик действий с постами
    """
    user = user_repository.find_by_chat_id(query.from_user.id)
    state_data = await state.get_data()
    simplecalendar = SimpleCalendar(locale="uk_UA")

    if callback_data.action == "publish_post":
        await clear_message_ids(query.message)
        # оправить сообщение на подтверждение
        state_data = await state.get_data()
        await query.message.answer(
            text="✅ Подтвердите отправку поста.",
            reply_markup=get_confirm_post_keyboard(state_data),
        )

    if callback_data.action == "ai_integration":
        await query.answer(
            text="🌟 Доступно только в платной подписке!", show_alert=True
        )

    if callback_data.action == "crm_integration":
        await query.answer(
            text="🌟 Доступно только в платной подписке!", show_alert=True
        )

    if callback_data.action == "show_send_report":
        info_message = BlockQuote(
            "ℹ️ Чтобы отчёт был доставлен, ваш клиент должен запустить бота."
        )
        message = f"""⬆️ <b>Отчёт клиенту</b>\n\n
Отправьте сюда юзернейм клиента, если его нет то отправьте его ID или перешлите сообщение от имени клиента.\n\n
{info_message.as_html()}\n\n
"""
        await query.message.edit_text(
            text=message,
            inline_message_id=query.inline_message_id,
            reply_markup=get_back_to_post_keyboard(state_data),
        )

        await state.set_state(PostForm.recipient_report_chat_id)

    if callback_data.action == "show_send_copy_post":
        info_message = BlockQuote(
            "ℹ️ Чтобы копия поста была доставлена, ваш клиент должен запустить бота."
        )
        message = f"""⬆️ <b>Копия поста</b>\n\n
Отправьте сюда юзернейм клиента, если его нет то отправьте его ID или перешлите сообщение от имени клиента.\n\n
{info_message.as_html()}\n\n
"""
        await query.message.edit_text(
            text=message,
            inline_message_id=query.inline_message_id,
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        await state.set_state(PostForm.recipient_post_chat_id)

    if callback_data.action == "confirm_create_post":
        state_data = await state.get_data()
        post = post_repository.create_post(user, state_data)

        if post:
            await clear_message_ids(query.message)
            await query.answer(text="✅ Пост успешно опубликован!", show_alert=True)
            time_frames = state_data.get("time_frames")
            time_frames_active = state_data.get("time_frames_active")
            date_frames_confirm = state_data.get("date_frames_confirm")
            if not time_frames or time_frames_active == "off":
                result = await post_repository.send_post(
                    post.id, True, create_remove_post_jod
                )
                if result:
                    channels = ""
                    for channel in result["channels"]:
                        channels += f"{html.blockquote(html.code(channel.title + '/' + channel.type))}\n"
                    await query.message.answer(
                        text=f"✅ <b>Отправка завершена.</b>\n\n📨 Доставлено {result['sended_channels']}/{result['total_channels']}:\n\n{channels}\n\n",
                        reply_markup=get_back_to_post_keyboard(state_data),
                    )
            else:
                # create job schedule with time_frames for sending post
                create_jod(post, time_frames)

                multiposting = BlockQuote("\n".join(time_frames)).as_html()

                if date_frames_confirm:
                    multiposting = f"📅 Дата публикации:\n {BlockQuote(date_frames_confirm).as_html()}\n {multiposting}\n"

                await query.message.answer(
                    text=f"✅ <b>Публикация завершена.</b>\n\n {multiposting}\n\n Вы получите уведомление о публикации поста.\n\n",
                    reply_markup=get_back_to_post_keyboard(state_data),
                )

    if callback_data.action == "active_multiposting_timeframe":
        multiposting = user_repository.get_multiposting_by_user_id(user.id)
        if multiposting:
            active_state = "off" if multiposting.active else "on"
            user_repository.update_multiposting_active_timeframe(
                user,
                active_state,
            )
            await state.update_data(time_frames_active=active_state)
            state_data = await state.get_data()
            await query.message.edit_reply_markup(
                inline_message_id=query.inline_message_id,
                reply_markup=get_confirm_post_keyboard(state_data),
            )

    if callback_data.action == "add_media":
        state_data = await state.get_data()
        await clear_message_ids(query.message)
        await query.message.answer(
            text="Положение медиа (🔼 Вверх с превью | 🆙 Вверх без превью | 🔽 Вниз с превью)",
            reply_markup=get_add_media_keyboard(state_data),
        )

    if callback_data.action == "remove_media":

        state_data = await state.get_data()

        if state_data.get("media_file_path"):
            remove_media_file(state_data.get("media_file_path"))
            await state.update_data(
                {
                    "media_file_path": None,
                    "media_file_name": None,
                    "media_file_position": None,
                    "media_file_type": None,
                }
            )
            await query.answer(text=f"✅ Медиафайл удален!", show_alert=True)

        state_data = await state.get_data()
        await answer_with_post(
            message=query.message,
            state_data=state_data,
        )

    if callback_data.action == "remove_reactions":
        state_data = await state.get_data()
        await state.update_data(reactions=None)
        state_data = await state.get_data()
        await answer_with_post(
            message=query.message,
            state_data=state_data,
        )

    if callback_data.action == "remove_buttons":
        state_data = await state.get_data()
        await state.update_data(buttons=None)
        state_data = await state.get_data()
        await answer_with_post(
            message=query.message,
            state_data=state_data,
        )

    if callback_data.action == "change_text":
        state_data = await state.get_data()
        await state.set_state(PostForm.text)
        # удаляем старый текст
        await clear_message_ids(query.message)
        msg1 = await query.message.answer(
            text="⬇️ Отправьте новый текст поста",
            inline_message_id=query.inline_message_id,
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        message_ids_list.append(msg1.message_id)

    if callback_data.action == "add_chat_channel":
        state_data = await state.get_data()
        reply_markup = get_channel_list_keyboard(state_data)
        await clear_message_ids(query.message)
        await query.message.answer(
            text="🏷 Выберите каналы/чаты для публикации",
            inline_message_id=query.inline_message_id,
            reply_markup=reply_markup,
        )

    if callback_data.action == "confirm":
        state_data = await state.get_data()
        await state.update_data(is_confirm=True)
        await state.set_state(PostForm.is_confirm)

        await answer_with_post(
            message=query.message,
            state_data=state_data,
        )

    if callback_data.action == "select_all_channels":
        state_data = await state.get_data()
        channels = state_data["chat_channel_list"]

        for ch in channels:
            ch["checked"] = "on"

        await state.update_data(chat_channel_list=channels)
        state_data = await state.get_data()
        reply_markup = get_channel_list_keyboard(state_data)

        await query.message.edit_reply_markup(
            inline_message_id=query.inline_message_id, reply_markup=reply_markup
        )

    if callback_data.action == "next":
        state_data = await state.get_data()
        is_confirm = await state.get_value("is_confirm")

        if not is_confirm:
            # Сообщение об ошибке
            await query.answer(
                text=f"⚠️ Подтвердите выбор каналов/чатов!", show_alert=True
            )
        else:
            await clear_message_ids(query.message)
            await query.message.answer(
                text=f"➡️ Меню настроек публикаций для поста",
                inline_message_id=query.inline_message_id,
                reply_markup=get_post_publish_settings_keyboard(state_data),
            )

    if callback_data.action == "back":
        await state.set_state(PostForm.text)
        state_data = await state.get_data()

        await answer_with_post(
            message=query.message,
            state_data=state_data,
        )

    if callback_data.action == "show_next_post_date_calendar":
        builder = InlineKeyboardBuilder()
        builder.attach(
            InlineKeyboardBuilder.from_markup(await simplecalendar.start_calendar())
        )
        builder.attach(
            InlineKeyboardBuilder.from_markup(get_back_to_post_keyboard(state_data))
        )
        await query.message.edit_text(
            text="📅 Выберите дату в календаре для отложенного поста\n\n",
            inline_message_id=query.inline_message_id,
            reply_markup=builder.as_markup(),
        )

    if callback_data.action == "date_frames_confirm":
        state_data = await state.get_data()
        date_frames = state_data.get("date_frames")
        if date_frames:
            await state.update_data(
                {
                    "date_frames_confirm": date_frames,
                }
            )
            await query.message.edit_text(
                text=f"📅 Дата публикации: {BlockQuote(date_frames).as_html()}",
                inline_message_id=query.inline_message_id,
                reply_markup=get_post_publish_settings_keyboard(state_data),
            )
        else:
            await query.answer(text="⚠️ Выберите дату публикации!", show_alert=True)

    if callback_data.action == "add_buttons":
        state_data = await state.get_data()
        await clear_message_ids(query.message)
        await query.message.answer(
            text=f"⬇️ Отправьте кнопки в формате:\n\n{ BlockQuote("Название - Ссылка").as_html()} {BlockQuote ('Название - Ссылка|Название - Ссылка').as_html()} Результат: 2 кнопки в столбик\n\n",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        await state.set_state(PostForm.buttons)

    if callback_data.action == "add_reactions":
        state_data = await state.get_data()
        await clear_message_ids(query.message)
        await query.message.answer(
            text="⬇️ Отправьте реакции в формате:\n\n❤️/👍/😁/🤔/🤬\nДа/Нет/Не знаю",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        await state.set_state(PostForm.reactions)

    if callback_data.action == "show_remove_time":
        state_data = await state.get_data()
        await query.message.answer(
            text="🗑️ Выберите интервал через сколько пост будет удален",
            reply_markup=get_remove_post_interval_keyboard(state_data),
        )

    if callback_data.action == "remove_post_interval":
        await state.update_data(
            {
                "auto_remove_datetime": callback_data.data,
            }
        )
        state_data = await state.get_data()
        await query.message.edit_reply_markup(
            inline_message_id=query.inline_message_id,
            reply_markup=get_remove_post_interval_keyboard(state_data),
        )


@post_router.callback_query(PostButtonData.filter(F.type == "post_settings"))
async def set_post_settings_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    state_data = await state.get_data()
    if callback_data.action == "sound":
        state_data["sound"] = "on" if state_data.get("sound") != "on" else "off"
    elif callback_data.action == "comments":
        state_data["comments"] = "on" if state_data.get("comments") != "on" else "off"
    elif callback_data.action == "pin":
        state_data["pin"] = "on" if state_data.get("pin") != "on" else "off"
    elif callback_data.action == "signature":
        state_data["signature"] = "on" if state_data.get("signature") != "on" else "off"

    await state.update_data(state_data)
    reply_markup = get_settings_post_keyboard(state_data)

    try:
        if query.message.reply_markup != reply_markup:
            await query.message.edit_reply_markup(
                inline_message_id=query.inline_message_id, reply_markup=reply_markup
            )
    except:
        pass


@post_router.message(F.chat & F.chat_shared)
async def handle_request_chat(message: Message) -> None:
    """
    Обработчик для получения информации о канале/чате
    """
    chat_info = message.chat_shared
    user = user_repository.find_by_chat_id(message.from_user.id)
    if user and chat_info:
        if chat_info.request_id == 1 or chat_info.request_id == 2:
            type = "chat"
            channel = user_repository.get_user_channel_by_chat_id(
                user, str(chat_info.chat_id)
            )
            if channel:
                await message.answer(
                    f"Канал/чат уже добавлен:\n\n{html.blockquote(channel.title)}"
                )
                return
            user_repository.add_channel(
                user, str(chat_info.chat_id), chat_info.title, type
            )
            await message.answer(
                f"Вы выбрали канал:\n\n{html.blockquote(chat_info.title)}"
            )


@post_router.message(PostForm.reactions)
async def create_post_reactions_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик добавления реакций
    """
    state_data = await state.get_data()

    try:
        lines = message.text.split("\n")
        parsed_reactions = []
        for line in lines:
            _reactions = line.split("/")
            for reaction in _reactions:
                parsed_reactions.append(reaction.strip())

        await state.update_data(reactions=parsed_reactions)
        state_data = await state.get_data()
        await answer_with_post(
            message=message,
            state_data=state_data,
        )
    except Exception as e:
        await message.answer(
            text="⚠️ Ошибка при добавлении реакций. Попробуйте еще раз.",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        print(e)


@post_router.message(PostForm.buttons)
async def create_post_buttons_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик добавления кнопок
    """
    state_data = await state.get_data()

    try:
        lines = message.text.split("\n")
        row = 0
        column = 0
        for line in lines:
            _buttons = line.split("|")
            parsed_buttons = []
            column = 0

            if not len(_buttons):
                # try parse single button
                _buttons = message.text.split("-")
                if len(_buttons) == 2:
                    name = _buttons[0].strip()
                    url = _buttons[1].strip()
                    parsed_buttons.append(
                        {"name": name, "url": url, "row": row, "column": column}
                    )

            for button in _buttons:
                parts = button.split("-")
                column += 1
                if len(parts) == 2:
                    name = parts[0].strip()
                    url = parts[1].strip()
                    parsed_buttons.append(
                        {"name": name, "url": url, "row": row, "column": column}
                    )

            row += 1

        await state.update_data(buttons=parsed_buttons)
        state_data = await state.get_data()
        await answer_with_post(
            message=message,
            state_data=state_data,
        )
    except Exception as e:
        await message.answer(
            text="⚠️ Ошибка при добавлении кнопок. Попробуйте еще раз.",
            reply_markup=get_back_to_post_keyboard(state_data),
        )
        print(e)


@post_router.callback_query(EmojiButtonData.filter())
async def emoji_button_handler(
    query: CallbackQuery, state: FSMContext, callback_data: EmojiButtonData
) -> None:
    """
    Обработчик добавления эмодзи
    """
    try:
        post_repository.update_post_reaction_by_user_id(
            callback_data.post_id,
            callback_data.id,
            query.from_user.id,
        )
        post = post_repository.get_by_id(callback_data.post_id)
        print(post)
        await query.message.edit_reply_markup(
            inline_message_id=query.inline_message_id,
            reply_markup=get_created_post_keyboard(post),
        )
    except Exception as e:
        print(e)
        return
