import os

from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, FSInputFile, Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot import bot, message_ids_list
from keyboard.keyboard import (
    PostMediaPositionData,
    get_back_to_post_keyboard,
    get_post_buttons_keyboard,
    get_reaction_buttons_keyboard,
    get_settings_post_keyboard,
)
from models import User
from repositories import user_repository
from states.post import PostForm

from . import media_router

media_path = "./media"


@media_router.callback_query(PostMediaPositionData.filter(F.type == "media"))
async def set_post_media_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostMediaPositionData
) -> None:
    """
    Обработчик выбора позиции медиа
    """
    state_data = await state.get_data()
    await state.update_data(media_file_position=callback_data.media_position)
    await state.set_state(PostForm.upload_media)
    await query.message.edit_text(
        text="⬇️ Отправьте медиафайл",
        inline_message_id=query.inline_message_id,
        reply_markup=get_back_to_post_keyboard(state_data),
    )


@media_router.message(F.photo)
async def set_post_media_photo_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик загрузки медиафайла
    """
    ikb = InlineKeyboardBuilder()
    state_data = await state.get_state()

    data = await state.get_data()
    reactions = data.get("reactions")
    buttons = data.get("buttons")

    if state_data != PostForm.upload_media:
        return

    file_id = message.photo[-1].file_id
    file_size = message.photo[-1].file_size

    print("File ID", file_id, message.photo[-1].file_unique_id)

    if file_size > 5 * 1024 * 1024:
        await message.answer(
            "⚠️ Размер файла превышает 5 МБ. Пожалуйста, выберите другой файл.",
            show_alert=True,
        )
        return

    user_id = message.from_user.id
    user = user_repository.find_by_chat_id(user_id)

    user_media_path = f"{media_path}/{user.id}/photos"

    if not os.path.exists(user_media_path):
        os.makedirs(user_media_path)

    # Сохраняем файл
    file = await bot.get_file(file_id)
    file_path = file.file_path

    if file_path:
        file_name = file_path.split("/")[-1]
        user_media_file_path = f"{user_media_path}/{file_name}"

        await bot.download_file(file_path, user_media_file_path)

        # Обновляем данные поста
        await state.update_data(
            {
                "media_file_path": user_media_file_path,
                "media_file_type": "photo",
                "media_file_name": file_name,
            }
        )

        # Выводим теккущий пост
        data = await state.get_data()
        media_file_position = data.get("media_file_position")
        text = data.get("text")

        if reactions:
            ikb.attach(
                InlineKeyboardBuilder.from_markup(get_reaction_buttons_keyboard(data))
            )

        if buttons:
            ikb.attach(
                InlineKeyboardBuilder.from_markup(get_post_buttons_keyboard(data))
            )

        ikb.attach(InlineKeyboardBuilder.from_markup(get_settings_post_keyboard(data)))

        photo = FSInputFile(
            path=data.get("media_file_path", user_media_file_path),
            filename=data.get("media_file_name", file_name),
        )

        if media_file_position == "top_preview":
            await message.answer_photo(
                photo=photo,
                caption=text,
                parse_mode="HTML",
                reply_markup=ikb.as_markup(),
            )
        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text, parse_mode="HTML")
            msg2 = await message.answer_photo(
                photo,
                parse_mode="HTML",
                reply_markup=ikb.as_markup(),
            )
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)


@media_router.message(F.video)
async def set_post_media_video_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик загрузки медиафайла
    """
    ikb = InlineKeyboardBuilder()
    state_data = await state.get_state()
    data = await state.get_data()
    reactions = data.get("reactions")
    buttons = data.get("buttons")

    if state_data != PostForm.upload_media:
        return

    file_id = message.video[-1].file_id
    file_size = message.video[-1].file_size

    if file_size > 5 * 1024 * 1024:
        await message.answer(
            "⚠️ Размер файла превышает 5 МБ. Пожалуйста, выберите другой файл.",
            show_alert=True,
        )
        return

    user_id = message.from_user.id
    user = user_repository.find_by_chat_id(user_id)

    user_media_path = f"{media_path}/{user.id}/videos"

    if not os.path.exists(user_media_path):
        os.makedirs(user_media_path)

    # Сохраняем файл
    file = await bot.get_file(file_id)
    file_path = file.file_path

    if file_path:
        file_name = file_path.split("/")[-1]
        user_media_file_path = f"{user_media_path}/{file_name}"

        await bot.download_file(file_path, user_media_file_path)

        # Обновляем данные поста
        await state.update_data(
            {
                "media_file_path": user_media_file_path,
                "media_file_type": "video",
                "media_file_name": file_name,
            }
        )

        # Выводим теккущий пост
        data = await state.get_data()
        media_file_position = data.get("media_file_position")
        text = data.get("text")

        if reactions:
            ikb.attach(
                InlineKeyboardBuilder.from_markup(get_reaction_buttons_keyboard(data))
            )

        if buttons:
            ikb.attach(
                InlineKeyboardBuilder.from_markup(get_post_buttons_keyboard(data))
            )

        ikb.attach(InlineKeyboardBuilder.from_markup(get_settings_post_keyboard(data)))

        video = FSInputFile(
            data.get("media_file_path", user_media_file_path),
            filename=data.get("media_file_name", file_name),
        )

        if media_file_position == "top_preview":
            await message.answer_video(
                video=video,
                caption=text,
                parse_mode="HTML",
                reply_markup=ikb.as_markup(),
            )

        elif media_file_position == "bottom_preview":
            msg1 = await message.answer(text, parse_mode="HTML")
            msg2 = await message.answer_video(
                video,
                parse_mode="HTML",
                reply_markup=ikb.as_markup(),
            )
            message_ids_list.append(msg1.message_id)
            message_ids_list.append(msg2.message_id)
