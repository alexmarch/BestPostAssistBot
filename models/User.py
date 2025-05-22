from typing import List

from sqlalchemy import BigInteger, Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[BigInteger] = mapped_column(BigInteger, unique=True)
    username: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    posts: Mapped[List["Post"]] = relationship(back_populates="user")
    channels: Mapped[List["Channel"]] = relationship(back_populates="user")
    multipostings: Mapped[List["Multiposting"]] = relationship(back_populates="user")
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    timezone: Mapped[str] = mapped_column(String(255), default="UTC")
