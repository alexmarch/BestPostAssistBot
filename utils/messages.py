from datetime import datetime

from utils import format_date
from utils.scheduler import parse_schedule_string


def get_confirm_auto_repeat_message(
    state_data: dict,
    time_frames_list: list,
    title: str = "<b>✅ ♻️ Подтвердите зацикленый пост:</b>",
) -> str:
    total_posts = 0
    auto_repeat_dates = state_data.get("auto_repeat_dates", [])
    formated_dates = [format_date(date_str) for date_str in auto_repeat_dates]
    now = datetime.now()
    hour, minute = now.hour, now.minute
    # end of the day hour, minute

    end_of_day_hour, end_of_day_minute = 23, 59
    text_message = f"{title}\n\n"
    index = 0
    datetime_start, datetime_end = None, None

    for _time_interval in time_frames_list:

        _type, interval = parse_schedule_string(_time_interval)

        date_index = 0

        for date_str in formated_dates:
            if _type == "cron":
                next_time = f"{interval.get('hour'):02d}:{interval.get('minute'):02d}"
                total_posts += 1
            else:
                if (
                    index >= len(time_frames_list) - 1
                    and date_index == len(formated_dates) - 1
                ):  # last interval
                    hour = end_of_day_hour - interval.get("hours", 0)
                    minute = end_of_day_minute - interval.get("minutes", 0)
                else:
                    hour = hour + interval.get("hours", 0)
                    minute = minute + interval.get("minutes", 0)

                if hour >= 24:
                    hour = hour % 24
                if minute >= 60:
                    minute = minute % 60
                # No need to convert hour or minute to string here; use formatting below

                # calculate total posts depending on interval
                next_time = f"{hour:02d}:{minute:02d}"

            if index == 0 and date_index == 0:
                text_message += f"<b>Дата отправки:</b> <i>{date_str} {next_time}</i>\n"
                # parse date string to datetime object and save as datetime_start
                datetime_start = datetime.strptime(
                    f"{date_str} {next_time}", "%d %a. %B %Y %H:%M"
                )
            elif (
                index >= len(time_frames_list) - 1
                and date_index == len(formated_dates) - 1
            ):
                text_message += (
                    f"<b>Дата окончания:</b> <i>{date_str} {next_time}</i>\n"
                )
                datetime_end = datetime.strptime(
                    f"{date_str} {next_time}", "%d %a. %B %Y %H:%M"
                )
            date_index += 1
        index += 1

        # calculate total time from datetime_start to datetime_end
        if datetime_start and datetime_end and _type != "cron":
            # to seconds
            hours = interval.get("hours", 0) * 3600
            minutes = interval.get("minutes", 0) * 60

            total_posts += int(
                (datetime_end - datetime_start).total_seconds() // (hours + minutes)
            )
    text_message += f"<b>Всего:</b> <i>{total_posts}</i> <b>постов</b> \n\n"
    return text_message
