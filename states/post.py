from aiogram.fsm.state import State, StatesGroup


class PostForm(StatesGroup):
    text = State()
    upload_media = State()
    media_file_position = State()
    media_file_path = State()
    media_file_name = State()
    media_file_type = State()
    recipient_report_chat_id = State()
    recipient_post_chat_id = State()
    auto_remove_datetime = State(state="2d")
    admin_message = State()
    settings_time_frames = State()
    time_frames = State()
    active_state = "on"
    time_frames_active = "on"
    date_frames = State()
    stop_schedule_date_frames = State()
    auto_repeat = State()
    auto_repeat_dates = State()
    date_frames_confirm = State()
    buttons = State()
    reactions = State()
    sound = State()
    comments = State()
    settings = State()
    pin = State()
    signature = State()
    is_confirm = State()
    chat_channel_list = State()
    edit_post = State()
    next = State()
