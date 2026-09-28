import datetime
import time
from typing import List
import logging

import config.config_file
from api.client_api import get_travel_time_matrix, \
    update_planned_order_sequence_in_system_state_management, get_current_system_time
from api.client_api_models import TravelTimeMatrixRequest, OrderUpdateRequest
from api.server_api_models import NewOrderInfo
from config.config_file import MAX_IMPROVEMENT_TIME, BUFFER_TIME_PRO_ORDER
from data.models import SystemStateAMR, Order, OrderSequenceUpdateRequest, PlannedOrderInfo, ActionIdCounter
from interfaces.task_assignment_interface import TaskAssignment
from logic.api_services.general_task_assignment_functions import setup_ttm, load_capable_amrs_state, transform_order_info_to_order, \
    get_general_duration_for_actions_from_order
from logic.api_services.general_functions import transform_str_to_datetime

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class GreedyCompletionTime(TaskAssignment):
    ##########
    # public #
    ##########
    def __init__(self, action_id_counter: ActionIdCounter, use_improvement=config.config_file.USE_IMPROVEMENT,
                 max_time_for_improvement=MAX_IMPROVEMENT_TIME):
        self.improve = False
        self.max_time_for_improvement = max_time_for_improvement
        self.ttm_layouts = {}
        self.ttm = None
        self.action_id_counter = action_id_counter

    def set_use_improvement(self, use_improvement: bool):
        self.improve = use_improvement

    def dispatch(self, new_order_info: NewOrderInfo):
        """
        :param new_order_info: information about new order, which should dispatch to an amr.
        :return: order update request data object, for dispatch the new order to an amr with the lowest costs  at the
         best insertion position between all other orders
        """
        # check and update, if ttm must set up new
        if new_order_info.layoutId not in self.ttm_layouts.keys():
            self.ttm_layouts[new_order_info.layoutId] = setup_ttm(get_travel_time_matrix(
                TravelTimeMatrixRequest(mapId=new_order_info.layoutId)).json())
        # set ttm used for dispatch order
        self.ttm = self.ttm_layouts[new_order_info.layoutId]

        # load states of all considered amr
        state_considered_amrs = load_capable_amrs_state(new_order_info)
        logger.debug(f'New order info: {new_order_info} ')
        # get order from new_order_info object
        order = transform_order_info_to_order(new_order_info, action_id=self.action_id_counter.nextActionId).dict()
        logger.debug(f'Transformed order: {order}')
        self.action_id_counter.nextActionId += 2
        # get the best insertion position and amr
        amr_id, insertion_position, estimated_start_time, estimated_end_time =\
            self.get_greedy_best_insertion(state_considered_amrs, order, new_order_info)

        if amr_id is None:
            logger.exception(f'Error: No feasible solution for order {new_order_info.orderId} '
                             f'found to dispatch order to AMR!')
            # Maybe return None better than raise an exception, because it is possible that order planning can be failed
            raise Exception(f'Error: No feasible solution for order {new_order_info.orderId} '
                            f'found to dispatch order to AMR!')

        logger.info(str(f'Successfully planned best insertion for Order ' + str(order['orderId']) +
                    f' for amr {amr_id} with insertion index {insertion_position}'))

        planned_order_info = PlannedOrderInfo(estimatedStartTime=estimated_start_time,
                                              estimatedEndTime=estimated_end_time,
                                              order=order).dict()

        if not self.improve:
            # No 2-opt improvement
            # Update start and end times of the other orders in the queue
            for amr in state_considered_amrs:
                if amr['amrState']['amrId'] == amr_id:
                    # insert order in planned order list for amr
                    amr['plannedOrders'].insert(insertion_position, planned_order_info)
                    if len(amr['plannedOrders']) > 1:
                        amr['plannedOrders'] = self.update_planned_orders_time(amr['plannedOrders'])
                    update_planned_order_sequence_in_system_state_management(
                        OrderSequenceUpdateRequest(amrId=amr_id, orders=amr['plannedOrders']))

            ###################################################
            logger.info(str(f'Order ' + str(order['orderId']) + f' successfully dispatched for amr {amr_id}'))
        else:
            # stage best insertion
            # execute 2-opt optimization
            for amr in state_considered_amrs:
                if amr['amrState']['amrId'] == amr_id:
                    logger.debug(f"Start optimizing order sequence for amr {amr_id}")
                    amr['plannedOrders'].insert(insertion_position, planned_order_info)
                    # Search improvements with 2-opt
                    amr['plannedOrders'], optimization_found = self.optimize_by_swapping(amr['plannedOrders'])
                    if len(amr['plannedOrders']) > 1:
                        # Update planned order times
                        amr['plannedOrders'] = self.update_planned_orders_time(amr['plannedOrders'])
                    if optimization_found is True:
                        order_id_sequence_list = []
                        for planned_oder in amr['plannedOrders']:
                            order_id_sequence_list.append(planned_oder['order']['orderId'])
                        logger.info(f'Optimization found with 2-opt!')
                        logger.info(f'New order sequence: {order_id_sequence_list}')
                    update_planned_order_sequence_in_system_state_management(
                        OrderSequenceUpdateRequest(amrId=amr_id, orders=amr['plannedOrders']))
            logger.info(str(f'Order ' + str(order['orderId']) + f' successfully dispatched for amr {amr_id}'))

        planned_order_update = OrderUpdateRequest(amrId=amr_id,
                                                  order=order,
                                                  index=insertion_position,
                                                  estimatedStartTime=estimated_start_time,
                                                  estimatedEndTime=estimated_end_time
                                                  )

        return planned_order_update

    def get_greedy_best_insertion(self, state_considered_amrs: List[SystemStateAMR], order: Order,
                                  order_info: NewOrderInfo) -> (str, int, datetime, datetime):
        """
        :param state_considered_amrs: system states of considered amr's
        :param order: new order object
        :param order_info: order info data
        :return: get the insertion position for the new order in the planned order list,
                for the amr with the lowest insertion cost
        """
        order_buffer_time = get_general_duration_for_actions_from_order(order, buffer_time=BUFFER_TIME_PRO_ORDER)
        best_insertion = (None, None,  datetime.datetime(2100,12, 31), None, None)
        # amr_id, insertion_position, best_insertion_costs, estimated_start_time, estimated_end_time
        # For all amr's
        for amr in state_considered_amrs:
            # evaluation for all insertion positions except from push back position
            for insertion_position in range(1, len(amr['plannedOrders'])):
                end_node_id_predecessor = amr['plannedOrders'][insertion_position - 1]['order']['nodes'][-1]['nodeId']
                start_node_order_id = order['nodes'][0]['nodeId']
                end_node_order_id = order['nodes'][-1]['nodeId']
                start_node_id_successor = amr['plannedOrders'][insertion_position]['order']['nodes'][0]['nodeId']
                # compute insertion costs
                insertion_costs = (self.ttm[(end_node_id_predecessor, start_node_order_id)]
                                   + self.ttm[(end_node_order_id, start_node_id_successor)]
                                   - self.ttm[(end_node_id_predecessor, start_node_id_successor)])
                if insertion_costs is float('inf'):
                    continue
                # compute estimated start- and end time order
                estimated_end_time_previous_order = (
                    transform_str_to_datetime(amr['plannedOrders'][insertion_position - 1]['estimatedEndTime']))
                estimated_start_time = max(order_info.startTime, estimated_end_time_previous_order)
                estimated_end_time = (estimated_start_time + datetime.timedelta(
                    seconds=(self.ttm[(end_node_id_predecessor, start_node_order_id)] + self.ttm[(start_node_order_id,
                                                                                                  end_node_order_id)]))
                                      + order_buffer_time)
                number_upcoming_orders = (len(amr['plannedOrders']) - insertion_position)
                # Shift time other orders end time through insert the order on this position
                shift_time = ((estimated_end_time - estimated_start_time) +
                              datetime.timedelta(seconds=insertion_costs)) * number_upcoming_orders
                if estimated_end_time + shift_time < best_insertion[2] and estimated_end_time <= order_info.dueTime:
                    best_insertion = (amr['amrState']['amrId'], insertion_position, estimated_end_time + shift_time,
                                      estimated_start_time, estimated_end_time)

            # evaluation of push back position
            if len(amr['plannedOrders']) == 0:
                end_node_id_predecessor = amr['amrState']['lastNodeId']
                start_node_order_id = order['nodes'][0]['nodeId']
                end_node_order_id = order['nodes'][-1]['nodeId']
                insertion_costs = self.ttm[(end_node_id_predecessor, start_node_order_id)]
                if insertion_costs is float('inf'):
                    continue
                estimated_start_time_system_time = (
                    transform_str_to_datetime(get_current_system_time().json()['timestamp']))

                estimated_start_time = max(order_info.startTime,
                                           estimated_start_time_system_time.replace(tzinfo=None))
                estimated_end_time = (estimated_start_time + datetime.timedelta(
                    seconds=(self.ttm[(end_node_id_predecessor, start_node_order_id)]+self.ttm[(start_node_order_id,
                                                                                                end_node_order_id)]))
                                      + order_buffer_time)
            else:  # insert order after last node
                end_node_id_predecessor = amr['plannedOrders'][-1]['order']['nodes'][-1]['nodeId']
                start_node_order_id = order['nodes'][0]['nodeId']
                end_node_order_id = order['nodes'][-1]['nodeId']
                insertion_costs = self.ttm[(end_node_id_predecessor, start_node_order_id)]
                estimated_start_time = transform_str_to_datetime(amr['plannedOrders'][-1]['estimatedEndTime'])
                estimated_start_time = max(order_info.startTime, estimated_start_time)
                estimated_end_time = (estimated_start_time + datetime.timedelta(
                    seconds=(self.ttm[(end_node_id_predecessor, start_node_order_id)] + self.ttm[(start_node_order_id,
                                                                                                  end_node_order_id)]))
                                      + order_buffer_time)
            # No shift time, because no more order at the end
            if estimated_end_time < best_insertion[2] and estimated_end_time <= order_info.dueTime:
                best_insertion = (amr['amrState']['amrId'], len(amr['plannedOrders']), estimated_end_time,
                                  estimated_start_time, estimated_end_time)

        return (best_insertion[0], best_insertion[1], best_insertion[3], best_insertion[4])

    def optimize_by_swapping(self, currently_planned_orders):
        '''
        Swapping is a 2-opt move for route planning. More information can be found at https://en.wikipedia.org/wiki/2-opt

        :param currently_planned_orders: sequence of orders currently stored in systemstatemanagement including new order
        :return: improved sequence of orders
        '''
        optimization_found = False
        num_current_orders = len(currently_planned_orders)
        planned_orders = list(currently_planned_orders)
        if num_current_orders > 1:
            found_improvement = True
            start_time = time.time()
            elapsed = time.time() - start_time
            while found_improvement and round(elapsed) < self.max_time_for_improvement:
                found_improvement = False
                for i in range(0, num_current_orders-1):
                    break_loop = False
                    for j in range(i+2, num_current_orders):  # Never j = i+1, it doesn't make sense!!!
                        indices = [i, j]
                        if indices[1] == num_current_orders - 1:
                            travel_time_delta_for_swapping = (
                                    - self.ttm[(planned_orders[indices[0]]['order']['nodes'][-1]['nodeId'],
                                                planned_orders[indices[0] + 1]['order']['nodes'][0]['nodeId'])]
                                    # Minus way from considered order i end to start of next order in order sequence
                                    + self.ttm[(planned_orders[indices[0]]['order']['nodes'][-1]['nodeId'],
                                                planned_orders[indices[1]]['order']['nodes'][0]['nodeId'])]
                                    # Plus way from considered order i end to start considered order j
                                    + self.ttm[(planned_orders[indices[1]]['order']['nodes'][-1]['nodeId'],
                                                planned_orders[indices[0] + 1]['order']['nodes'][0]['nodeId'])]
                                    # Plus way from considered order j end to start of next order i in order sequence
                                    - self.ttm[(planned_orders[indices[1]]['order']['nodes'][0]['nodeId'],
                                                planned_orders[indices[1] - 1]['order']['nodes'][-1]['nodeId'])])
                                    # Minus way from considered order j start to end of previous order j
                            if travel_time_delta_for_swapping is float('inf'):
                                continue
                        else:
                            travel_time_delta_for_swapping = (
                                        - self.ttm[(planned_orders[indices[0]]['order']['nodes'][-1]['nodeId'],
                                                    planned_orders[indices[0] + 1]['order']['nodes'][0]['nodeId'])]
                                        # Minus way from considered order i end to start of next order in order sequence
                                        - self.ttm[(planned_orders[indices[1]]['order']['nodes'][-1]['nodeId'],
                                                    planned_orders[indices[1] + 1]['order']['nodes'][0]['nodeId'])]
                                        # Minus way from considered order j end to start of next order in order sequence
                                        + self.ttm[(planned_orders[indices[0]]['order']['nodes'][-1]['nodeId'],
                                                    planned_orders[indices[1]]['order']['nodes'][0]['nodeId'])]
                                        # Plus way from considered order i end to start considered order j
                                        + self.ttm[(planned_orders[indices[1]]['order']['nodes'][-1]['nodeId'],
                                                    planned_orders[indices[0] + 1]['order']['nodes'][0]['nodeId'])]
                                        # Plus way from considered order j end to start of next order i in order sequence
                                        - self.ttm[(planned_orders[indices[1]]['order']['nodes'][0]['nodeId'],
                                                    planned_orders[indices[1] - 1]['order']['nodes'][-1]['nodeId'])]
                                        # Minus way from considered order j start to end of previous order j
                                        + self.ttm[(planned_orders[indices[1] - 1]['order']['nodes'][-1]['nodeId'],
                                                    planned_orders[indices[1] + 1]['order']['nodes'][0]['nodeId'])])
                                        # Plus way from previous order j end to start of next order j in order sequence
                            if travel_time_delta_for_swapping is float('inf'):
                                continue
                        if travel_time_delta_for_swapping < 0:
                            planned_orders = (planned_orders[:(indices[0] + 1)] + [planned_orders[indices[1]]] +
                                              planned_orders[(indices[0] + 1):indices[1]] +
                                              planned_orders[(indices[1] + 1):])
                            found_improvement = True
                            break_loop = True
                            optimization_found = True
                            break

                    if break_loop:
                        break

                elapsed = time.time()-start_time

        return planned_orders, optimization_found

    def update_planned_orders_time(self, planned_orders: List[PlannedOrderInfo]):
        """
        :param planned_orders: List of planned order infos
        :return: Planned order lis, with updated times
        """
        for index, order in enumerate(planned_orders[:-1]):
            planned_orders[index + 1]['estimatedStartTime'] = (
                transform_str_to_datetime(planned_orders[index + 1]['estimatedStartTime']))
            planned_orders[index + 1]['estimatedEndTime'] = (
                transform_str_to_datetime(planned_orders[index + 1]['estimatedEndTime']))
            planned_orders[index]['estimatedEndTime'] = (
                transform_str_to_datetime(planned_orders[index]['estimatedEndTime']))
            if planned_orders[index + 1]['estimatedStartTime'] < planned_orders[index]['estimatedEndTime'] or \
                    planned_orders[index + 1]['estimatedStartTime'] > planned_orders[index]['estimatedEndTime']:
                duration_way = 0
                start_node_predecessor = planned_orders[index]['order']['nodes'][-1]['nodeId']
                for node in planned_orders[index + 1]['order']['nodes']:
                    duration_way += self.ttm[(start_node_predecessor, node['nodeId'])]
                    start_node_predecessor = node['nodeId']
                estimated_order_duration = (datetime.timedelta(seconds=duration_way) +
                                            get_general_duration_for_actions_from_order(
                                                order=planned_orders[index + 1]['order']))
                planned_orders[index + 1]['estimatedStartTime'] = planned_orders[index]['estimatedEndTime']
                planned_orders[index + 1]['estimatedEndTime'] = (planned_orders[index + 1]['estimatedStartTime'] +
                                                                 estimated_order_duration)

        return planned_orders
