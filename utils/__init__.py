import locale
import re
from datetime import datetime, time

from models import get_session
from repositories.post_repository import PostRepository


def format_date(date_str: str, _locale: str = "ru_RU.UTF-8") -> str:
    """
    Format a date string from "DD/MM/YYYY" to a 23 Пт. Май 2023
    """
    try:
        # Parse the date string into a datetime object
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        # Set the locale for formatting
        locale.setlocale(locale.LC_TIME, _locale)
        return dt.strftime("%d %a. %B %Y").title()
    except ValueError as e:
        raise ValueError(f"Invalid date format: {e}") from e


def parse_time(time_str: str) -> time:
    # Remove any non-numeric characters (like spaces or colons)
    cleaned = re.sub(r"\D", "", time_str)

    if len(cleaned) == 4:  # HHMM format
        return datetime.strptime(cleaned, "%H%M").time()
    elif len(cleaned) == 2:  # HH format
        return datetime.strptime(cleaned, "%H").time()
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def parse_button(button_str: str) -> str:
    """
    Parse button string
      Название - ссылка
        or
      Название - ссылка|Название - ссылка
    """
    # Split the string by '|'
    buttons = button_str.split("|")
    parsed_buttons = []

    for button in buttons:
        # Split each button by '-'
        parts = button.split("-")
        if len(parts) == 2:
            name = parts[0].strip()
            url = parts[1].strip()
            parsed_buttons.append(f"{name} - {url}")
        else:
            raise ValueError(f"Invalid button format: {button}")

    return "|".join(parsed_buttons)


from .scheduler import create_remove_post_jod
