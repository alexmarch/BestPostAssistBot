import os

from aiogram import F, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.utils.formatting import BlockQuote, as_list, as_marked_section

from bot import bot
from keyboard.keyboard import PostMediaPositionData, get_back_to_post_keyboard
from models import User
from repositories import user_repo
from states.post import PostForm

from . import media_router, post_router

media_path = "./media"


@media_router.callback_query(PostMediaPositionData.filter(F.type == "media"))
async def set_post_media_handler(
    query: CallbackQuery, state: FSMContext, callback_data: PostMediaPositionData
) -> None:
    """
    Обработчик выбора позиции медиа
    """
    state_data = await state.get_data()
    await state.update_data(media_position=callback_data.media_position)
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

    state_data = await state.get_state()
    if state_data != PostForm.upload_media:
        return

    file_id = message.photo[-1].file_id
    file_size = message.photo[-1].file_size

    if file_size > 5 * 1024 * 1024:
        await message.answer(
            "⚠️ Размер файла превышает 5 МБ. Пожалуйста, выберите другой файл.",
            show_alert=True,
        )
        return

    user_id = message.from_user.id
    user = user_repo.find_by_chat_id(user_id)

    user_media_path = f"{media_path}/{user.id}/photos"

    if not os.path.exists(user_media_path):
        os.makedirs(user_media_path)

    # Сохраняем файл
    file = await bot.get_file(file_id)
    file_path = file.file_path

    if file_path:
        file_name = file_path.split("/")[-1]
        user_media_file_path = f"{user_media_path}/{file_name}"

        await state.update_data(media_file_path=user_media_file_path)
        await bot.download_file(file_path, user_media_file_path)
