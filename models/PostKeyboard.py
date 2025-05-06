from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class PostKeyboard(Base):
    __tablename__ = "posts_keyboards"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    post: Mapped["Post"] = relationship(back_populates="post_keyboard")
    button_text: Mapped[str] = mapped_column(String(255), nullable=False)
    button_url: Mapped[str] = mapped_column(String(255), nullable=False)
