from sqlalchemy import select, func
from models import User, Channel, Post
from .base import BaseRepository

class UserRepository(BaseRepository):

  def create(self, chat_id: int, username: str, full_name: str) -> User:
    user = User(chat_id=chat_id, username=username, full_name=full_name)
    self.session.add(user)
    self.session.commit()
    return user

  def find_by_chat_id(self, chat_id: int) -> User | None:
    return self.session.execute(
        select(User)
        .where(User.chat_id == chat_id)
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
      select(func.count("*"))
        .select_from(Post)
        .where(Post.user_id == user.id)
    ).one()
    return res[0]

  def get_user_channel_by_chat_id(self, user: User, chat_id: str) -> Channel | None:
    return self.session.execute(
        select(Channel)
        .where(Channel.user_id == user.id)
        .where(Channel.chat_id == chat_id)
      ).scalar()

  def get_all_user_channels(self, user: User) -> list[Channel]:
    return self.session.execute(
        select(Channel)
        .where(Channel.user_id == user.id)
      ).scalars().all()

  def add_channel(self, user: User, chat_id: str, title: str, type: str) -> Channel:
    channel = Channel(user_id=user.id, chat_id=chat_id, title=title, type=type)
    self.session.add(channel)
    self.session.commit()
    return channel

