import datetime
import os
import re

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, EVENT_JOB_SUBMITTED
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from models.Post import Post
from repositories import get_session
from repositories.post_repository import PostRepository

DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///database.db")

jobstores = {
    "default": SQLAlchemyJobStore(url=DATABASE_URI),
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


async def stop_job(user_id: int, post_id: int, hour: int, minute: int, _type: str):
    try:
        job_id = f"{user_id}_{post_id}_{hour}_{minute}_{_type}"
        remove_job_by_id(job_id)
    except:
        pass

    stop_job_id = f"{user_id}_{post_id}_{hour}_{minute}_{_type}_stop_job"
    remove_job_by_id(stop_job_id)


async def job_func(post_id: int):
    post_repository = PostRepository(get_session())
    await post_repository.send_post(post_id, True, create_remove_post_jod)


async def job_func_remove(user_id: int, post_id: int, chat_id: str, message_id: int):
    post_repository = PostRepository(get_session())
    await post_repository.remove_post(post_id, chat_id, message_id)
    remove_job_by_id(f"{user_id}_{post_id}_{chat_id}_{message_id}_remove")


def create_remove_post_jod(
    post: Post, chat_id: str, message_id: int, datetime: datetime.datetime
):
    """
    Create a job to remove a post at a specific datetime.
    """
    print(f"Create job Removing post {post.id} in chat {chat_id} at {datetime}")
    scheduler.add_job(
        job_func_remove,
        args=[post.user_id, post.id, chat_id, message_id],
        id=f"{post.user_id}_{post.id}_{chat_id}_{message_id}_remove",
        trigger=DateTrigger(
            run_date=datetime,
        ),
        replace_existing=True,
    )


def remove_job_by_id(job_id: str) -> bool:
    """
    Remove a job by its ID.
    """
    try:
        job = scheduler.get_job(job_id)
        if job:
            print(f"Removing job {job_id}")
            scheduler.remove_job(job_id)
            return True
        else:
            print(f"Job {job_id} not found")
    except:
        pass

    return False


def remove_job_by_time_interval(time_frames: list[str], user_id: int):
    post_repository = PostRepository(get_session())
    posts = post_repository.get_all_posts_by_user_id(user_id)
    for post in posts:
        for time_frame in time_frames:
            try:
                _type, params = parse_schedule_string(time_frame)
                print(f"Parsed duration: {_type}, {params} minutes")
                if _type == "interval":
                    id = f"{post.user_id}_{post.id}_{params['hours']}_{params['minutes']}_interval"
                    job = scheduler.get_job(id)
                    if job:
                        print(f"Removing job {id} for post {post.id}")
                        scheduler.remove_job(id)
                elif _type == "cron":
                    id = f"{post.user_id}_{post.id}_{params['hour']}_{params['minute']}_cron"
                    job = scheduler.get_job(id)
                    if job:
                        print(f"Removing job {id} for post {post.id}")
                        scheduler.remove_job(
                            f"{post.user_id}_{post.id}_{params['hour']}_{params['minute']}_cron"
                        )
            except ValueError as e:
                print(f"Error parsing time frame '{time_frame}': {e}")


def get_all_jobs_by_user_id(time_frames: list[str], user_id: int) -> list:
    """
    Get all jobs for a user by user_id.
    """
    post_repository = PostRepository(get_session())
    posts = post_repository.get_all_posts_by_user_id(user_id)
    # user_multiposting = user_repository.get_multiposting_by_id(user_id)
    user_multiposting = None
    jobs = []
    stop_jobs = []
    for post in posts:
        for time_frame in time_frames:
            try:
                _type, params = parse_schedule_string(time_frame)
                if _type == "interval":
                    id = f"{post.user_id}_{post.id}_{params['hours']}_{params['minutes']}_interval"
                    stop_job_id = f"{post.user_id}_{post.id}_{params['hours']}_{params['minutes']}_interval_stop_job"
                    job = scheduler.get_job(id)
                    stop_job = scheduler.get_job(stop_job_id)
                    if job:
                        jobs.append(job)
                    if stop_job:
                        stop_jobs.append(stop_job)
                elif _type == "cron":
                    id = f"{post.user_id}_{post.id}_{params['hour']}_{params['minute']}_cron"
                    stop_job_id = f"{post.user_id}_{post.id}_{params['hour']}_{params['minute']}_cron_stop_job"
                    stop_job = scheduler.get_job(stop_job_id)
                    job = scheduler.get_job(id)
                    if job:
                        jobs.append(job)
                    if stop_job:
                        stop_jobs.append(stop_job)
            except ValueError as e:
                print(f"Error parsing time frame '{time_frame}': {e}")

    return jobs, stop_jobs


def create_jod(post: Post, time_frames: list[str], auto_repeat_dates: list[str] = []):
    post_schedule = post.post_schedule
    start_date = None
    end_date, start_date = None, None
    if post_schedule and post_schedule.is_active:
        start_date = datetime.datetime.strptime(
            post_schedule.schedule_date_frames, "%d/%m/%Y"
        )
        end_date = datetime.datetime.strptime(
            post_schedule.stop_schedule_date_frames, "%d/%m/%Y"
        )
        if len(auto_repeat_dates) > 0:
            start_date = datetime.datetime.strptime(auto_repeat_dates[0], "%d/%m/%Y")
            end_date = datetime.datetime.strptime(auto_repeat_dates[-1], "%d/%m/%Y")

    if not start_date:
        start_date = datetime.datetime.now()

    index = 0

    for time_frame in time_frames:
        try:
            _type, params = parse_schedule_string(time_frame)

            if _type == "interval":
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{params['hours']}_{params['minutes']}_interval",
                    trigger=IntervalTrigger(
                        start_date=start_date,
                        end_date=(
                            end_date if end_date and end_date != start_date else None
                        ),
                        timezone="Europe/Kiev",
                        **params,
                    ),
                    next_run_time=datetime.datetime.now(),
                    replace_existing=True,
                )
            elif _type == "cron":
                scheduler.add_job(
                    job_func,
                    args=[post.id],
                    id=f"{post.user_id}_{post.id}_{params['hour']}_{params['minute']}_cron",
                    trigger=CronTrigger(
                        start_date=start_date,
                        end_date=(
                            end_date if end_date and end_date != start_date else None
                        ),
                        timezone="Europe/Kiev",
                        **params,
                    ),
                    replace_existing=True,
                )

            if end_date:
                hour = params.get("hour", None)
                if not hour:
                    hour = params.get("hours", None)

                minute = params.get("minute", None)
                if not minute:
                    minute = params.get("minutes", None)

                scheduler.add_job(
                    stop_job,
                    args=[
                        post.user_id,
                        post.id,
                        hour,
                        minute,
                        _type,
                    ],
                    id=f"{post.user_id}_{post.id}_{hour}_{minute}_{_type}_stop_job",
                    trigger=DateTrigger(
                        run_date=end_date,
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
