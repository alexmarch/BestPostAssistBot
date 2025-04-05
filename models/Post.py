from typing import List
from sqlalchemy import ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from . import association_table

class Post(Base):
  __tablename__ = "posts"
  id: Mapped[int] = mapped_column(primary_key=True)
  user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
  user: Mapped["User"] = relationship(back_populates="posts")
  text: Mapped[str] = mapped_column(Text)
  disable_notification: Mapped[bool] = mapped_column(Boolean, default=False)
  disable_web_page_preview: Mapped[bool] = mapped_column(Boolean, default=False)
  protect_content: Mapped[bool] = mapped_column(Boolean, default=False) # This prevents users from forwarding or saving the post but does not directly disable comments.
  remove_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
  media_file: Mapped['MediaFile'] = relationship(back_populates="post")
  channels: Mapped[List['Channel']] = relationship(secondary=association_table, back_populates="posts")
