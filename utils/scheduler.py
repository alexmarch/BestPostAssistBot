import datetime
import re

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from models import get_session
from models.Post import Post
from repositories.post_repository import PostRepository

post_repository = PostRepository(get_session())

jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:///database.db"),
}

scheduler = AsyncIOScheduler(jobstores=jobstores)


def parse_time_from_str(time_str: str) -> tuple[int, int]:
    """
    Parse a time string in various formats (e.g., "HH:MM", "HH MM", "HHMM")
    and return hours and minutes
    """
    try:
        # Match formats like "12:00", "12 00", or "1200" or "12"
        match = re.match(r"^(\d{1,2})(?::|\s)?(\d{2})?", time_str)
        if not match:
            raise ValueError("Invalid time format no match found")

        hours = int(match.group(1))
        minutes = (
            int(match.group(2)) if match.group(2) else 0
        )  # Default to 0 if minutes are not provided

        if hours and minutes is None:
            minutes = 0
        # Validate hours and minutes
        if not (0 <= hours < 24 and 0 <= minutes < 60):
            raise ValueError("Invalid time format")

        return hours, minutes

    except ValueError:
        raise ValueError("Invalid time format")


async def job_func(post_id: int):
    await post_repository.send_post(post_id, True)


def create_jod(post: Post, time_frames: list[str], job_type: str = "cron"):
    post_schedule = post.post_schedule
    for time_frame in time_frames:
        try:
            hours, minutes = time_frame.split(":")
            if post_schedule and post_schedule.is_active:
                _date = datetime.datetime.strptime(
                    post_schedule.schedule_date_frames, "%d/%m/%Y"
                )
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{time_frame}",
                    trigger=CronTrigger(
                        year=_date.year,
                        month=_date.month,
                        day=_date.day,
                        hour=hours,
                        minute=minutes,
                    ),
                    replace_existing=True,
                )
            else:
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{time_frame}",
                    trigger=CronTrigger(
                        hour=hours,
                        minute=minutes,
                        second=0,
                        day_of_week="*",
                        month="*",
                        day="*",
                    ),
                    replace_existing=True,
                )
        except ValueError as e:
            print(f"Error parsing time frame '{time_frame}': {e}")


async def start_scheduler():
    """
    Start the scheduler.
    """
    scheduler.start()
