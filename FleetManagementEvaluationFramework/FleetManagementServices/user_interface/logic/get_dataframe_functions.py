import pandas as pd

from api.client_api import get_map_info
from data.enums import ActionStatus
from data.models import AMRRequests, OrderInfoRequest
import api.client_api


def get_amr_df(amr_ids='*'):
    """
    :param amr_ids: request info about amr
    :return: dataframe with infos about amr
    """
    amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=[amr_ids])).json()

    if len(amr_data) > 0:
        df_amrs_all_data = pd.DataFrame(amr_data)
        df_amrs = df_amrs_all_data[['amrId', 'lastNodeId', 'driving', 'currentOrder',
                                    'numberOfPlannedOrders', 'pause']].copy()
        if not df_amrs.empty:
            df_amrs.rename(columns={'amrId': 'AMR ID', 'lastNodeId': 'Last Position', 'driving': 'Driving',
                                    'currentOrder': 'Current Order',
                                    'numberOfPlannedOrders': 'Number Planned Orders',
                                    'pause': 'Pause'}, inplace=True)
        df_amrs['Pause'] = df_amrs['Pause'].astype(str)
        df_amrs['Pause'] = df_amrs['Pause'].apply(lambda x: x.replace('false', 'False'))
        df_amrs['Pause'] = df_amrs['Pause'].apply(lambda x: x.replace('true', 'True'))
        df_amrs['Driving'] = df_amrs['Driving'].astype(str)
        df_amrs['Driving'] = df_amrs['Driving'].apply(lambda x: x.replace('false', 'False'))
        df_amrs['Driving'] = df_amrs['Driving'].apply(lambda x: x.replace('true', 'True'))
        return df_amrs
    else:
        return None


def get_orders_df_with_computed_start_and_end_times():
    """
    :return: request infos about orders
    """
    request_body = OrderInfoRequest(orderIds=['*'])
    response = api.client_api.get_order_info(request_body).json()
    df_orders = pd.DataFrame(response)
    if not df_orders.empty:
        df_orders.rename(columns={'orderId': 'Order ID', 'amrId': 'AMR', 'orderStatus': 'Status',
                                  'startTime': 'Start Time',
                                  'dueTime': 'End Time', 'sourceNodeId': 'Source node',
                                  'sinkNodeId': 'Sink node'}, inplace=True)
        df_orders['Start Time'] = df_orders['Start Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))
        df_orders['End Time'] = df_orders['End Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))

        amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=['*'])).json()
        order_id_list = []
        estimated_start_time_list = []
        estimated_end_time_list = []
        for amr in amr_data:
            for planned_order in amr['plannedOrders']:
                order_id_list.append(planned_order['order']['orderId'])
                estimated_start_time_list.append(planned_order['estimatedStartTime'])
                estimated_end_time_list.append(planned_order['estimatedEndTime'])
        for i, order_id in enumerate(order_id_list):
            if estimated_start_time_list[i] is not None:
                df_orders.loc[df_orders['Order ID'] == order_id, 'Start Time'] = estimated_start_time_list[i]
            if estimated_end_time_list[i] is not None:
                df_orders.loc[df_orders['Order ID'] == order_id, 'End Time'] = estimated_end_time_list[i]
        df_orders = df_orders[df_orders['Order ID'].str[0:4] != 'RePo']
        df_orders['Start Time'] = df_orders['Start Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))
        df_orders['End Time'] = df_orders['End Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))
        df_orders = df_orders.sort_values(by="Start Time").reset_index(drop=True)

    return df_orders


def get_df_single_amr(amr_id: str):
    """
    :param amr_id: str
    :return: get information about a single amr
    """
    amr_data = api.client_api.get_amr_data(AMRRequests(amrIds=[amr_id.replace('AMR ', '')])).json()
    df = pd.DataFrame(amr_data)
    df_amr = df[['lastNodeId', 'x', 'y', 'driving', 'currentOrder', 'numberOfPlannedOrders',
                 'connectionState', 'pause']].copy()
    if not df_amr.empty:
        df_amr.rename(columns={'lastNodeId': 'Last Node', 'x': 'X-Pos.', 'y': 'Y-Pos.', 'driving': 'Driving',
                                'currentOrder': 'Current Order',
                                'numberOfPlannedOrders': 'Number Planned Orders', 'connectionState': 'Connection',
                                'pause': 'Pause'}, inplace=True)
    df_amr['Pause'] = df_amr['Pause'].astype(str)
    df_amr['Pause'] = df_amr['Pause'].apply(lambda x: x.replace('false', 'False'))
    df_amr['Pause'] = df_amr['Pause'].apply(lambda x: x.replace('true', 'True'))
    df_amr['Driving'] = df_amr['Driving'].astype(str)
    df_amr['Driving'] = df_amr['Driving'].apply(lambda x: x.replace('false', 'False'))
    df_amr['Driving'] = df_amr['Driving'].apply(lambda x: x.replace('true', 'True'))

    action_id_list = []
    action_type_list = []
    action_status_list = []
    for action in amr_data[0]['actionsCurrentOrder']:
        action_id_list.append(action['actionId'])
        action_type_list.append(action['actionType'])
        action_status_list.append(ActionStatus(action['actionStatus']))

    df_actions = pd.DataFrame({'Action ID': action_id_list, 'Type': action_type_list, 'Status': action_status_list})

    battery_charge = int(amr_data[0]['batteryState']['batteryCharge'])
    charging = amr_data[0]['batteryState']['charging']
    reach = amr_data[0]['batteryState']['reach']

    order_id_list = []
    estimated_start_time_list = []
    estimated_end_time_list = []
    for planned_order in amr_data[0]['plannedOrders']:
        order_id_list.append(planned_order['order']['orderId'])
        estimated_start_time_list.append(planned_order['estimatedStartTime'])
        estimated_end_time_list.append(planned_order['estimatedEndTime'])

    df_planned_orders = pd.DataFrame({'Order ID': order_id_list, 'Estimated Start Time': estimated_start_time_list,
                                      'Estimated End Time': estimated_end_time_list})
    df_planned_orders['Estimated Start Time'] = df_planned_orders[
        'Estimated Start Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))
    df_planned_orders['Estimated End Time'] = df_planned_orders[
        'Estimated End Time'].apply(lambda x: str(x)[0:19].replace('T', ' '))
    return df_amr, df_actions, battery_charge, charging, reach, df_planned_orders


