from datetime import datetime, date

import pytz

DEFAULT_TIMEZONE = "America/New_York"


def get_timezone_aware_date(timezone: str = DEFAULT_TIMEZONE) -> date:
    timezone = DEFAULT_TIMEZONE if timezone is None else timezone
    try:
        tz_obj = pytz.timezone(timezone)
    except pytz.exceptions.UnknownTimeZoneError:
        print(f"Got unknown timezone: {timezone}")
        tz_obj = pytz.timezone(DEFAULT_TIMEZONE)

    return datetime.now(tz=tz_obj).date()
