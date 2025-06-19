from models import get_session

from .post_repository import PostRepository
from .scheduler_repository import ScheduleRepository
from .user_repository import UserRepository

session = get_session()

user_repository = UserRepository(get_session())
post_repository = PostRepository(get_session())
scheduler_repository = ScheduleRepository(get_session())
