from sqlalchemy import Column, ForeignKey, Table, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


association_table = Table(
    "association_table",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id")),
    Column("channel_id", ForeignKey("channels.id")),
)

engine = create_engine("sqlite:///database.db", echo=False)
Session = sessionmaker(engine)

session = Session()


def create_all():
    Base.metadata.create_all(engine)


from .Channel import Channel
from .MediaFile import MediaFile
from .Post import Post
from .User import User
