import re
from datetime import datetime, time

def parse_time(time_str: str) -> time:
    # Remove any non-numeric characters (like spaces or colons)
    cleaned = re.sub(r'\D', '', time_str)

    if len(cleaned) == 4:  # HHMM format
        return datetime.strptime(cleaned, "%H%M").time()
    elif len(cleaned) == 2:  # HH format
        return datetime.strptime(cleaned, "%H").time()
    else:
        raise ValueError(f"Invalid time format: {time_str}")
