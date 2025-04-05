from aiogram.fsm.state import State, StatesGroup


class PostForm(StatesGroup):
    text = State()
    upload_media = State()
    media_position = State()
    media_file_path = State()
    buttons = State()
    reactions = State()
    sound = State()
    comments = State()
    pin = State()
    signature = State()
    is_confirm = State()
    chat_channel_list = State()
    next = State()
