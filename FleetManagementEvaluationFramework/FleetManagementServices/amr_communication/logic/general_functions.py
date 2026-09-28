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
                                raise Exception(f'Error: In datetime transformation!')
    else:
        datetime_obj = str_datetime  # str_datetime is already in the right datetime format
    return datetime_obj


def env_to_bool(text: str) -> bool:
    value = text.strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid boolean for: {text}")