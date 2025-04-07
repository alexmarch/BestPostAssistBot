from typing import Any

from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section

from bot import bot, message_ids_list
from keyboard.keyboard import (
    ChannelData,
    PostButtonData,
    get_add_media_keyboard,
    get_back_to_post_keyboard,
    get_channel_list_keyboard,
    get_chat_channel_keyboard,
    get_confirm_post_keyboard,
    get_post_publish_settings_keyboard,
    get_settings_post_keyboard,
)
from models import User
from repositories import post_repository, user_repository
from states.post import PostForm
from utils.media import remove_media_file

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
    text = state_data.get("text")
    media_file_position = state_data.get("media_file_position")
    media_file_path = state_data.get("media_file_path")
    media_file_name = state_data.get("media_file_name")
    media_file_type = state_data.get("media_file_type")

    await clear_message_ids(message)  # Clear previous messages

    # Remove last message

    if media_file_type == "photo":
        photo = FSInputFile(path=media_file_path, filename=media_file_name)
        if media_file_position == "top_preview":
            await message.answer_photo(
                photo=photo,
                caption=text,
                reply_markup=get_settings_post_keyboard(state_data),
            )
        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text)
            msg2 = await message.answer_photo(
                photo=photo,
                reply_markup=get_settings_post_keyboard(state_data),
            )
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)

    elif media_file_type == "video":
        video = FSInputFile(path=media_file_path, filename=media_file_name)
        if media_file_position == "top_preview":
            await message.answer_video(
                video=video,
                caption=text,
                reply_markup=get_settings_post_keyboard(state_data),
            )
        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text)
            msg2 = await message.answer_video(
                video, reply_markup=get_settings_post_keyboard(state_data)
            )
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)
    else:
        await message.answer(
            text,
            reply_markup=get_settings_post_keyboard(state_data),
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


@post_router.message(Command("create_post"))
@post_router.message(F.text == "Создать пост")
async def create_post_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик создания поста
    """
    await state.set_state(PostForm.text)
    msg1 = await message.answer("⬇️ Создайте или перешлите нужный вам пост")
    message_ids_list.append(msg1.message_id)


@post_router.message(PostForm.text)
async def create_post_text_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик добавленя текста поста
    """
    user = user_repository.find_by_chat_id(message.from_user.id)
    channels = user_repository.get_all_user_channels(user)
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

    if state_data.get("media_file_path"):
        remove_media_file(state_data.get("media_file_path"))

    await state.update_data(
        text=message.text,
        sound="on",
        comments="on",
        pin="off",
        signature="off",
        chat_channel_list=chat_channel,
        is_confirm=True,
        media_file_path=None,
        media_file_name=None,
        media_file_position=None,
        media_file_type=None,
    )

    await state.set_state(PostForm.chat_channel_list)
    state_data = await state.get_data()
    await answer_with_post(
        message=message,
        state_data=state_data,
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


@post_router.callback_query(PostButtonData.filter(F.type == "post_settings_action"))
async def set_post_settings_action_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostButtonData
) -> None:
    """
    Обработчик действий с постами
    """
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

    # Подтверждение создания поста
    if callback_data.action == "confirm_create_post":
        state_data = await state.get_data()
        user = user_repository.find_by_chat_id(query.from_user.id)

        post = post_repository.create_post(user, state_data)
        if post:
            await clear_message_ids(query.message)
            await query.answer(text="✅ Пост успешно опубликован!", show_alert=True)
            await state.clear()
            result = await post_repository.send_post(post.id)
            if result:
                channels = ""
                for channel in result["channels"]:
                    channels += f"{html.blockquote(html.code(channel.title)) (channel['type'])}\n"
                await query.message.answer(
                    text=f"✅ Отправка завершена!\n\n📨 Доставлено {result['sended_channels']}/{result['total_channels']}:\n\n{channels}\n\n",
                    reply_markup=get_back_to_post_keyboard(state_data),
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
    print(chat_info)
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
