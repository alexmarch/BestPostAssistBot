from sqlalchemy import Boolean, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class PostSchedule(Base):
    __tablename__ = "posts_schedules"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    post: Mapped["Post"] = relationship(back_populates="post_schedule")
    schedule_time_frames: Mapped[str] = mapped_column(String(100), nullable=True)
    schedule_date_frames: Mapped[str] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(
        String(100), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        String(100), server_default=func.now(), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
