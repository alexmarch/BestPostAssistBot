from sqlalchemy import ForeignKey
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from . import Base

class MediaFile(Base):
  __tablename__ = "media_files"
  id: Mapped[int] = mapped_column(primary_key=True)
  file_path: Mapped[str] = mapped_column(String)
  type: Mapped[str] = mapped_column(String)
  post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
  post: Mapped['Post'] = relationship(back_populates="media_file")
