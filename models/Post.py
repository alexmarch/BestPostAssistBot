from typing import List

from sqlalchemy import Boolean, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, association_table


class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
    channels: Mapped[List["Channel"]] = relationship(
        secondary=association_table, back_populates="posts"
    )
    post_media_file: Mapped["MediaFile"] = relationship(back_populates="post")
    post_keyboard: Mapped["PostKeyboard"] = relationship(back_populates="post")
    post_schedules: Mapped[List["PostSchedule"]] = relationship(back_populates="post")
    text: Mapped[str] = mapped_column(Text)
    sound: Mapped[bool] = mapped_column(Boolean, default=False)
    comments: Mapped[bool] = mapped_column(Boolean, default=False)
    pin: Mapped[bool] = mapped_column(Boolean, default=False)
    signature: Mapped[bool] = mapped_column(
        Boolean, default=False
    )  # Autosignature post
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(
        String(100), server_default=func.now(), nullable=False
    )
