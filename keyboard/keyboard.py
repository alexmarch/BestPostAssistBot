from enum import Enum
from typing import Any, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
  InlineKeyboardButton,
  InlineKeyboardMarkup,
  KeyboardButtonRequestChat,
  ReplyKeyboardMarkup,
)
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from models.Post import Post

CheckState = {"on": "✅", "off": "☑️"}

main_buttons = [
    __("Add channel/chat"),
    __("Create post"),
    __("Settings"),
    __("Edit post"),
    # __("Content plan"),
    # __("Templates"),
    __("My profile"),
]

add_chat_channel_buttons = [
    __("Channel"),
    __("Chat"),
    __("Main menu"),
]

post_inline_buttons = [
    {
        "text": __("📝 Edit text"),
        "action": "change_text",
        "type": "post_settings_action",
    },
    {
        "text": __("📎 Add media"),
        "action": "add_media",
        "type": "post_settings_action",
    },
    {
        "text": __("🎛️ Add buttons"),
        "action": "add_buttons",
        "type": "post_settings_action",
    },
    {
        "text": __("😊 Add reactions"),
        "action": "add_reactions",
        "type": "post_settings_action",
    },
    {"text": __("Sound 🔊"), "action": "sound", "type": "post_settings"},
    {"text": __("Comments 💬"), "action": "comments", "type": "post_settings"},
    {"text": __("Pin 📌"), "action": "pin", "type": "post_settings"},
    {"text": __("Auto-signature ✍️"), "action": "signature", "type": "post_settings"},
    {
        "text": __("‹ Channels/chats"),
        "action": "add_chat_channel",
        "type": "post_settings_action",
    },
    {"text": __("Next ›"), "action": "next", "type": "post_settings_action"},
]


class EmojiButtonData(CallbackData, prefix="emoji"):
    action: str
    post_id: int
    id: int | None = None
    text: str | None = None
    type: str = "emoji_action"


class GeneralSettingsButtonData(CallbackData, prefix="settings"):
    action: str
    type: str = "general_settings"
    data: str | None = None


class PostButtonData(CallbackData, prefix="post"):
    action: str
    type: str = "settings"
    data: str | None = None


class PostMediaPositionData(CallbackData, prefix="post_media"):
    action: str
    media_position: str
    type: str = "media"


class ChannelData(CallbackData, prefix="channel"):
    action: str
    channel_id: int


def get_main_keyboard() -> ReplyKeyboardMarkup:
    rkb = ReplyKeyboardBuilder()
    for btn in main_buttons:
        rkb.button(text=btn)
    rkb.adjust(2)
    return rkb.as_markup()


def get_remove_post_interval_keyboard(
    state_data: dict[str, Any],
) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для удаления поста [[1d, 2d, 3d,], [1w, 2w, 3w,], [1m, 2m, 3m]]
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=(
                    "✅ 2d"
                    if state_data.get("auto_remove_datetime") == "2d"
                    or not state_data.get("auto_remove_datetime")
                    else "2d"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="2d",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 4d" if state_data.get("auto_remove_datetime") == "4d" else "4d"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="4d",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 6d" if state_data.get("auto_remove_datetime") == "6d" else "6d"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="6d",
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=(
                    "✅ 1w" if state_data.get("auto_remove_datetime") == "1w" else "1w"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="1w",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 2w" if state_data.get("auto_remove_datetime") == "2w" else "2w"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="2w",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 3w" if state_data.get("auto_remove_datetime") == "3w" else "3w"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="3w",
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=(
                    "✅ 1m" if state_data.get("auto_remove_datetime") == "1m" else "1m"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="1m",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 2m" if state_data.get("auto_remove_datetime") == "2m" else "2m"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="2m",
                ).pack(),
            ),
            InlineKeyboardButton(
                text=(
                    "✅ 3m" if state_data.get("auto_remove_datetime") == "3m" else "3m"
                ),
                callback_data=PostButtonData(
                    action="remove_post_interval",
                    type="post_settings_action",
                    data="3m",
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="‹ Назад к посту",
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_created_post_keyboard(post: Post) -> InlineKeyboardMarkup:

    ikb = InlineKeyboardBuilder()
    ikb_reaction = InlineKeyboardBuilder()
    ikb_buttons = InlineKeyboardBuilder()

    if post.post_reaction_buttons:
        for reaction in post.post_reaction_buttons:
            ikb_reaction.button(
                text=f"{reaction.text} {len(reaction.reactions) if len(reaction.reactions) > 0 else ''}",
                callback_data=EmojiButtonData(
                    action="add_reaction",
                    post_id=post.id,
                    id=reaction.id,
                    text=f"{reaction.text} {len(reaction.reactions)}",
                    type="emoji_action",
                ).pack(),
            )
        ikb_reaction.adjust(len(post.post_reaction_buttons))
        ikb.attach(InlineKeyboardBuilder.from_markup(ikb_reaction.as_markup()))

    if post.post_keyboards:
        for button in post.post_keyboards:
            if button.button_column == 0:
                ikb_buttons.button(
                    text=button.button_text,
                    url=button.button_url,
                )
            else:
                ikb_buttons.row()
                ikb_buttons.button(
                    text=button.button_text,
                    url=button.button_url,
                )
        ikb_buttons.adjust(len(post.post_keyboards))
        ikb.attach(InlineKeyboardBuilder.from_markup(ikb_buttons.as_markup()))

    return ikb.as_markup()


def get_reaction_buttons_keyboard(state_data: dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для добавления реакций к посту
    """
    ikb = InlineKeyboardBuilder()
    reactions = state_data.get("reactions", [])
    for reaction in reactions:
        ikb.button(
            text=reaction,
            callback_data=EmojiButtonData(
                action="add_reaction",
                post_id=-1,
                id=-1,
                text=reaction,
                type="emoji_action",
            ).pack(),
        )
    ikb.adjust(len(reactions))
    return ikb.as_markup()


def get_post_buttons_keyboard(
    state_data: dict[str, Any], post_id: int = -1
) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardBuilder()
    # buttton format  {"name": name, "url": url, "row": row, "column": column}
    buttons = state_data.get("buttons", [])
    for button in buttons:
        # check if button column is 0 it is a single button
        if button["column"] == 0:
            ikb.button(
                text=button["name"],
                url=button["url"],
                callback_data=EmojiButtonData(
                    action="add_reaction",
                    post_id=post_id,
                    type="emoji_action",
                ).pack(),
            )
        else:
            ikb.row()
            ikb.button(
                text=button["name"],
                url=button["url"],
                callback_data=EmojiButtonData(
                    action="add_reaction",
                    post_id=post_id,
                    type="emoji_action",
                ).pack(),
            )
    ikb.adjust(len(buttons))
    return ikb.as_markup()


def get_confirm_post_keyboard(state_data: dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для подтверждения поста"""
    date_frames_confirm = state_data.get("date_frames_confirm", None)
    stop_schedule_date_frames = state_data.get("stop_schedule_date_frames", None)
    time_frames = state_data.get("time_frames", [])
    time_frames_active_state = state_data.get("time_frames_active", "off")
    btn_text = ",".join(time_frames) if time_frames else ""

    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("✅⚡️ Confirm"),
                callback_data=PostButtonData(
                    action="confirm_create_post", type="post_settings_action"
                ).pack(),
            )
        ],
        (
            [
                InlineKeyboardButton(
                    text=f"📅 {date_frames_confirm} - {stop_schedule_date_frames}",
                    callback_data=PostButtonData(
                        action="show_next_post_date_calendar",
                        type="post_settings_action",
                    ).pack(),
                )
            ]
            if date_frames_confirm
            else []
        ),
        (
            [
                InlineKeyboardButton(
                    text=f"{CheckState[time_frames_active_state]}⏰ Интервал {btn_text}",
                    callback_data=PostButtonData(
                        action="active_multiposting_timeframe",
                        type="post_settings_action",
                    ).pack(),
                )
            ]
            if time_frames
            else []
        ),
        [
            InlineKeyboardButton(
                text=__("Change post time"),
                callback_data=GeneralSettingsButtonData(
                    action="show_multiposting_timeframe", type="general_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=__("‹ Back to post"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_add_media_keyboard(state_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для добавления медиа (🔼 Вверх с превью | 🆙 Вверх без превью | 🔽 Вниз с превью)
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("🔼 Top with preview"),
                callback_data=PostMediaPositionData(
                    action="add_media", media_position="top_preview"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=__("🔽 Bottom with preview"),
                callback_data=PostMediaPositionData(
                    action="add_media", media_position="bottom_preview"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("‹ Back to post"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_back_to_post_keyboard(state_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для возврата к посту"""

    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("‹ Back to post"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ]
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_post_settings_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для настроек поста"""
    pass


def get_post_jobs_keyboard(data: Dict[str, Any], jobs: list) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для задач постинга"""
    inline_kb_list = []
    index = 0
    for job in jobs:
        inline_kb_list.append(
            [
                InlineKeyboardButton(
                    text=f"🗑️ Удалить задачу {job.id}",
                    callback_data=GeneralSettingsButtonData(
                        action="delete_post_job",
                        type="general_settings_action",
                        data=str(index),
                    ).pack(),
                )
            ]
        )
        index += 1
    inline_kb_list.append(
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=GeneralSettingsButtonData(
                    action="back", type="general_settings_action"
                ).pack(),
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_general_settings_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    text = data.get("text", None)
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("📅 Multiposting schedule"),
                callback_data=GeneralSettingsButtonData(
                    action="show_multiposting_timeframe", type="general_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=__("🗒️ Posting task log"),
                callback_data=GeneralSettingsButtonData(
                    action="show_posting_tasks", type="general_settings_action"
                ).pack(),
            )
        ],
        (
            [
                InlineKeyboardButton(
                    text=__("‹ Back to post"),
                    callback_data=PostButtonData(
                        action="back", type="post_settings_action"
                    ).pack(),
                )
            ]
            if text
            else []
        ),
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_multiposting_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для мультипостинга
    """
    time_frames = data.get("time_frames", [])
    time_frames_active_state = data.get("time_frames_active", "off")
    btn_text = __("Off") if time_frames_active_state == "off" else __("On")
    text = data.get("text", None)

    inline_kb_list = [
        (
            [
                InlineKeyboardButton(
                    text=f"{CheckState[time_frames_active_state]} {btn_text}",
                    callback_data=GeneralSettingsButtonData(
                        action="active_multiposting_timeframe",
                        type="general_settings_action",
                    ).pack(),
                )
            ]
            if time_frames
            else []
        ),
        (
            [
                InlineKeyboardButton(
                    text="🗑️ Удалить",
                    callback_data=GeneralSettingsButtonData(
                        action="delete_multiposting_timeframe",
                        type="general_settings_action",
                    ).pack(),
                )
            ]
            if time_frames
            else []
        ),
        (
            [
                InlineKeyboardButton(
                    text=__("‹ Back to post"),
                    callback_data=PostButtonData(
                        action="back", type="post_settings_action"
                    ).pack(),
                )
            ]
            if text
            else []
        ),
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=GeneralSettingsButtonData(
                    action="back", type="general_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_next_calendar_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для выбора даты
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("Next ›"),
                callback_data=PostButtonData(
                    action="show_stop_schedule_date_frames", type="post_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_confirm_calendar_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для подтверждения выбора даты
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text=__("✅⚡️ Confirm"),
                callback_data=PostButtonData(
                    action="date_frames_confirm", type="post_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=PostButtonData(
                    action="show_next_post_date_calendar", type="post_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_post_publish_settings_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для настроек публикации поста
    """
    inline_kb_list = [
        # [
        #     InlineKeyboardButton(
        #         text="🕒 Таймер удаления",
        #         callback_data=PostButtonData(
        #             action="show_remove_time", type="post_settings_action"
        #         ).pack(),
        #     )
        # ],
        # [
        #     InlineKeyboardButton(
        #         text="♻️ Автоповтор/Зацикленность",
        #         callback_data=PostButtonData(
        #             action="show_auto_repeat", type="post_settings_action"
        #         ).pack(),
        #     )
        # ],
        [
            InlineKeyboardButton(
                text=__("💼 Report to client"),
                callback_data=PostButtonData(
                    action="show_send_report", type="post_settings_action"
                ).pack(),
            ),
            InlineKeyboardButton(
                text=__("➡️ Forward"),
                callback_data=PostButtonData(
                    action="show_send_copy_post", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("📅 Schedule"),
                callback_data=PostButtonData(
                    action="show_next_post_date_calendar", type="post_settings_action"
                ).pack(),
            ),
            InlineKeyboardButton(
                text=__("🚀 Publish"),
                callback_data=PostButtonData(
                    action="publish_post", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("🕒 Delete timer"),
                callback_data=PostButtonData(
                    action="show_remove_time", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("🤖 AI integration"),
                callback_data=PostButtonData(
                    action="ai_integration", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("📊 CRM integration"),
                callback_data=PostButtonData(
                    action="crm_integration", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            ),
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_channel_list_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для списка каналов"""

    channel_list = data.get("chat_channel_list", [])
    channel_buttons = []

    action_buttons = [
        InlineKeyboardButton(
            text=__("✓ Select all"),
            callback_data=PostButtonData(
                action="select_all_channels", type="post_settings_action"
            ).pack(),
        ),
    ]

    for channel in channel_list:
        btn_text = f'{CheckState[channel['checked']]} {channel["title"]}'

        if channel["checked"] == "on" and len(action_buttons) < 2:
            action_buttons.append(
                InlineKeyboardButton(
                    text=__("⚡ CONFIRM"),
                    callback_data=PostButtonData(
                        action="confirm", type="post_settings_action"
                    ).pack(),
                )
            )

        channel_buttons.append(
            InlineKeyboardButton(
                text=btn_text,
                callback_data=ChannelData(
                    action="check", channel_id=channel["id"]
                ).pack(),
            )
        )

    inline_kb_list = [
        channel_buttons,
        action_buttons,
        [
            InlineKeyboardButton(
                text=__("‹ Back"),
                callback_data=PostButtonData(
                    action="back", type="post_settings_action"
                ).pack(),
            )
        ],
    ]

    return InlineKeyboardMarkup(inline_keyboard=inline_kb_list)


def get_settings_post_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    ikb = InlineKeyboardBuilder()
    for btn in post_inline_buttons:
        if data.get("media_file_name") and btn["action"] == "add_media":
            btn["text"] = __("🗑️ Delete media")
            btn["action"] = "remove_media"
        elif btn["action"] == "remove_media" and not data.get("media_file_name"):
            btn["text"] = __("📎 Add media")
            btn["action"] = "add_media"

        if data.get("reactions") and btn["action"] == "add_reactions":
            btn["text"] = __("🗑️ Delete reactions")
            btn["action"] = "remove_reactions"
        elif not data.get("reactions") and btn["action"] == "remove_reactions":
            btn["text"] = __("😊 Add reactions")
            btn["action"] = "add_reactions"

        if data.get("buttons") and btn["action"] == "add_buttons":
            btn["text"] = __("🗑️ Delete buttons")
            btn["action"] = "remove_buttons"
        elif not data.get("buttons") and btn["action"] == "remove_buttons":
            btn["text"] = __("🎛️ Add buttons")
            btn["action"] = "add_buttons"

        if btn["action"] == "sound":
            btn_text = f'{CheckState[data["sound"]]} {btn["text"]}'
        elif btn["action"] == "comments":
            btn_text = f'{CheckState[data["comments"]]} {btn["text"]}'
        elif btn["action"] == "pin":
            btn_text = f'{CheckState[data["pin"]]} {btn["text"]}'
        elif btn["action"] == "signature":
            btn_text = f'{CheckState[data["signature"]]} {btn["text"]}'
        else:
            btn_text = btn["text"]
        ikb.button(
            text=btn_text,
            callback_data=PostButtonData(action=btn["action"], type=btn["type"]),
        )
    ikb.adjust(2)
    return ikb.as_markup()


def get_chat_channel_keyboard() -> ReplyKeyboardMarkup:
    rkb = ReplyKeyboardBuilder()
    for btn in add_chat_channel_buttons:
        if btn == __("Channel"):
            rkb.button(
                text=btn,
                request_chat=KeyboardButtonRequestChat(
                    request_id=1,
                    request_title=True,
                    chat_is_channel=True,
                    bot_is_member=True,
                ),
            )
        elif btn == __("Chat"):
            rkb.button(
                text=btn,
                request_chat=KeyboardButtonRequestChat(
                    request_id=2,
                    request_title=True,
                    chat_is_channel=False,
                    bot_is_member=True,
                ),
            )
        else:
            rkb.button(text=btn)
    rkb.adjust(2)
    return rkb.as_markup()
