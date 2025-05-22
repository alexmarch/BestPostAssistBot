import os

from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


association_table = Table(
    "association_table",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id")),
    Column("channel_id", ForeignKey("posts_channels.id")),
)

DATABASE_URL = os.getenv(
    "DATABASE_URL", "mysql+pymysql://vanileuser:vanilepass@mariadb/vaniledb"
)

engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(engine)


def get_session():
    return Session()


def create_all():
    Base.metadata.create_all(engine)


from .Channel import Channel
from .MediaFile import MediaFile
from .Multiposting import Multiposting
from .Post import Post
from .PostKeyboard import PostKeyboard
from .PostReactioButton import PostReactioButton
from .PostSchedule import PostSchedule
from .User import User
