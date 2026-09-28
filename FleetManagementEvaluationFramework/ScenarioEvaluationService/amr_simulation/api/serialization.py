import datetime


def serialize_json(obj):
    if isinstance(obj, datetime.datetime):
        return str(obj)
    else:
        return obj.dict(exclude_none=True)
