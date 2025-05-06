from typing import Any

from sqlalchemy import func, select

from models import Channel, Multiposting, Post, User
from states.post import PostForm

from .base import BaseRepository


class UserRepository(BaseRepository):
    def create(
        self, chat_id: int, username: str, full_name: str, timezone: str
    ) -> User:
        user = User(
            chat_id=chat_id, username=username, full_name=full_name, timezone=timezone
        )
        self.session.add(user)
        self.session.commit()
        return user

    def find_by_chat_id(self, chat_id: int) -> User | None:
        return self.session.execute(
            select(User).where(User.chat_id == chat_id)
        ).scalar()

    def find_by_username(self, username: str) -> User | None:
        return self.session.execute(
            select(User).where(User.username == username)
        ).scalar()

    def count_channels(self, user: User) -> int:
        res = self.session.execute(
            select(func.count("*"))
            .select_from(Channel)
            .where(Channel.user_id == user.id)
        ).one()
        return res[0]

    def count_posts(self, user: User) -> int:
        res = self.session.execute(
            select(func.count("*")).select_from(Post).where(Post.user_id == user.id)
        ).one()
        return res[0]

    def get_user_channel_by_chat_id(self, user: User, chat_id: str) -> Channel | None:
        return self.session.execute(
            select(Channel)
            .where(Channel.user_id == user.id)
            .where(Channel.chat_id == chat_id)
        ).scalar()

    def get_all_user_channels(self, user: User) -> list[Channel]:
        return (
            self.session.execute(select(Channel).where(Channel.user_id == user.id))
            .scalars()
            .all()
        )

    def add_channel(self, user: User, chat_id: str, title: str, type: str) -> Channel:
        channel = Channel(user_id=user.id, chat_id=chat_id, title=title, type=type)
        self.session.add(channel)
        self.session.commit()
        return channel

    def delete_channel(self, user: User, channel: Channel) -> None:
        self.session.delete(channel)
        self.session.commit()

    def create_multiposting(self, user: User, timeframes: list[str]) -> Multiposting:
        # Check if the user already has a multiposting
        existing_multiposting = self.session.execute(
            select(Multiposting).where(Multiposting.user_id == user.id)
        ).scalar()
        if existing_multiposting:
            # Update the existing multiposting
            existing_multiposting.time_frames = "|".join(timeframes)
            self.session.commit()
            return existing_multiposting
        # Create a new multiposting
        multiposting = Multiposting(
            user_id=user.id,
            time_frames="|".join(timeframes),
        )
        self.session.add(multiposting)
        self.session.commit()
        return multiposting

    def get_multiposting(self, user: User) -> Multiposting | None:
        return self.session.execute(
            select(Multiposting).where(Multiposting.user_id == user.id)
        ).scalar()

    def delete_multiposting_timeframe(self, user: User) -> None:
        multiposting = self.session.execute(
            select(Multiposting).where(Multiposting.user_id == user.id)
        ).scalar()
        if multiposting:
            self.session.delete(multiposting)
            self.session.commit()

    def get_multiposting_by_id(self, multiposting_id: int) -> Multiposting | None:
        return self.session.execute(
            select(Multiposting).where(Multiposting.id == multiposting_id)
        ).scalar()

    def get_multiposting_by_user_id(self, user_id: int) -> Multiposting | None:
        return self.session.execute(
            select(Multiposting).where(Multiposting.user_id == user_id)
        ).scalar()

    def update_multiposting_active_timeframe(self, user: User, state: str) -> None:
        multiposting = self.session.execute(
            select(Multiposting).where(Multiposting.user_id == user.id)
        ).scalar()
        if multiposting:
            multiposting.active = True if state == "on" else False
            self.session.commit()
