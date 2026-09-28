import json
import datetime

from api.client_api import get_system_time, send_new_order_info_to_simulation, send_new_order_info, \
    set_system_time_from_extern_in_system_state_management, set_system_time_from_extern_in_amr_simulation
from api.client_api_models import NewOrderInfo, Dimension, SystemTimeResponse
from config.evaluation_config import ORDER_SCENARIO_FILE
from data.enums import OrderStatus
from logic.general_functions import transform_str_to_datetime
from logic.help_functions import get_next_order_id

import config.config_file


def init_scenario_with_orders(configs=None):
    if configs is None:
        f = open(ORDER_SCENARIO_FILE, "r")
        data = json.load(f)
        f.close()
    else:
        f = open(configs.get_orders_file(), "r")
        data = json.load(f)
        f.close()

    if 'publishTime' in data[0].keys():
        publish_time = transform_str_to_datetime(data[0]['publishTime'])
        set_system_time_from_extern_in_system_state_management(SystemTimeResponse(timestamp=publish_time))
        set_system_time_from_extern_in_amr_simulation(SystemTimeResponse(timestamp=publish_time))
    sys_time = get_system_time().json()
    system_time = transform_str_to_datetime(sys_time['timestamp'])
    next_order_id = get_next_order_id()

    for i, order in enumerate(data):
        if 'publishTime' in order.keys():
            publish_time_order = transform_str_to_datetime(order['publishTime'])
            publish_time = max(publish_time_order, system_time)
        else:
            publish_time = system_time

        start_time_order = transform_str_to_datetime(order['startTime'])
        due_time_order = transform_str_to_datetime(order['dueTime'])
        duration_order = due_time_order - start_time_order

        start_time = max(start_time_order, publish_time + datetime.timedelta(hours=1))
        due_time = start_time + duration_order

        new_order_info = NewOrderInfo(orderId=next_order_id, sourceId=order['sourceId'],
                                      sinkId=order['sinkId'],
                                      startTime=start_time, dueTime=due_time,
                                      publishTime=publish_time,
                                      layoutId=order['layoutId'],
                                      pickupTime=order['pickupTime'], dropoffTime=order['dropoffTime'],
                                      dimension=Dimension(x=order['dimension']['x'], y=order['dimension']['y'],
                                                          z=order['dimension']['z'],
                                                          weight=order['dimension']['weight']),
                                      status=OrderStatus.NEW)
        if config.config_file.SIMULATION_ACTIVE is True:
            send_new_order_info_to_simulation(new_order_info)
        else:
            send_new_order_info(new_order_info)
        next_order_id = str(int(next_order_id) + 1)

    return next_order_id
