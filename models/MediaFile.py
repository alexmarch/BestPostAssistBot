from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class MediaFile(Base):
    __tablename__ = "posts_media_files"
    id: Mapped[int] = mapped_column(primary_key=True)
    media_file_path: Mapped[str] = mapped_column(String)
    media_file_name: Mapped[str] = mapped_column(String)
    media_file_type: Mapped[str] = mapped_column(String)
    media_file_position: Mapped[str] = mapped_column(String)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    post: Mapped["Post"] = relationship(back_populates="post_media_file")
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
