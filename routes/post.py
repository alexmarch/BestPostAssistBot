from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section

from keyboard.keyboard import (
    ChannelData,
    PostButtonData,
    get_add_media_keyboard,
    get_back_to_post_keyboard,
    get_channel_list_keyboard,
    get_chat_channel_keyboard,
    get_post_publish_settings_keyboard,
    get_settings_post_keyboard,
)
from models import User
from repositories import user_repo
from states.post import PostForm

from . import post_router


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


@post_router.message(Command("create_post"))
@post_router.message(F.text == "Создать пост")
async def create_post_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик создания поста
    """
    await state.set_state(PostForm.text)
    await message.answer("⬇️ Создайте или перешлите нужный вам пост")


@post_router.message(PostForm.text)
async def create_post_text_handler(message: Message, state: FSMContext) -> None:
    user = user_repo.find_by_chat_id(message.from_user.id)
    channels = user_repo.get_all_user_channels(user)
    chat_channel = [
        {
            "id": channel.id,
            "title": channel.title,
            "chat_id": channel.chat_id,
            "checked": "off",
        }
        for channel in channels
    ]
    await state.update_data(text=message.text)
    await state.update_data(sound="on")
    await state.update_data(comments="on")
    await state.update_data(pin="off")
    await state.update_data(signature="off")
    await state.update_data(chat_channel_list=chat_channel)
    await state.update_data(is_confirm=False)
    await state.set_state(PostForm.text)
    state_data = await state.get_data()
    await message.answer(
        f"{message.text}", reply_markup=get_settings_post_keyboard(state_data)
    )


# @post_router.message(PostForm.chat_channel_list)
# async def create_post_chat_channel_list_handler(message: Message, state: FSMContext) -> None:
#     # reply_markup = get_chat_channel_keyboard(channels)
#     await message.answer("🏷 Выберите каналы/чаты для публикации")


@post_router.callback_query(ChannelData.filter(F.action == "check"))
async def channel_check_action_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    state_data = await state.get_data()
    channel_list = state_data["chat_channel_list"]
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


@post_router.callback_query(PostButtonData.filter(F.type == "post_settings_action"))
async def set_post_settings_action_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    """
    Обработчик действий с постами
    """
    if callback_data.action == "add_media":
        state_data = await state.get_data()
        await query.message.edit_text(
            text="Положение медиа (🔼 Вверх с превью | 🆙 Вверх без превью | 🔽 Вниз с превью)",
            inline_message_id=query.inline_message_id,
            reply_markup=get_add_media_keyboard(state_data),
        )

    if callback_data.action == "change_text":
        state_data = await state.get_data()
        await state.set_state(PostForm.text)
        reply_markup = get_back_to_post_keyboard(state_data)
        await query.message.edit_text(
            text="⬇️ Отправьте новый текст поста",
            inline_message_id=query.inline_message_id,
            reply_markup=reply_markup,
        )

    if callback_data.action == "add_chat_channel":
        state_data = await state.get_data()
        reply_markup = get_channel_list_keyboard(state_data)
        await query.message.edit_text(
            text="🏷 Выберите каналы/чаты для публикации",
            inline_message_id=query.inline_message_id,
            reply_markup=reply_markup,
        )

    if callback_data.action == "confirm":
        state_data = await state.get_data()
        await state.update_data(is_confirm=True)
        await state.set_state(PostForm.is_confirm)
        await query.message.edit_text(
            text=f"{state_data['text']}",
            inline_message_id=query.inline_message_id,
            reply_markup=get_settings_post_keyboard(state_data),
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
        print(is_confirm)
        if not is_confirm:
            # Сообщение об ошибке
            await query.answer(
                text=f"⚠️ Подтвердите выбор каналов/чатов!", show_alert=True
            )
        else:
            reply_markup = get_post_publish_settings_keyboard(state_data)
            await query.message.edit_text(
                text=f"➡️ Меню настроек публикаций для поста",
                inline_message_id=query.inline_message_id,
                reply_markup=reply_markup,
            )

    if callback_data.action == "back":
        await state.set_state(PostForm.text)
        state_data = await state.get_data()
        await query.message.edit_text(
            text=f"{state_data['text']}",
            inline_message_id=query.inline_message_id,
            reply_markup=get_settings_post_keyboard(state_data),
        )


@post_router.callback_query(PostButtonData.filter(F.type == "post_settings"))
async def set_post_settings_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    if callback_data.action == "sound":
        await state.update_data(
            sound=("on" if await state.get_value("sound") != "on" else "off")
        )
    elif callback_data.action == "comments":
        await state.update_data(
            comments="on" if await state.get_value("comments") != "on" else "off"
        )
    elif callback_data.action == "pin":
        await state.update_data(
            pin="on" if await state.get_value("pin") != "on" else "off"
        )
    elif callback_data.action == "signature":
        await state.update_data(
            signature="on" if await state.get_value("signature") != "on " else "off"
        )

    state_data = await state.get_data()
    reply_markup = get_settings_post_keyboard(state_data)

    try:
        if query.message.reply_markup != reply_markup:
            await query.message.edit_reply_markup(
                inline_message_id=query.inline_message_id, reply_markup=reply_markup
            )
    except:
        pass


# @post_router.message(F.chat)
# async def handle_request_chat(message: Message) -> None:
#     chat_info = message.chat_shared
#     user = user_repo.find_by_chat_id(message.from_user.id)
#     if user and chat_info:
#         if chat_info.request_id == 1 or chat_info.request_id == 2:
#             type = "chat"
#             channel = user_repo.get_user_channel_by_chat_id(
#                 user, str(chat_info.chat_id)
#             )
#             if channel:
#                 await message.answer(
#                     f"Канал/чат уже добавлен:\n\n{html.blockquote(channel.title)}"
#                 )
#                 return
#             user_repo.add_channel(user, str(chat_info.chat_id), chat_info.title, type)
#             await message.answer(
#                 f"Вы выбрали канал:\n\n{html.blockquote(chat_info.title)}"
#             )


async def send_message_handler() -> None:
    """
    Handler will send message for chat
    """
    try:
        #  bot = session.execute(select(Bot).limit(1)).scalar_one()
        #  media_type = bot.media_type
        #  if media_type == "image":
        #     media_path = f"media/{bot.file_media}"  # Replace with actual image path
        #     media = FSInputFile(media_path)
        #     for chat_id in bot.chats:
        #       await bot.send_photo(chat_id, media, caption=bot.message)

        #  elif media_type == "video":
        #     media_path = f"media/{bot.file_media}"  # Replace with actual video path
        #     media = FSInputFile(media_path)
        #     for chat_id in bot.chats:
        #       await bot.send_video(chat_id, media, caption=bot.message)

        #  for chat_id in bot.chats:
        #    bot.send_message(chat_id, bot.message)
        pass
    except:
        print("Send message error.")


# @base_router.chat_member()
# async def remove_pinned_message(event: ChatMemberUpdated):
#   if event.chat.id == CHANNEL_ID:
#     try:
#       # Получаем последнее закрепленное сообщение
#       pinned_msg = await bot.get_chat(CHANNEL_ID)
#       if pinned_msg.pinned_message:
#         await bot.unpin_chat_message(CHANNEL_ID)
#     except Exception as e:
#       print(e)
