import datetime
import re

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.calendarinterval import CalendarIntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from models.Post import Post

from . import post_repository

jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:///database.db"),
}

scheduler = AsyncIOScheduler(jobstores=jobstores)


def parse_schedule_string(s):
    s = s.strip()

    # Time of day: HH:MM format
    if re.match(r"^\d{1,2}:\d{2}$", s):
        hour, minute = map(int, s.split(":"))
        return "cron", {"hour": hour, "minute": minute}

    # Duration format: "Xh Ym"
    match = re.match(r"(?:(\d+)\s*h)?\s*(?:(\d+)\s*m)?", s)
    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return "interval", {"hours": hours, "minutes": minutes}

    raise ValueError(f"Invalid schedule format: {s}")


def parse_time_from_str(time_str: str) -> str:
    """
    Parse a time string in various formats (e.g., "HH:MM", "HH MM", "HHMM")
    and return hours and minutes
    """
    try:
        # Match formats like "12:00", "12 00", or "1200" or "12"
        match = re.match(r"^(\d{1,2})(m|h)?(?::|\s)?(\d{1,2})?(m|h)?", time_str)

        duration_time = int(match.group(1)) if match.group(1) else 0
        duration_time2 = int(match.group(3)) if match.group(3) else None
        duration_str = match.group(2) if match.group(2) else ""
        duration_str2 = match.group(4) if match.group(4) else ""

        first_interval = ""
        second_interval = ""

        if duration_str in ["m", "h"] and duration_time > 0:
            first_interval = f"{duration_time}{duration_str} "
            if duration_str == "m" and duration_time < 15:
                raise ValueError("Minimum interval is 15 minutes")

        elif duration_time > 0:
            first_interval = f"{duration_time}:{'00' if duration_time2 is None else ""}"

        if duration_str2 in ["m", "h"] and duration_time2 > 0:
            second_interval = f"{duration_time2}{duration_str2}"
        elif duration_time2 is not None:
            second_interval = (
                f"{duration_time2 if duration_time2 > 0 else str(duration_time2) + '0'}"
            )

        if not first_interval:
            raise ValueError("Invalid time format")

        return f"{first_interval}{second_interval}"

    except ValueError:
        raise ValueError("Invalid time format")


async def job_func(post_id: int):
    await post_repository.send_post(post_id, True, create_remove_post_jod)


async def job_func_remove(post_id: int, chat_id: str, message_id: int):
    await post_repository.remove_post(post_id, chat_id, message_id)


def create_remove_post_jod(
    post: Post, chat_id: str, message_id: int, datetime: datetime.datetime
):
    """
    Create a job to remove a post at a specific datetime.
    """
    print(f"Create job Removing post {post.id} in chat {chat_id} at {datetime}")
    scheduler.add_job(
        job_func_remove,
        args=[post.id, chat_id, message_id],
        id=f"{post.user_id}_{post.id}_{chat_id}_{message_id}_remove",
        trigger=DateTrigger(
            run_date=datetime,
        ),
        replace_existing=True,
    )


def create_jod(post: Post, time_frames: list[str], job_type: str = "cron"):
    post_schedule = post.post_schedule
    _date = None

    if post_schedule and post_schedule.is_active:
        _date = datetime.datetime.strptime(
            post_schedule.schedule_date_frames, "%d/%m/%Y"
        )
    index = 0
    for time_frame in time_frames:
        try:
            _type, params = parse_schedule_string(time_frame)
            print(f"Parsed duration: {_type}, {params} minutes")
            if _type == "interval":
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{index}_interval",
                    trigger=IntervalTrigger(
                        start_date=_date,
                        **params,
                    ),
                    replace_existing=True,
                )
            elif _type == "cron":
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{index}cron",
                    trigger=CronTrigger(
                        start_date=_date,
                        **params,
                    ),
                    replace_existing=True,
                )
            index += 1
        except ValueError as e:
            print(f"Error parsing time frame '{time_frame}': {e}")


def submited_event_listener(event):
    """
    Listener for job submission events.
    """
    if event.exception:
        print(f"Job {event.job_id} failed to execute: {event.exception}")
    else:
        print(f"Job {event.job_id} submitted successfully.")


def executed_event_listener(event):
    """
    Listener for job execution events.
    """
    if event.exception:
        print(f"Job {event.job_id} failed to execute: {event.exception}")
    else:
        print(f"Job {event.job_id} executed successfully.")


async def start_scheduler():
    """
    Start the scheduler.
    """
    scheduler.add_listener(submited_event_listener, EVENT_JOB_SUBMITTED)
    scheduler.add_listener(
        executed_event_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
    )
    scheduler.start()
