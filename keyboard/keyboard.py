from enum import Enum
from typing import Any, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButtonRequestChat,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

CheckState = {"on": "✅", "off": "☑️"}

main_buttons = [
    "Добавить канал/чат",
    "Создать пост",
    "Настройки",
    "Изменить пост",
    "Контент-план",
    "Шаблоны",
    "Мой профиль",
]

add_chat_channel_buttons = [
    "Канал",
    "Чат",
    "Главное меню",
]

post_inline_buttons = [
    {
        "text": "📝 Изменить текст",
        "action": "change_text",
        "type": "post_settings_action",
    },
    {
        "text": "📎 Добавить медиа",
        "action": "add_media",
        "type": "post_settings_action",
    },
    {
        "text": "🎛️ Добавить кнопки",
        "action": "add_buttons",
        "type": "post_settings_action",
    },
    {
        "text": "😊 Добавить реакции",
        "action": "add_reactions",
        "type": "post_settings_action",
    },
    {"text": "Звук 🔊", "action": "sound", "type": "post_settings"},
    {"text": "Коментарии 💬", "action": "comments", "type": "post_settings"},
    {"text": "Закрепить 📌", "action": "pin", "type": "post_settings"},
    {"text": "Aвтоподпись ✍️", "action": "signature", "type": "post_settings"},
    {
        "text": "‹ Каналы/чаты",
        "action": "add_chat_channel",
        "type": "post_settings_action",
    },
    {"text": "Далее ›", "action": "next", "type": "post_settings_action"},
]


class PostButtonData(CallbackData, prefix="post"):
    action: str
    type: str = "settings"


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


def get_confirm_post_keyboard(state_data: dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для подтверждения поста"""
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text="✅⚡️ Подтвердить",
                callback_data=PostButtonData(
                    action="confirm_create_post", type="post_settings_action"
                ).pack(),
            )
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


def get_add_media_keyboard(state_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для добавления медиа (🔼 Вверх с превью | 🆙 Вверх без превью | 🔽 Вниз с превью)
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text="🔼 Вверх с превью",
                callback_data=PostMediaPositionData(
                    action="add_media", media_position="top_preview"
                ).pack(),
            )
        ],
        # [
        #     InlineKeyboardButton(
        #         text="🆙 Вверх без превью",
        #         callback_data=PostMediaPositionData(
        #             action="add_media", media_position="top_no_preview"
        #         ).pack(),
        #     ),
        # ],
        [
            InlineKeyboardButton(
                text="🔽 Вниз с превью",
                callback_data=PostMediaPositionData(
                    action="add_media", media_position="bottom_preview"
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


def get_back_to_post_keyboard(state_data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для возврата к посту"""

    inline_kb_list = [
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


def get_post_settings_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Возвращает маркап клавиатуры для настроек поста"""
    pass


def get_post_publish_settings_keyboard(data: Dict[str, Any]) -> InlineKeyboardMarkup:
    """
    Возвращает маркап клавиатуры для настроек публикации поста
    """
    inline_kb_list = [
        [
            InlineKeyboardButton(
                text="🕒 Таймер удаления",
                callback_data=PostButtonData(
                    action="show_remove_time", type="post_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="♻️ Автоповтор/Зацикленность",
                callback_data=PostButtonData(
                    action="show_auto_repeat", type="post_settings_action"
                ).pack(),
            )
        ],
        [
            InlineKeyboardButton(
                text="💼 Отчет клиету",
                callback_data=PostButtonData(
                    action="show_send_report", type="post_settings_action"
                ).pack(),
            ),  # Приграсить либо отправить id клиента
            InlineKeyboardButton(
                text="➡️ Переслать",
                callback_data=PostButtonData(
                    action="show_send_report", type="post_settings_action"
                ).pack(),
            ),  # Переслать на выбранный канал/чат
        ],
        [
            InlineKeyboardButton(
                text="📅 Отложить",
                callback_data=PostButtonData(
                    action="show_next_post_date_calendar", type="post_settings_action"
                ).pack(),
            ),  # Отображает календарь для отложеной публикации
            InlineKeyboardButton(
                text="🚀 Опубликовать",
                callback_data=PostButtonData(
                    action="publish_post", type="post_settings_action"
                ).pack(),
            ),  # ✔️ Подтвердите отправку поста с кнопкой подтвердить
        ],
        [
            InlineKeyboardButton(
                text="🤖 Интеграция с ИИ",
                callback_data=PostButtonData(
                    action="ai_integration", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="📊 Интеграция с CRM",
                callback_data=PostButtonData(
                    action="crm_integration", type="post_settings_action"
                ).pack(),
            ),
        ],
        [
            InlineKeyboardButton(
                text="‹ Назад",
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
            text="✓ Выбрать все",
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
                    text="⚡ ПОДТВЕРДИТЬ",
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
                text="‹ Назад",
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
            btn["text"] = "🗑️ Удалить медиа"
            btn["action"] = "remove_media"
        elif btn["action"] == "remove_media" and not data.get("media_file_name"):
            btn["text"] = "📎 Добавить медиа"
            btn["action"] = "add_media"

        # if btn["action"] == "add_chat_channel":
        #     btn["text"] = f"{btn["text"]} ({len(data.get('chat_channel_list', []))})"

        if btn["action"] == "sound":
            btn_text = f'{CheckState[data["sound"]]} {btn['text']}'
        elif btn["action"] == "comments":
            btn_text = f'{CheckState[data["comments"]]} {btn['text']}'
        elif btn["action"] == "pin":
            btn_text = f'{CheckState[data["pin"]]} {btn['text']}'
        elif btn["action"] == "signature":
            btn_text = f'{CheckState[data["signature"]]} {btn['text']}'
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
        if btn == "Канал":
            rkb.button(
                text=btn,
                request_chat=KeyboardButtonRequestChat(
                    request_id=1,
                    request_title=True,
                    chat_is_channel=True,
                    bot_is_member=True,
                    # bot_administrator_rights=ChatAdministratorRights(
                    #   is_anonymous=False,
                    #   can_manage_chat=False,
                    #   can_manage_video_chats=False,
                    #   can_promote_members=False,
                    #   can_change_info=False,
                    #   can_post_stories=False,
                    #   can_edit_stories=False,
                    #   can_delete_stories=False,
                    #   can_post_messages=True,
                    #   can_edit_messages=True,
                    #   can_delete_messages=True,
                    #   can_invite_users=True,
                    #   can_restrict_members=True,
                    #   can_pin_messages=True,
                    # )
                ),
            )
        elif btn == "Чат":
            rkb.button(
                text=btn,
                request_chat=KeyboardButtonRequestChat(
                    request_id=2,
                    request_title=True,
                    chat_is_channel=False,
                    bot_is_member=True,
                    # bot_administrator_rights=ChatAdministratorRights(
                    #   is_anonymous=False,
                    #   can_manage_chat=False,
                    #   can_manage_video_chats=False,
                    #   can_promote_members=False,
                    #   can_change_info=False,
                    #   can_post_stories=False,
                    #   can_edit_stories=False,
                    #   can_delete_stories=False,
                    #   can_post_messages=True,
                    #   can_edit_messages=True,
                    #   can_delete_messages=True,
                    #   can_invite_users=True,
                    #   can_restrict_members=True,
                    # )
                ),
            )
        else:
            rkb.button(text=btn)
    rkb.adjust(2)
    return rkb.as_markup()
