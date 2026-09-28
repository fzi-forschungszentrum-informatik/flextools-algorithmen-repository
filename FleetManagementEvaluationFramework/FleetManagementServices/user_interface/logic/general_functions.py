import datetime

from api.client_api import get_map_info
from data.enums import OrderStatus
from data.models import OrderInfoRequest
import api.client_api


def safe_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def get_order_span():
    """
    :return: Compute min and max parameter to request makespan in statistics evaluation service
    """
    response = api.client_api.get_order_info(OrderInfoRequest(orderIds=['*'])).json()
    for item in response:
        if item['orderId'][:4] == 'RePo':
            response.remove(item)

    if len(response) > 1:
        order_start_id = None
        order_end_id = None

        # Erste FINISHED Order suchen
        for item in response:
            if OrderStatus(item['orderStatus']) == OrderStatus.FINISHED:
                order_start_id = safe_int(item['orderId'])
                if order_start_id is not None:
                    break

        # Letzte FINISHED Order suchen
        for item in reversed(response):
            if OrderStatus(item['orderStatus']) == OrderStatus.FINISHED:
                order_end_id = safe_int(item['orderId'])
                if order_end_id is not None:
                    break
    else:
        order_start_id = None
        order_end_id = None
    return order_start_id, order_end_id


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


def env_to_bool(text: str) -> bool:
    value = text.strip().lower()
    if value in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "f", "no", "n", "off"}:
        return False

    raise ValueError(f"Invalid boolean for: {text}")


