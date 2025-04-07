from models import session

from .post_repository import PostRepository
from .scheduler_repository import ScheduleRepository
from .user_repository import UserRepository

user_repository = UserRepository(session)
post_repository = PostRepository(session)
scheduler_repository = ScheduleRepository(session)
