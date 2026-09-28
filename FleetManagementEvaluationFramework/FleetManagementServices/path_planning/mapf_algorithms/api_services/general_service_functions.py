from typing import List
import time
import copy
import logging
import ast
import math

import mapf_algorithms
import config.config_file

from api.server_api_models import Token, RoutingRequestObject
from data.enums import PathPlanningStrategy
from data.models import Order, Node
from mapf_algorithms.api_services.service_processing_functions import get_constraints_from_tokens

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def get_node_infos_node_id(node_id: str, layout_id: str) -> Node:
    """
    :param node_id: node identification
    :param layout_id: layout identification
    :return:  get the node object from the layout information file
    """
    node_object = None
    for node in mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts[layout_id].nodes:
        if node.nodeId == node_id:
            node_object = node
    if node_object is None:
        logger.exception(f'No node information found for node {node_id}')
        raise Exception(f'No node information found for node {node_id}')
    return node_object


def get_relevant_node_sequence_for_order(amr_position: Node, orders: List[Order]):
    """
    :param amr_position: Last position of the amr
    :param orders: The new order
    :return: List of relevant nodes for the new order
    """
    node_sequence_for_order = []
    node_sequence_for_order.append(amr_position.nodeId)
    for order in orders:
        for node in order.nodes:
            node_sequence_for_order.append(node.nodeId)
    return node_sequence_for_order


def get_relevant_node_sequence(routing_object: RoutingRequestObject):
    """
    :param routing_object: RoutingRequestObject
    :return: Method to get relevant nodes dictionary for routing from current location to pickup and delivery
             location for all amr
    """
    node_sequences_amrs = {}
    if routing_object.planOrderIds is not None:
        new_plan_order_ids = routing_object.newOrderIds + routing_object.planOrderIds
    else:
        new_plan_order_ids = routing_object.newOrderIds
    # Already started amr by tokens and new order by orders
    for index, route_request in enumerate(routing_object.routingAMR):
        node_sequence_for_order = []
        node_sequence_for_order.append(route_request.lastNodeId)
        if route_request.order.orderId in new_plan_order_ids:
            for node in route_request.order.nodes:
                node_sequence_for_order.append(node.nodeId)
        else:
            if config.config_file.PATH_PLANNING_STRATEGY == 'multi_agent_path_planning':
                while 'Event' in route_request.token.tokens:
                    node_sequence_for_order.append(route_request.token.tokens[
                                                       route_request.token.tokens.index('Event') - 1])
                    del route_request.token.tokens[0:route_request.token.tokens.index('Event') + 1]
        node_sequences_amrs[route_request.amrId] = node_sequence_for_order
    return node_sequences_amrs


def get_node_sequence_for_orders_for_all_amr(tokens: List[Token], amr_id, node_sequence_for_order: List[str]):
    """
    :param tokens: Tokens of each amr, the current planned path
    :param amr_id: Amr id of considered amr which should process the new order
    :param node_sequence_for_order:  List of relevant nodes for the new order
    :return: dict{amr_id: List[relevant_nodes]}
    """
    node_sequences_orders_amrs = {}
    # Set all other node sequences for already planned orders depend of the path planning strategy
    if config.config_file.PATH_PLANNING_STRATEGY == 'multi_agent_path_planning':
        for token in tokens:
            if token.amrId == amr_id:
                continue
            else:
                relevant_node_list = []
                relevant_node_list.append(token.tokens[0])  # current position
                while 'Event' in token.tokens:
                    relevant_node_list.append(token.tokens[token.tokens.index('Event') - 1])
                    del token.tokens[0:token.tokens.index('Event') + 1]
                node_sequences_orders_amrs[token.amrId] = relevant_node_list
    # Node sequence for new order independent of the path planning strategy
    node_sequences_orders_amrs[amr_id] = node_sequence_for_order
    logger.info(f'Orders AMRs relevant nodes: {node_sequences_orders_amrs}')
    return node_sequences_orders_amrs


def compute_shortest_paths_for_multi_agent_system(tokens: List[Token], node_sequences_orders_amrs, constraints_outside,
                                                  layout_id: str):
    """
    :param tokens: Tokens of each amr, the current planned path
    :param node_sequences_orders_amrs: dict{amr_id: List[relevant_nodes]}
    :param layout_id: layout identification
    :return: set of shortest paths to process the planned orders order update the transmitted orders
            1. Loop for path planning around multi_agent_path_planning for computing path between the first two relevant nodes of all amr
            2. After planing a path for a segment of the total path update the relevant node dictionary
            3. Termination condition satisfied if the len of relevant node for all amr is one.
    """
    overall_shortest_paths = [[] for i in range(len(node_sequences_orders_amrs))]  # Empty list of all paths AMR 1, 2, 3

    event_nodes = []
    for amr in node_sequences_orders_amrs.keys():
        event_nodes.append(node_sequences_orders_amrs[amr][1:])
    logger.debug(f'Event nodes: {event_nodes}')
    terminate_time = time.monotonic()
    elapsed = time.monotonic() - terminate_time
    terminate = False
    while terminate is False and round(elapsed) < config.config_file.MAX_TIME_ROUTING:
        # Start loop online optimization
        # Get constraints and tokens in dependence of the selected path planning strategy
        constraints, token_list = get_relevant_tokens_and_constraints(overall_shortest_paths, tokens,
                                                                      constraints_outside,
                                                                      next(iter(node_sequences_orders_amrs)))
        # Get node sequence of relevant nodes for all amrs
        logger.info(f'Relevant node sequence orders: {node_sequences_orders_amrs}')
        start_node_id_list, end_node_id_list = get_start_and_goal_nodes_for_routing(node_sequences_orders_amrs)
        # end_node_id_list = check_start_and_end_node_ids(start_node_id_list, end_node_id_list, layout_id)
        end_node_id_list = check_start_and_end_node_ids(end_node_id_list, layout_id)
        # Normally not necessary
        start_node_id_list = check_start_and_end_node_ids(start_node_id_list, layout_id)
        if end_node_id_list is None:
            raise Exception('Error: No other goal found close to node to get a solution for path planning!')
        # Start computing path and measure computational time
        start_time = time.monotonic()
        logger.info(f'Start node ids: {start_node_id_list}, Goals: {end_node_id_list}')
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_path_planning_requests += 1
        paths, costs, _ = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].compute_path(
            layout_id=layout_id,
            start_node_ids=start_node_id_list,
            end_node_ids=end_node_id_list,
            constraints=constraints,
            tokens=token_list
        )
        if paths is None:
            logger.info(f'No path found with {config.config_file.PATH_PLANNING_STRATEGY}!')
            mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].number_of_failed_path_computations += 1
            return None

        computational_time = time.monotonic() - start_time
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].computational_time += computational_time

        node_sequence_orders_copy = copy.deepcopy(node_sequences_orders_amrs)
        # Update node sequence of orders with computed path
        node_sequence_orders_copy = update_node_sequence_for_termination_check(node_sequence_orders_copy, paths)
        # check terminate condition
        terminate = check_terminate_condition(node_sequence_orders_copy)

        if terminate is True:
            # If termination is true, update rest of the total path
            for i, path in enumerate(paths):
                if len(path) != 0 and len(overall_shortest_paths[i]) > 0:
                    del path[0]
                overall_shortest_paths[i] += path
                if overall_shortest_paths[i][-1] != 'Event':
                    overall_shortest_paths[i].append('Event')
        else:
            min_path_length_list = get_min_path_length(node_sequences_orders_amrs,
                                                       paths)
            if len(min_path_length_list) == 0:
                logger.info(f'No path found with {config.config_file.PATH_PLANNING_STRATEGY}!')
                mapf_algorithms.core.path_planning_init.path_planning_strategies[
                    config.config_file.PATH_PLANNING_STRATEGY].number_of_failed_path_computations += 1
                return None
            min_path_length = min(min_path_length_list)
            logger.debug(f'Min path length: {min_path_length}')
            shortest_path = []
            for i, path in enumerate(paths):
                shortest_path.append(path[:min_path_length])
                shift = 0
                if len(path) != 0 and len(overall_shortest_paths[i]) > 0:
                    del path[0]
                    shift = 1
                logger.debug(str(f'Index {i} with overall shortest path ' + str(overall_shortest_paths[i]) +
                                 ' add path ' + str(path[:min_path_length-shift])))
                overall_shortest_paths[i] += path[:min_path_length-shift]
                if overall_shortest_paths[i][-1] in event_nodes[i]:
                    overall_shortest_paths[i].append('Event')
            # Update node sequence of orders with computed path
            node_sequences_orders_amrs = update_node_sequence_orders_with_computed_path(node_sequences_orders_amrs,
                                                                                        shortest_path)

            logger.info(f'Overall shortest paths after Iteration: {overall_shortest_paths}')

        elapsed = time.monotonic() - terminate_time
        logger.debug(f'Time: {elapsed}')

    if elapsed > config.config_file.MAX_TIME_ROUTING:
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_failed_path_computations += 1
        return None

    if elapsed > config.config_file.REAL_TIME_ROUTING_THRESHOLD:
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_exceed_routing_time_threshold += 1
    logger.info(f'Optimal paths for all agents: {overall_shortest_paths}')
    return overall_shortest_paths


def transform_multi_agent_paths_to_node_and_edge_objects(overall_shortest_paths: List[List[str]], orders: List[Order],
                                                         layout_id: str):
    """
    :param overall_shortest_paths: List of paths for each amr
    :param orders: List of current orders for all amr`s
    :param layout_id: layout identification
    :return: transform list of node ids to a route object with a list of node and edge objects. Additionally
             considered actions in nodes for orders and compute sequence id
    """
    route_nodes_list = []
    route_edges_list = []
    for j, shortest_path in enumerate(overall_shortest_paths):
        node_list = []
        edge_list = []
        sequence_id = 0
        for i, node_id in enumerate(shortest_path[:-1]):  # Last Item is Event
            add_node = False
            if node_id == 'Event':
                continue
            elif shortest_path[i + 1] == 'Event':
                if j == len(overall_shortest_paths) - 1:  # For computing only on path
                    index = -1
                else:
                    index = j
                for order_node in orders[index].nodes:
                    if node_id == order_node.nodeId and len(order_node.actions) > 0:
                        order_node.sequenceId = copy.deepcopy(sequence_id)
                        sequence_id += 1
                        node_list.append(copy.deepcopy(order_node))
                        add_node = True
                        break
                if add_node is False:  # For empty order, amr stay at last position
                    for node in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                            config.config_file.PATH_PLANNING_STRATEGY].layouts[layout_id].nodes:
                        if node.nodeId == node_id:
                            node.sequenceId = copy.deepcopy(sequence_id)
                            sequence_id += 1
                            node_list.append(copy.deepcopy(node))
                            break
            else:
                for node in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                        config.config_file.PATH_PLANNING_STRATEGY].layouts[layout_id].nodes:
                    if node.nodeId == node_id:
                        node.sequenceId = copy.deepcopy(sequence_id)
                        sequence_id += 1
                        node_list.append(copy.deepcopy(node))
                        break

            if node_id == shortest_path[i+1]:
                # add no edge to edge list
                continue
            elif shortest_path[i+1] == 'Event':
                if i + 2 < len(shortest_path) - 1:
                    if shortest_path[i+2] == node_id:
                        # add no edge to edge list
                        continue
                    if shortest_path[i + 2] != node_id:
                        for edge in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                                config.config_file.PATH_PLANNING_STRATEGY].layouts[layout_id].edges:
                            if (edge.startNodeId == node_id and edge.endNodeId == shortest_path[i + 2]):
                                edge.sequenceId = copy.deepcopy(sequence_id)
                                sequence_id += 1
                                edge_list.append(copy.deepcopy(edge))
                                break
                            elif (edge.endNodeId == node_id and edge.startNodeId == shortest_path[i + 2] and
                                        config.config_file.DIRECTED_GRAPH is False):
                                edge.startNodeId = copy.deepcopy(node_id)
                                edge.endNodeId = copy.deepcopy(shortest_path[i + 2])
                                edge.sequenceId = copy.deepcopy(sequence_id)
                                sequence_id += 1
                                edge_list.append(copy.deepcopy(edge))
                                break
            else:
                for edge in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                        config.config_file.PATH_PLANNING_STRATEGY].layouts[layout_id].edges:
                    if (edge.startNodeId == node_id and edge.endNodeId == shortest_path[i + 1]):
                        edge.sequenceId = copy.deepcopy(sequence_id)
                        sequence_id += 1
                        edge_list.append(copy.deepcopy(edge))
                        break
                    elif (edge.endNodeId == node_id and edge.startNodeId == shortest_path[i + 1] and
                                  config.config_file.DIRECTED_GRAPH is False):
                        edge.startNodeId = copy.deepcopy(node_id)
                        edge.endNodeId = copy.deepcopy(shortest_path[i + 1])
                        edge.sequenceId = copy.deepcopy(sequence_id)
                        sequence_id += 1
                        edge_list.append(copy.deepcopy(edge))
                        break
        if len(node_list) > 1:
            node_list_with_theta = compute_theta_for_node_list_of_route(node_list)
            route_nodes_list.append(node_list_with_theta)
        else:
            route_nodes_list.append(node_list)

        route_edges_list.append(edge_list)
    logger.debug(f'Route node list: {route_nodes_list}')
    logger.debug(f'Route edge list: {route_edges_list}')
    return route_nodes_list, route_edges_list


def compute_theta_for_node_list_of_route(node_list: List[Node]):
    """
    :param node_list: List[Node] from computed route
    :return: List[Node] with computed theta degree for rotation on the nodes
    """
    new_node_list = []
    for index, node in enumerate(node_list):
        if index == len(node_list) - 2:
            # second last element, it follows degree computation for the last both nodes
            if node.nodeId != node_list[index + 1].nodeId:
                theta = compute_theta_for_rotation_on_nodes(node, node_list[index + 1])
                node.nodePosition.theta = copy.deepcopy(theta)
                new_node_list.append(copy.deepcopy(node))
                next_node = node_list[index + 1]
                next_node.nodePosition.theta = copy.deepcopy(theta)
                new_node_list.append(copy.deepcopy(next_node))
            else:
                next_node = node_list[index + 1]
                if len(new_node_list) > 0:
                    theta = copy.deepcopy(new_node_list[-1].nodePosition.theta)
                    node.nodePosition.theta = copy.deepcopy(theta)
                    next_node.nodePosition.theta = copy.deepcopy(theta)
                # Else don't specify theta parameter, it is not important
                new_node_list.append(copy.deepcopy(node))
                new_node_list.append(copy.deepcopy(next_node))
            break
        else:
            if node.nodeId != node_list[index+1].nodeId:
                theta = compute_theta_for_rotation_on_nodes(node, node_list[index+1])
                node.nodePosition.theta = copy.deepcopy(theta)
                new_node_list.append(copy.deepcopy(node))
            else:
                if len(new_node_list) > 0:
                    theta = copy.deepcopy(new_node_list[-1].nodePosition.theta)
                    node.nodePosition.theta = copy.deepcopy(theta)
                # Else don't specify theta parameter, it is not important
                new_node_list.append(copy.deepcopy(node))

    return new_node_list


def compute_theta_for_rotation_on_nodes(node_start: Node, node_end: Node):
    """
    :param node_start: start node position
    :param node_end: end node position
    :return: Compute rotation radiant for rotate on start node to drive over edge in the direction of the end node.
    """
    logger.debug(f'Compute degree with start node {node_start.nodePosition} and end node {node_end.nodePosition}')
    if node_start.nodePosition.x == 0:
        theta = math.atan2(node_end.nodePosition.y, node_end.nodePosition.x)
    else:
        theta = math.atan2(node_end.nodePosition.y-node_start.nodePosition.y,
                           node_end.nodePosition.x-node_start.nodePosition.x)
    logger.debug(f'Computed theta {theta}')
    return theta


def get_start_and_goal_nodes_for_routing(node_sequences_orders_amrs: dict):
    """
    :param node_sequences_orders_amrs: dict{amr_id: List[relevant_nodes]}
    :return: List of start and goal node ids for all amr`s based on the relevant nodes of the amr's and the orders
    """
    start_node_id_list = []
    end_node_id_list = []
    for amr in node_sequences_orders_amrs.keys():
        start_node_id_list.append(node_sequences_orders_amrs[amr][0])
        if len(node_sequences_orders_amrs[amr]) > 1:
            end_node_id_list.append(node_sequences_orders_amrs[amr][1])
        else:
            end_node_id_list.append(node_sequences_orders_amrs[amr][0])
    logger.debug(f'Start computing route with {start_node_id_list} and goals {end_node_id_list}')
    return start_node_id_list, end_node_id_list


def get_relevant_tokens_and_constraints(overall_shortest_paths: List[List[str]], tokens: List[Token],
                                        constraints_from_outside, amr_id):
    """
    :param overall_shortest_paths: List of path for each amr
    :param tokens: Tokens of each amr, the current planned path
    :param constraints_from_outside: Constraints from outside.
    :return: initialize tokens and constraints based of the selected path planning strategy
    """
    if config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cooperative_a_star:
        logger.info(f'Tokens for cooperative A-Star: {tokens}')
        token_without_events = copy.deepcopy(tokens)
        for token in token_without_events:
            while 'Event' in token.tokens:
                token.tokens.remove('Event')

        time_steps = len(overall_shortest_paths[0]) - overall_shortest_paths[0].count('Event') - 1
        # Time steps -1 because is the computed path length 1, the amr don't move and stay on the same position,
        # so the time steps for constraints shouldn't increase
        constraints = get_constraints_from_tokens(token_without_events, amr_id, len_path=max(time_steps, 0))
        logger.info(f'Constraints for cooperative A-Star: {constraints}')
        token_list = [token.tokens[min(time_steps, len(token.tokens) - 1):] for token in token_without_events if
                      token.amrId != amr_id]
    elif (config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.dijkstra or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.cbs_djs or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.ecbs_djs or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_ecbs or
          config.config_file.PATH_PLANNING_STRATEGY == PathPlanningStrategy.i_cbs):

        if constraints_from_outside is None:
            constraints = None
        else:
            constraints = constraints_from_outside
        token_list = []
    else:
        constraints = None
        token_list = []
    return constraints, token_list


def check_terminate_condition(node_sequence_orders_copy: dict) -> bool:
    """
    :param node_sequence_orders_copy: dict{amr_id: List[relevant_nodes]}
    :return: boolean, true if the length of the relevant nodes for all amr`s equal to one
    """
    # check terminate condition
    for amr in node_sequence_orders_copy.keys():
        if len(node_sequence_orders_copy[amr]) > 1:
            return False
    return True


def update_node_sequence_orders_with_computed_path(node_sequence_orders: dict, paths: List[List[str]]):
    """
    :param node_sequence_orders: dict{amr_id: List[relevant_nodes]}
    :param paths: List of path for each amr
    :return: updated node_sequence_orders list, which removed relevant nodes which are already on the paths
    """
    # Remove relevant nodes from node sequence order list, if path satisfy the routing points
    logger.debug(f'Paths in update node sequence: {paths}')
    for i, amr, in enumerate(node_sequence_orders.keys()):
        if node_sequence_orders[amr][0] == paths[i][0]:
            if len(node_sequence_orders[amr]) > 1:
                if node_sequence_orders[amr][1] == paths[i][-1]:
                    del node_sequence_orders[amr][0]
                else:
                    node_sequence_orders[amr][0] = paths[i][-1]
    logger.info(f'Updated relevant node sequence: {node_sequence_orders}')
    return node_sequence_orders


def update_node_sequence_for_termination_check(node_sequence_orders: dict, paths: List[List[str]]):
    """
    :param node_sequence_orders: dict{amr_id: List[relevant_nodes]}
    :param paths: List of path for each amr
    :return: updated node_sequence_orders list, which removed relevant nodes which are already on the paths
    """
    # Remove relevant nodes from node sequence order list, if path satisfy the routing points
    logger.debug(f'Paths in update node sequence for termination: {paths}')
    for i, amr, in enumerate(node_sequence_orders.keys()):
        if node_sequence_orders[amr][0] == paths[i][0]:
            if len(node_sequence_orders[amr]) > 1:
                if node_sequence_orders[amr][1] == paths[i][-1]:
                    del node_sequence_orders[amr][0]
                else:
                    node_sequence_orders[amr][0] = paths[i][-1]
    logger.debug(f'Updated relevant node sequence in termination check: {node_sequence_orders}')
    return node_sequence_orders


def get_min_path_length(node_sequence_orders: dict, paths: List[List[str]]):
    """
    :param node_sequence_orders: Current node sequence of relevant nodes
    :param paths: computed paths
    :return: min path length to next event node
    """
    min_path_length = []
    for i, amr, in enumerate(node_sequence_orders.keys()):
        if node_sequence_orders[amr][0] == paths[i][0]:
            if len(node_sequence_orders[amr]) > 1:
                if node_sequence_orders[amr][1] == paths[i][-1]:
                    min_path_length.append(len(paths[i]))
                elif node_sequence_orders[amr][1] in paths[i]:
                    min_path_length.append(paths[i].index(node_sequence_orders[amr][1]) + 1)
    return min_path_length


def check_start_and_end_node_ids(end_node_id_list: List[str], layout_id: str):
    """
    :param end_node_id_list: List[str]
    :param layout_id: str
    :return: List[str], which different node ids for resolvability
    """
    end_node_id_list_new = []
    for node in end_node_id_list:
        if node not in end_node_id_list_new:
            end_node_id_list_new.append(node)
        else:
            new_node_id = search_closest_node_which_is_not_in_end_node_id_list(node, end_node_id_list_new, layout_id)
            end_node_id_list_new.append(new_node_id)
    return end_node_id_list_new


def search_closest_node_which_is_not_in_end_node_id_list(node_id, end_node_id_list, layout_id: str):
    ttm = \
    mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].travel_time_matrix[
        layout_id].ttm
    filtered_ttm = {ast.literal_eval(k): v for k, v in ttm.items() if ast.literal_eval(k)[0] == node_id}
    sorted_ttm = {k: v for k, v in sorted(filtered_ttm.items(), key=lambda item: item[1][0])}
    for key, value in sorted_ttm.items():
        if key[1] not in end_node_id_list:
            return key[1]
    return None


def get_token_list(routing_request: RoutingRequestObject):
    token_list = []
    for route_obj in routing_request.routingAMR:
        token_list.append(route_obj.token)
    return token_list


def get_order_list(routing_request: RoutingRequestObject):
    order_list = []
    for route_obj in routing_request.routingAMR:
        order_list.append(route_obj.order)
    return order_list


def update_token_list(token_list: List[Token], path: List[str], amr_id: str):
    """
    :param token_list: List[Token]
    :param path: List[str]
    :param amr_id: str
    :return: method to update token with computed path
    """
    new_token_list = []
    for token in token_list:
        if token.amrId == amr_id:
            token.tokens = path
        new_token_list.append(token)
    return new_token_list


