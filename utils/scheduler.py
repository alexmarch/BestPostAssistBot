import re

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.background import BackgroundScheduler

jobstores = {
    "default": SQLAlchemyJobStore(url="sqlite:///jobs.db"),
}

scheduler = BackgroundScheduler(jobstores=jobstores)


def parse_time_from_str(time_str: str) -> int:
    """
    Parse a time string in various formats (e.g., "HH:MM", "HH MM", "HHMM")
    and return the total number of seconds since midnight.
    """
    try:
        # Match formats like "12:00", "12 00", or "1200"
        match = re.match(r"^(\d{1,2})[:\s]?(\d{2})$", time_str)
        if not match:
            raise ValueError("Invalid time format")

        hours, minutes = map(int, match.groups())
        if 0 <= hours < 24 and 0 <= minutes < 60:
            return hours * 3600 + minutes * 60
        else:
            raise ValueError("Invalid time format")

    except ValueError:
        raise ValueError("Invalid time format")


def start_scheduler():
    """
    Start the scheduler.
    """
    scheduler.start()
