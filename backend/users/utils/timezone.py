from datetime import timezone as dt_timezone, tzinfo

import pytz


from users.models import User


def get_user_timezone(user: User) -> tzinfo:
    try:
        return pytz.timezone(user.timezone)
    except pytz.UnknownTimeZoneError:
        return dt_timezone.utc
