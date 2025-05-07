from sqlalchemy import JSON, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class PostReactioButton(Base):
    __tablename__ = "posts_reaction_buttons"
    id: Mapped[int] = mapped_column(primary_key=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    post: Mapped["Post"] = relationship(back_populates="post_reaction_buttons")
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    reactions: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
