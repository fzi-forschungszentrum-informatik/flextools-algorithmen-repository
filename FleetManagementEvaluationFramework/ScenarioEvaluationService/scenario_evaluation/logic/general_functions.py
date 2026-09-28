import datetime


def transform_str_to_datetime(str_datetime):
    if type(str_datetime) is str:
        try:
            datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            try:
                datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S')
            except:
                try:
                    datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%fZ')
                except:
                    try:
                        datetime_obj = datetime.datetime.strptime(str_datetime, '%Y-%m-%dT%H:%M:%S.%f%z')
                    except:
                        try:
                            datetime_obj = datetime.datetime.fromisoformat(str_datetime)
                        except:
                            raise Exception('Error in datetime transformation!')
    else:
        datetime_obj = str_datetime  # str_datetime is already datetime
    return datetime_obj
