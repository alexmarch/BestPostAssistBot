import os

from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy.pool import NullPool


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

engine = create_engine(
    DATABASE_URL,
    echo_pool="debug",  # log pool checkouts
    pool_size=40,  # default
    max_overflow=10,  # allow 10 overflow connections
    pool_timeout=30,  # wait up to 30 seconds for a connection
)  # wait up to 30s before raising error)

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
