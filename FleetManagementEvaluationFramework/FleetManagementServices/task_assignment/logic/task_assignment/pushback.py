import datetime
from typing import List
import logging

import numpy as np

import config.config_file
from api.client_api import get_travel_time_matrix, set_planned_order_in_system_state_management, get_current_system_time
from api.client_api_models import TravelTimeMatrixRequest, OrderUpdateRequest
from api.server_api_models import NewOrderInfo
from config.config_file import BUFFER_TIME_PRO_ORDER
from data.models import SystemStateAMR, Order, ActionIdCounter
from interfaces.task_assignment_interface import TaskAssignment
from logic.api_services.general_task_assignment_functions import setup_ttm, load_capable_amrs_state, transform_order_info_to_order, \
    get_general_duration_for_actions_from_order
from logic.api_services.general_functions import transform_str_to_datetime

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class PushBack(TaskAssignment):
    ##########
    # public #
    ##########
    def __init__(self, action_id_counter: ActionIdCounter):
        self.ttm_layouts = {}
        self.ttm = None
        self.action_id_counter = action_id_counter

    def dispatch(self, new_order_info: NewOrderInfo):
        """
        :param new_order_info: information about new order, which should dispatch to an amr.
        :return: order update request data object, for dispatch the new order to an amr with the lowest cost at the
                 end of the planned order list.
        """
        # check and update, if ttm must set up new
        if new_order_info.layoutId not in self.ttm_layouts.keys():
            self.ttm_layouts[new_order_info.layoutId] = setup_ttm(get_travel_time_matrix(
                TravelTimeMatrixRequest(mapId=new_order_info.layoutId)).json())
        # set ttm used for dispatch order
        self.ttm = self.ttm_layouts[new_order_info.layoutId]

        # load states of all considered amr
        state_considered_amrs = load_capable_amrs_state(new_order_info)

        # get order from new_order_info object
        order = transform_order_info_to_order(new_order_info, action_id=self.action_id_counter.nextActionId)
        # update action_id counter with plus two, for pickup and delivery action
        self.action_id_counter.nextActionId += 2
        # get the amr that is closest to the start node of the order
        (state_closest_amr, reference_node_amr, estimated_start_time, estimated_end_time) =\
            self.get_closest_amr_final_position(state_considered_amrs, order, new_order_info)
        if reference_node_amr is None:
            logger.exception(f'Error: No feasible solution for order {new_order_info.orderId} '
                             f'found to dispatch order to AMR!')
            # Maybe return None better than raise an exception, because it is possible that order planning can be failed
            raise Exception(f'Error: No feasible solution for order {new_order_info.orderId} '
                            f'found to dispatch order to AMR!')
        closest_amr_id = state_closest_amr['amrState']['amrId']

        # send planned order to system_state_management
        planned_order_update = OrderUpdateRequest(amrId=closest_amr_id,
                                                  order=order,
                                                  index=len(state_closest_amr['plannedOrders']),
                                                  estimatedStartTime=estimated_start_time,
                                                  estimatedEndTime=estimated_end_time)
        set_planned_order_in_system_state_management(planned_order_update)
        ###################################################
        logger.info(f"Order {order.orderId} successfully planned for amr {closest_amr_id} at time {estimated_start_time}")
        response = planned_order_update
        return response

    def get_closest_amr_final_position(self, considered_amrs: List[SystemStateAMR], order: Order,
                                       order_info: NewOrderInfo) -> (SystemStateAMR, str, datetime, datetime):
        start_position_order_map = order.nodes[0].nodePosition.mapId
        order_buffer_time = get_general_duration_for_actions_from_order(order.dict(), buffer_time=BUFFER_TIME_PRO_ORDER)

        # INITIALIZE TUPLE FOR CLOSEST AMR
        closest_amr = (None, None, datetime.timedelta(hours=1000000), None, None)
        # Tuple(amr_state, reference_node_id, duration to start position order,
        #       estimated_start_time, estimated_end_time)
        for amr in considered_amrs:
            logger.info(f'Check Order Assignment AMR: {amr}')
            if amr['amrState']['amrPosition']['mapId'] == start_position_order_map:  # only if amr uses same map
                if len(amr['plannedOrders']) != 0:
                    reference_node_id = amr['plannedOrders'][-1]['order']['nodes'][-1]['nodeId']
                    estimated_start_time = transform_str_to_datetime(amr['plannedOrders'][-1]['estimatedEndTime'])
                else:
                    reference_node_id = amr['amrState']['lastNodeId']
                    estimated_start_time = transform_str_to_datetime(get_current_system_time().json()['timestamp'])

                estimated_start_time = max(order_info.startTime.replace(tzinfo=None), estimated_start_time.replace(tzinfo=None))
                logger.info(f'Check Order Assignment estimated Start Time: {estimated_start_time}')
                duration_amr_pickup = self.ttm[(reference_node_id, order.nodes[0].nodeId)]
                logger.info(f'Check Order Assignment Duration Pickup: {duration_amr_pickup}')
                if duration_amr_pickup is np.inf:
                    continue
                duration_pickup_dropoff = self.ttm[(order.nodes[0].nodeId, order.nodes[-1].nodeId)]
                logger.info(f'Check Order Assignment Duration Pickup Dropoff: {duration_pickup_dropoff}')
                if duration_pickup_dropoff is np.inf:
                    continue
                duration_total = (datetime.timedelta(seconds=(duration_amr_pickup + duration_pickup_dropoff))
                                  + order_buffer_time)
                end_time = estimated_start_time + duration_total
                logger.info(f'Check Order Assignment Duration Total: {duration_total}, End Time: {end_time}')
                # Second term for check feasibility of solution
                if duration_total < closest_amr[2] and end_time <= order_info.dueTime.replace(tzinfo=None):
                    logger.info('Order Assignment feasible')
                    closest_amr = (amr, reference_node_id, duration_total, estimated_start_time, end_time)

        return closest_amr[0], closest_amr[1], closest_amr[3], closest_amr[4]
        # closest amr and reference node id as a predecessor for insertion and estimated start and end time

