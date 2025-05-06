from typing import List

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Multiposting(Base):
    __tablename__ = "multipostings"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="multipostings")
    time_frames: Mapped[str] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(default=True)
