from aiogram.fsm.state import State, StatesGroup


class PostForm(StatesGroup):
    text = State()
    upload_media = State()
    media_file_position = State()
    media_file_path = State()
    media_file_name = State()
    media_file_type = State()
    time_frames = State()
    date_frames = State()
    buttons = State()
    reactions = State()
    sound = State()
    comments = State()
    pin = State()
    signature = State()
    is_confirm = State()
    chat_channel_list = State()
    next = State()
