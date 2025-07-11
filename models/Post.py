from typing import List

from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String, Text, func
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, association_table


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_report_chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    recipient_post_chat_id: Mapped[int] = mapped_column(Integer, nullable=True)
    user: Mapped["User"] = relationship(back_populates="posts")
    channels: Mapped[List["Channel"]] = relationship(
        secondary=association_table, back_populates="posts"
    )
    post_media_file: Mapped["MediaFile"] = relationship(back_populates="post")
    post_keyboards: Mapped[List["PostKeyboard"]] = relationship(back_populates="post")
    post_reaction_buttons: Mapped[List["PostReactioButton"]] = relationship(
        back_populates="post"
    )
    post_schedule: Mapped["PostSchedule"] = relationship(back_populates="post")
    text: Mapped[str] = mapped_column(Text)
    sound: Mapped[bool] = mapped_column(Boolean, default=False)
    comments: Mapped[bool] = mapped_column(Boolean, default=False)
    pin: Mapped[bool] = mapped_column(Boolean, default=False)
    signature: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Autosignature post
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    messages_ids: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True, default=list  # type: ignore
    )
    auto_remove_datetime: Mapped[str] = mapped_column(
        String(100), nullable=True, default="48h"
    )
    time_frames: Mapped[List[str]] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True, default=list  # type: ignore
    )
    auto_repeat_dates: Mapped[List[str]] = mapped_column(
        MutableList.as_mutable(JSON), nullable=True, default=list  # type: ignore
    )
    created_at: Mapped[str] = mapped_column(
        String(100), server_default=func.now(), nullable=False
    )
