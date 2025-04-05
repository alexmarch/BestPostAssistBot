from models import session
from .user_repository import UserRepository

user_repo = UserRepository(session)
