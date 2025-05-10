from typing import List

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base, association_table


class Channel(Base):
    __tablename__ = "posts_channels"
    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(Text)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="channels")
    type: Mapped[str] = mapped_column(String(20))
    messages_ids: Mapped[list] = mapped_column(
        MutableList.as_mutable(JSON), nullable=False, default=list  # type: ignore
    )
    posts: Mapped[List["Post"]] = relationship(
        secondary=association_table, back_populates="channels"
    )
