import datetime


def transform_str_to_datetime(str_datetime):
    """
    :param str_datetime: datetime object as string in different formats
    :return: datetime object in equal format for all incoming string formats
    """
    if type(str_datetime) is str:
        try:
            datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            try:
                datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f')
            except:
                try:
                    datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%d %H:%M:%S')
                    except:
                        try:
                            datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f%z')
                        except:
                            try:
                                datetime_obj = datetime.datetime.fromisoformat(str_datetime)
                            except:
                                raise Exception('Error in datetime transformation!')
    else:
        datetime_obj = str_datetime  # str_datetime is already right datetime format
    return datetime_obj

def datetime_to_rounded_str(dt: datetime, ndigits=2):
    """
    Return datetime object as HH:MM:SS.xx
    """
    seconds = dt.second + dt.microsecond / 1_000_000
    rounded_seconds = round(seconds, ndigits)

    sec_int = int(rounded_seconds)
    frac = rounded_seconds - sec_int

    hh = dt.hour
    mm = dt.minute
    ss = f"{sec_int + frac:.{ndigits}f}"

    return f"{hh:02d}:{mm:02d}:{ss}"


def env_to_bool(text: str) -> bool:
    value = text.strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid boolean for: {text}")
