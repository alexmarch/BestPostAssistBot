from typing import List

from sqlalchemy import ForeignKey, String, Text
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
    posts: Mapped[List["Post"]] = relationship(
        secondary=association_table, back_populates="channels"
    )
