from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Router
from aiogram.types import TelegramObject

from repositories import user_repository


class UserMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        event_user = data.get("event_from_user", None)
        user = None
        if event_user:
            try:
                user = user_repository.find_by_chat_id(event_user.id)
            except Exception as e:
                print(f"Error finding user by chat_id: {e}")
        if user:
            data["user_id"] = user.id
        return await handler(event, data)


base_router = Router()
post_router = Router()
user_router = Router()
media_router = Router()

post_router.include_router(media_router)

post_router.message.outer_middleware(UserMiddleware())

from . import base, media, post, profile
