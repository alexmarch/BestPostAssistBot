from datetime import datetime

from aiogram.utils.formatting import BlockQuote

from utils import format_date
from utils.scheduler import parse_schedule_string


def get_notify_update_version_message() -> str:
    return (
        "<b>🚀 ОБНОВЛЕНИЕ</b> бота!\n\n"
        "<b>Мы</b> стали ещё лучше 💪\n\n"
        "Что <b>нового:</b>\n\n"
        "🐞 <b>Иссправлены ошибка:</b> добавления новой задачи на рассылку\n"
        "🐞 <b>Иссправлены ошибка:</b> выбора канала/чата в момент создания поста\n"
        "🐞 <b>Иссправлены ошибка:</b> поведения UI элементов формы\n"
        "🐞 <b>Иссправлены ошибка:</b> уведомления пользователя о доставке\n"
        "⭐ <b>Обновленный календарь с мультивыбором</b>\n"
        "⭐ <b>Доработан UI/UX</b>\n"
        "⭐ <b>Автоповтор/Зацикленность</b>\n\n"
        "✨ <b>Опробуйте</b> обновлённого бота прямо сейчас 🚀\n"
    )


def get_multiposting_message(time_frames: list) -> str:
    return f"""
<b>🗓 Расписание</b>\n\n
Здесь можно установить ежедневное расписание постов в режиме мультипостинга, чтобы в дальнейшем планировать публикации всего одним кликом сразу в несколько каналов.\n
Чтобы задать расписание, отправь время выхода постов в виде списка в любом удобном формате.\n
🕒 <b>Публикация по времени</b>(отправте время в любом из форматов):\n
{BlockQuote("12:00 - Опубликуется в 12:00\n12 00 - Опубликуется в 12:00\n1200 - Опубликуется в 12:00\n12 00, 15 00, 18 00 - Опубликуется в 12:00, 15:00, 18:00").as_html()}\n
🕒 <b>Настройка интервалов выхода постов:</b>\n
{BlockQuote('30m - Опубликуется каждые 30 минут\n12h - Опубликуется каждые 12 часов\n1h 30m - Опубликуется каждый 1 часа 30 минут').as_html()}\n
⚠️ <b>ВАЖНО!</b> Минимальное время автоповтора/зацикленности 15m (минут)\n
{ '⏰ <b>Текущее расписание публикации:</b>\n' if time_frames else "" }
<i>{"\n".join(time_frames) if time_frames else ""}</i>\n
"""


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
                    and index > 0
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

        # if not datetime_end and len(formated_dates) == 1:
        #     # create date end in 23:59 of the last date
        #     datetime_end = datetime.strptime(
        #         f"{formated_dates[-1]} {end_of_day_hour:02d}:{end_of_day_minute:02d}",
        #         "%d %a. %B %Y %H:%M",
        #     )
        #     f_datetime_end = datetime_end.strftime("%d %a. %B %Y %H:%M")
        #     text_message += f"<b>Дата окончания:</b> <i>{f_datetime_end}</i>\n"
        #     print("datetime_end", datetime_end)

        # calculate total time from datetime_start to datetime_end
        if datetime_start and datetime_end and _type != "cron":
            # to seconds
            hours = interval.get("hours", 0) * 3600
            minutes = interval.get("minutes", 0) * 60

            total_posts += int(
                (datetime_end - datetime_start).total_seconds() // (hours + minutes)
            )

        elif datetime_start and _type != "cron":
            # if only datetime_start is set, calculate total posts for the last interval
            hours = interval.get("hours", 0) * 3600
            minutes = interval.get("minutes", 0) * 60
            # dadatetime_end should be 23:59:59
            datetime_end = datetime.strptime(
                f"{formated_dates[-1]} {end_of_day_hour:02d}:{59}",
                "%d %a. %B %Y %H:%M",
            )
            print("datetime_end", datetime_end)
            total_posts += int(
                (datetime_end - datetime_start).total_seconds() // (hours + minutes)
            )
            text_message += f"<b>Дата окончания:</b> <i>Зацикленно</i>\n"

    text_message += f"<b>Всего:</b> <i>{total_posts}</i> <b>постов</b> \n\n"
    return text_message
