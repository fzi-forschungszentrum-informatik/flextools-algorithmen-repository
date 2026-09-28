from typing import List
import logging
import numpy as np

import config.config_file
from api.client_api import get_possible_amrs, get_travel_time_matrix, get_nodes_for_order, \
    set_order_update, set_reposition_order, check_start_and_goal_are_connected
from api.client_api_models import OrderUpdateRequest, OrderDimensionRequest, \
    TravelTimeMatrixRequest, NodeInfoRequest, AssignedOrderUpdateRequest, RepositionOrder, TokensEndPositionsRequest
from api.server_api_models import NewOrderInfo, StoredOrderInfo
from data.enums import OrderStatus
from data.models import ActionIdCounter, Order, Node, NodePosition, SystemStateAMR
from interfaces.task_assignment_interface import TaskAssignment
from logic.api_services.general_task_assignment_functions import transform_order_info_to_order, setup_ttm

logger = logging.getLogger(config.config_file.LOGGER_NAME)


class TokenPassing(TaskAssignment):
    def __init__(self, action_id_counter: ActionIdCounter):
        self.stored_orders = {}
        self.action_id_counter = action_id_counter
        self.ttm_layouts = {}
        self.ttm = None
        self.reposition_order_id = 1

    def dispatch(self, new_order_info: NewOrderInfo):
        """
        :param new_order_info: info about new order
        :return: add new order to order pool, where amr's can request orders
        """
        # get order from new_order_info object
        order = transform_order_info_to_order(new_order_info, action_id=self.action_id_counter.nextActionId).dict()
        self.stored_orders[order['orderId']] = StoredOrderInfo(order=order, orderInfo=new_order_info, assigned=False)
        self.action_id_counter.nextActionId += 2

        planned_order_update = OrderUpdateRequest(amrId=None,
                                                  order=order,
                                                  index=None,
                                                  estimatedStartTime=None,
                                                  estimatedEndTime=None
                                                  )
        return planned_order_update

    def request_order_from_amr(self, amr_id: str, amr_states: List[SystemStateAMR]):
        """
        :param amr_id: requested amr
        :param amr_states: states
        :return: dispatched order
        :algorithm: token passing
        :changes: check connection start and goal order row 72
        """
        logger.info(f'Requested  Order from amr {amr_id} for order')
        current_order = (None, np.inf)  # (order_id, distance to pickup)
        # get all amr states with tokens
        for amr in amr_states:  # Get amr state from considered amr
            while 'Event' in amr.token:
                amr.token.remove('Event')
            if amr.amrState.amrId == amr_id:
                amr_state = amr
                # set amr_state variable amr state information of considered amr
                break
        for stored_order_id in self.stored_orders.keys():  # For all orders from the order pool, filter order
            if self.stored_orders[stored_order_id].orderInfo.layoutId not in self.ttm_layouts.keys():  # Load ttm
                self.ttm_layouts[self.stored_orders[stored_order_id].orderInfo.layoutId] = setup_ttm(
                    get_travel_time_matrix(TravelTimeMatrixRequest(
                        mapId=self.stored_orders[stored_order_id].orderInfo.layoutId)).json())
            # set ttm used for dispatch order
            self.ttm = self.ttm_layouts[self.stored_orders[stored_order_id].orderInfo.layoutId]
            if self.stored_orders[stored_order_id].assigned is True:
                continue
            consider_next_order = False
            token_goal_position = []
            for considered_amr in amr_states:  # For all other AMRs
                if considered_amr.amrState.amrId == amr_id:
                    continue
                logger.debug(str(f'AMR {considered_amr.amrState.amrId} with end position' + considered_amr.token[-1]
                                 + 'check consider next order, with start ' +
                                 self.stored_orders[stored_order_id].orderInfo.sourceId +
                                 ' and goal' + self.stored_orders[stored_order_id].orderInfo.sinkId))
                token_goal_position.append(considered_amr.token[-1])  # Last position current planned way/token
                if considered_amr.token[-1] == self.stored_orders[stored_order_id].orderInfo.sourceId or \
                        considered_amr.token[-1] == self.stored_orders[stored_order_id].orderInfo.sinkId:
                    consider_next_order = True
                    # Consider next order if last position of one token from the other AMRs is the start or
                    # goal position of the considered order, then order is not executable without collisions
            if consider_next_order is False:  # EXTRA to Token-Passing!!!
                # Check that no other token endpoint disconnect the start and the gaol location of the considered order
                response = check_start_and_goal_are_connected(token_end_position=TokensEndPositionsRequest(
                    nodeIds=token_goal_position, layoutId=self.stored_orders[stored_order_id].orderInfo.layoutId,
                    start=self.stored_orders[stored_order_id].orderInfo.sourceId,
                    goal=self.stored_orders[stored_order_id].orderInfo.sinkId)).json()
                if response['isConnected'] is False:
                    consider_next_order = True

            if consider_next_order is False:  # Order in filtered set
                order_dimension = OrderDimensionRequest(x=self.stored_orders[stored_order_id].orderInfo.dimension.x,
                                                        y=self.stored_orders[stored_order_id].orderInfo.dimension.y,
                                                        z=self.stored_orders[stored_order_id].orderInfo.dimension.z,
                                                        weight=self.stored_orders[stored_order_id].orderInfo.dimension.weight)
                capable_amrs = get_possible_amrs(order_dimension).json()  # request possible amr's to process order
                if amr_id in capable_amrs:
                    # Load system state amr
                    logger.debug(f'Last node amr {amr_id} {amr_state.amrState.lastNodeId}')
                    current_distance_to_pickup = self.ttm[(amr_state.amrState.lastNodeId,
                                                           self.stored_orders[stored_order_id].order.nodes[0].nodeId)]
                    if current_distance_to_pickup is float('inf'):
                        continue
                    if current_distance_to_pickup < current_order[1]:
                        current_order = (self.stored_orders[stored_order_id].order.orderId, current_distance_to_pickup)
            else:
                continue

        if current_order[0] is None:  # filtered order set is empty, no order to process
            token_goal_positions = []  # list of token goal position for all amr's without requested amr for order
            for considered_amr in amr_states:
                if considered_amr.amrState.amrId == amr_id:
                    continue
                token_goal_positions.append(considered_amr.token[-1])
            agent_position_ok = True  # Check if agent position is okay
            for stored_order_id in self.stored_orders.keys():
                if amr_state.amrState.lastNodeId == self.stored_orders[stored_order_id].orderInfo.sinkId:
                    # Agent is in the goal location of another order
                    agent_position_ok = False
                    break
                if agent_position_ok is True:
                    # Remove the agent position node, will disconnect start and goal from another order,
                    # so another order is not executable
                    node_ids_input = token_goal_positions
                    while self.stored_orders[stored_order_id].orderInfo.sourceId in node_ids_input:
                        node_ids_input.remove(self.stored_orders[stored_order_id].orderInfo.sourceId)
                    response = check_start_and_goal_are_connected(token_end_position=TokensEndPositionsRequest(
                        nodeAmr=amr_state.amrState.lastNodeId,
                        nodeIds=node_ids_input,  # and last node id
                        layoutId=self.stored_orders[stored_order_id].orderInfo.layoutId,
                        start=self.stored_orders[stored_order_id].orderInfo.sourceId,
                        goal=self.stored_orders[stored_order_id].orderInfo.sinkId)).json()
                    if response['isConnected'] is False:
                        logger.info('Reposition amr because through the position of this amr the start and goal'
                                    ' location of another order are not more connected')
                        agent_position_ok = False
                        break

            if agent_position_ok is True:
                # Position ok, do nothing
                logger.info(f'Position of Amr {amr_id} is okay. Does not get a new order.')
                return None
            else:
                # plan to go to another location, reposition order
                reposition_order = self.compute_reposition_order(amr_state.amrState.lastNodeId, amr_id, amr_states)
                if reposition_order is None:
                    return None
                set_reposition_order(RepositionOrder(amrId=amr_id, order=reposition_order))
                # Cost minimal Path, delivery locations of the task set are different to the endpoint
                # no paths of other agents in the token ends in the chosen endpoint
                # does not collide with paths from other agents
                logger.info(f'Computed reposition order {reposition_order}')
                return reposition_order
        else:
            # Dispatch selected order to requested amr
            self.stored_orders[current_order[0]].assigned = True
            assigned_order_update_request = AssignedOrderUpdateRequest(amrId=amr_id,
                                                                       orderStatus=OrderStatus.PLANNED,
                                                                       orderId=self.stored_orders[current_order[0]].order.orderId)
            set_order_update(assigned_order_update_request)
            order = self.stored_orders[current_order[0]]
            # del self.stored_orders[current_order[0]] # ToDo only after computing a path
            logger.info(f'Assign Order {order} to AMR {amr_id}')
        return order

    def compute_reposition_order(self, node_id, amr_id, amr_states):
        logger.debug('Compute reposition order')
        filtered_ttm = {(k1, k2): value for (k1, k2), value in self.ttm.items() if k1 == node_id}
        sorted_ttm = {}  # compute sorted ttm with increasing costs
        order = None
        for key in sorted(filtered_ttm, key=filtered_ttm.get):  # sort ttm to distance to considered node
            sorted_ttm[key] = filtered_ttm[key]
        token_goal_positions = []  # token goal positions of all other amr's
        for considered_amr in amr_states:
            if considered_amr.amrState.amrId == amr_id:
                continue
            token_goal_positions.append(considered_amr.token[-1])
        for key, value in sorted_ttm.items():  # For each node in layout, sorted by the closest distance
            # to the current location
            node_not_in_delivery_points = True
            for stored_order_id in self.stored_orders.keys():  # For each stored order
                if self.stored_orders[stored_order_id].orderInfo.sinkId == key[1]:
                    # Check if node not in delivery point of another order
                    node_not_in_delivery_points = False
                    break
                node_ids_input = token_goal_positions
                while self.stored_orders[stored_order_id].orderInfo.sourceId in node_ids_input:
                    node_ids_input.remove(self.stored_orders[stored_order_id].orderInfo.sourceId)
                response = check_start_and_goal_are_connected(token_end_position=TokensEndPositionsRequest(
                    nodeAmr=key[1],
                    nodeIds=node_ids_input,  # and considered position
                    layoutId=self.stored_orders[stored_order_id].orderInfo.layoutId,
                    start=self.stored_orders[stored_order_id].orderInfo.sourceId,
                    goal=self.stored_orders[stored_order_id].orderInfo.sinkId)).json()
                # check is order connected without considered node
                if response['isConnected'] is False:
                    node_not_in_delivery_points = False
                    break
            for considered_amr in amr_states:
                if considered_amr.amrState.amrId == amr_id:
                    continue
                if considered_amr.token[-1] == key[1]:
                    node_not_in_delivery_points = False
                    break
            if node_not_in_delivery_points is True:  # plan reposition order for node which are satisfy constraints
                node_info_request = NodeInfoRequest(nodeIds=[key[0], key[1]],
                                                    layoutId=amr_states[0].amrState.amrPosition.mapId)
                node_response_obj = get_nodes_for_order(node_ids=node_info_request).json()
                node_list = [node for node in node_response_obj['nodes']]
                # create reposition order object
                order = Order(orderId=f'RePo{self.reposition_order_id}', orderUpdateId=0,
                              nodes=[Node(nodeId=key[0], sequenceId=0, released=True,
                                          nodePosition=NodePosition(x=node_list[0]['nodePosition']['x'],
                                                                    y=node_list[0]['nodePosition']['y'],
                                                                    mapId=node_list[0]['nodePosition']['mapId']),
                                          actions=[]),
                                     Node(nodeId=key[1], sequenceId=0, released=True,
                                          nodePosition=NodePosition(x=node_list[1]['nodePosition']['x'],
                                                                    y=node_list[1]['nodePosition']['y'],
                                                                    mapId=node_list[1]['nodePosition']['mapId']),
                                          actions=[])], edges=[])
                self.reposition_order_id += 1
                logger.debug(f'Reposition Order: {order}')
                break
        return order

    def remove_order_from_order_pool(self, order_id: str):
        if order_id in self.stored_orders.keys():
            del self.stored_orders[order_id]
        else:
            raise Exception(f'Error: Order {order_id} not found in order pool!')
        return

    def release_order_again(self, order_id: str):
        if order_id in self.stored_orders.keys():
            self.stored_orders[order_id].assigned = False
        else:
            raise Exception(f'Error: Order {order_id} not found in order pool!')
        return


