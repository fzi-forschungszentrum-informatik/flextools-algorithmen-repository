import os
import copy
import logging
import time

import numpy as np

import mapf_algorithms

from api.client_api import reset_order_management, reset_dispatching, \
    reset_base_data_management, reset_system_state_management

from api.server_api_models import SetTravelTimeRequest, TravelTimeMatrixRequest, NodeInfoRequest, NodesResponse, \
    MapInfoRequest, MapResponse, RouteResponse, PathPlanningStrategy, PathRequest, \
    StationInfoRequest, StationInfoResponse, RoutingForOrdersRequest, TokensEndPositionsRequest, GraphConnectedInfo, \
    ComputationalTimeResponse, LIFObject, EdgeDurationResponse, MapIdResponse, RoutingStartGoalRequest, \
    RoutingRequestObject, HeuristicRequest, CBSImprovementRequest, ParkingNodesRequest, StatisticTimeDataResponse, \
    SetParkingNodesRequest, LayoutInformation, DurationEdgeRequest, PathPlanningTestRequest, FocalHeuristicRequest, \
    PathPlanningRequest
from data.models_lif_file_generator import LIFFile

import data.enums
import config.config_file
from mapf_algorithms.api_services.general_service_functions import get_node_infos_node_id, \
    get_relevant_node_sequence_for_order, get_node_sequence_for_orders_for_all_amr, \
    compute_shortest_paths_for_multi_agent_system, transform_multi_agent_paths_to_node_and_edge_objects, \
    get_relevant_node_sequence, get_token_list, get_order_list, update_token_list
from mapf_algorithms.api_services.service_processing_functions import post_process_paths
from mapf_algorithms.core.path_planning_obj import PathPlanningObj
from mapf_algorithms.core.path_planning_init import path_planning_strategies
from mapf_algorithms.methods.class_selection import get_path_planning_interface, get_heuristic_interface
from tests.random_lif_generator.lif_show import show_lif_animated2, show_lif_animated

logger = logging.getLogger(config.config_file.LOGGER_NAME)


def service_travel_time_matrix(request_body: TravelTimeMatrixRequest):
    response = mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].get_travel_time_matrix(request_body)
    return response


def service_set_travel_time(request_body: SetTravelTimeRequest):
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].set_travel_time(request_body)
    return


def service_get_node_infos(request_body: NodeInfoRequest):
    """
    :param request_body: list of node and station ids
    :return: Node objects of all requested node ids and all node objects the first interaction node id of
     each requested station
    """
    node_id_list = []
    for node_id in request_body.nodeIds:  # Add interaction node id from station to requested node id list
        if node_id[0] == 'S':
            for station in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                    config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.layoutId].stations:
                if station.stationId == node_id:
                    node_id_list.append(station.interactionNodeIds[0])  # At the moment take always first node
        else:
            node_id_list.append(node_id)
    node_list = []
    for node_id in node_id_list:  # Get node information
        for node in mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].layouts[
                request_body.layoutId].nodes:
            if node_id == node.nodeId:
                node_list.append(node)
    return NodesResponse(nodes=node_list)


def service_get_map_info(request_body: MapInfoRequest):
    """
    :param request_body: MapInfoRequest
    :return: Service to get information about the layout
    """
    if request_body.mapId in mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts.keys():
        # Get all nodes, edges and stations from the environment of the requested layout
        nodes = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.mapId].nodes
        edges = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.mapId].edges
        stations = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.mapId].stations
    else:
        raise Exception(f'Error: Layout {request_body.mapId} not in Layouts.')
    return MapResponse(nodes=nodes, edges=edges, stations=stations)


def service_compute_routes(request_body: RoutingForOrdersRequest):
    """
    Currently not used routing request for order response of state updates
    :param request_body:
    :return:
    """
    logger.info(f'Compute Routes order {request_body.orders} , tokens: {request_body.tokens}')
    # 1. get infos from current amr location node
    last_node_amr = get_node_infos_node_id(request_body.lastNodeAmrId, request_body.mapId)
    # 2. set sequence of nodes for order
    # Only the last order is relevant for the new incoming order node sequence
    node_sequence_for_order = get_relevant_node_sequence_for_order(last_node_amr, [request_body.orders[-1]])
    # 3. Get node sequence of orders list for all AMRs, depends on path planning strategy
    node_sequences_orders_amrs = get_node_sequence_for_orders_for_all_amr(
        tokens=request_body.tokens,
        amr_id=request_body.amrId,
        node_sequence_for_order=node_sequence_for_order)
    # 4. compute shortest path for all nodes in the sequence for the order
    overall_shortest_paths = compute_shortest_paths_for_multi_agent_system(
        tokens=request_body.tokens,
        node_sequences_orders_amrs=node_sequences_orders_amrs,
        layout_id=request_body.mapId,
        constraints_outside=None)

    if overall_shortest_paths is None:
        return [RouteResponse(nodes=[], edges=[])]

    # 5. Optional post-process path to avoid cycles
    if config.config_file.PATH_POST_PROCESSING is True:
        overall_shortest_paths = post_process_paths(overall_shortest_paths)

    # 6. shortest path str to node and edge objects
    route_nodes_list, route_edges_list = transform_multi_agent_paths_to_node_and_edge_objects(
        overall_shortest_paths=overall_shortest_paths,
        orders=request_body.orders,
        layout_id=request_body.mapId)

    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].print_current_computational_time()
    route_response = []
    for i, item in enumerate(route_nodes_list):
        route_response.append(RouteResponse(nodes=item, edges=route_edges_list[i]))
    return route_response


def service_set_path_planning_strategy(request_body: PathPlanningStrategy):
    """
    :param request_body: PathPlanningStrategy
    :return: Service to select used path planning strategy
    """
    if request_body.pathPlanningStrategy not in mapf_algorithms.core.path_planning_init.path_planning_strategies.keys():
        layouts = mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].layouts
        graph = mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].graph
        exgraph = mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].exgraph
        graph_with_stations = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph_with_stations
        travel_time_matrix = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].travel_time_matrix
        heuristic = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].heuristic
        config.config_file.PATH_PLANNING_STRATEGY = data.enums.PathPlanningStrategy(request_body.pathPlanningStrategy)
        if request_body.boundary is not None:
            config.config_file.OPTIMALITY_BOUND = request_body.boundary
        if request_body.heuristic is not None:
            config.config_file.ECBS_HEURISTIC = data.enums.ECBSHeuristic(request_body.heuristic)

        # Set path planning parameter
        # restart travel_time class with right interface
        path_planning_interface = get_path_planning_interface()
        heuristic_interface = heuristic
        mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY] = PathPlanningObj(
            os.environ['LIF_FILE'], path_planning_interface, heuristic_interface)
        mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].layouts = layouts
        mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].graph = graph
        mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY].exgraph = exgraph
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph_with_stations = graph_with_stations
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].travel_time_matrix = travel_time_matrix
    config.config_file.PATH_PLANNING_STRATEGY = data.enums.PathPlanningStrategy(request_body.pathPlanningStrategy)
    return


def service_set_lif_file(request_body: PathRequest):
    config.config_file.SCENARIO_LIF_FILE = request_body.path  # Set LIF-file parameter
    os.environ['LIF_FILE'] = request_body.path  # Set environment variable
    # restart travel_time class with right LIF-file
    path_planning_interface = get_path_planning_interface()
    heuristic_interface = get_heuristic_interface()
    mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY] = PathPlanningObj(
        request_body.path, path_planning_interface, heuristic_interface)
    return


def service_set_lif_object(request_body: LIFObject):
    """
    :param request_body: LIFObject
    :return: Method to set Layout according the Layout Interchange Format
    """
    # Update Layout with LIF object request
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].set_layout(request_body)
    return


def service_get_stations_info(request_body: StationInfoRequest):
    """
    :param request_body: StationInfoRequest
    :return: Get Information about the stations in the considered layout
    """
    # Get information about the stations in the environment of the LIF-file
    response = []
    for station_id in request_body.stationIds:
        for station in mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.layoutId].stations:
            if station_id == station.stationId:
                response.append(StationInfoResponse(stationId=station_id,
                                                    interactionNodes=station.interactionNodeIds))
    return response


def service_get_info_graph_connected(request_body: TokensEndPositionsRequest):
    """
    :param: node_ids: list of node ids
    :param: layout_id
    :param: start
    :param: goal
    :return: boolean, check if start and goal of the graph from layout_id is connected after removing some node ids
    """
    if config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.cbs:
        return GraphConnectedInfo(isConnected=True)
    graph = copy.deepcopy(mapf_algorithms.core.path_planning_init.path_planning_strategies[
                                config.config_file.PATH_PLANNING_STRATEGY].graph[request_body.layoutId])
    for node in request_body.nodeIds:
        graph.remove_node(node)
    is_connected = graph.are_connected(request_body.start, request_body.goal)
    if request_body.nodeAmr is None:
        return GraphConnectedInfo(isConnected=is_connected)
    else:
        if is_connected is False:
            # Graph is already without the amr position not connected between start and goal,
            # so the amr position is ok
            is_connected = True
        else:
            graph.remove_node(request_body.nodeAmr)
            is_connected = graph.are_connected(request_body.start, request_body.goal)
    return GraphConnectedInfo(isConnected=is_connected)


def service_reset_travel_time():
    # Reset travel time class
    path_planning_interface = get_path_planning_interface()
    heuristic_interface = get_heuristic_interface()
    mapf_algorithms.core.path_planning_init.path_planning_strategies[config.config_file.PATH_PLANNING_STRATEGY] = (
        PathPlanningObj(os.environ['LIF_FILE'], path_planning_interface, heuristic_interface))
    return


def service_reset_time():
    # Reset the measured computational time of the travel time class
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].computational_time = 0
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].number_of_exceed_routing_time_threshold = 0
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].number_of_failed_path_computations = 0
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].number_of_generated_nodes_cbs = 0
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].number_of_path_planning_requests = 0
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].path_planning_time = 0
    return


def service_get_computational_time():
    # get the computational time of the path planning algorithms after the last time reset or initialization
    computational_time = mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].computational_time
    return ComputationalTimeResponse(compTime=computational_time)


def service_get_duration_edge(request_body: MapInfoRequest):
    """
    :param request_body: MapInfoRequest
    :return: request the duration of an edge in the layout
    """
    if request_body.mapId in mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts.keys():
        if len(mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.mapId].edges) > 0:
            edge_length = mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.mapId].edges[0].length
            edge_duration = EdgeDurationResponse(duration=round(edge_length / config.config_file.MAX_SPEED_EDGE, 2))
        else:
            edge_duration = EdgeDurationResponse(duration=1)
    else:
        raise Exception(f'No Layout with map id {request_body.mapId} available')
    return edge_duration


def service_set_lif_file_as_object(request_body: LIFFile):
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].set_lif_object(request_body)
    return


def service_get_current_map_id():
    """
    :return: current map/layout id
    """
    key_list = []
    for key in mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts.keys():
        key_list.append(key)
    if len(key_list) > 0:
        relevant_key = key_list[-1]
    else:
        relevant_key = None
    map_id = MapIdResponse(mapId=relevant_key)
    return map_id


def service_routing_for_all_amr_after_timestep(request_body: RoutingRequestObject):
    """
    Current used routing api
    :param request_body: RoutingRequestObject
    :return: List[routes]
             1. Get relevant node sequence for path planning
             2. Get token and order list
             3. Compute the shortest path depending on the path planning strategy
             4. Transform the shortest path in node and edge objects
    """
    relevant_node_sequence = get_relevant_node_sequence(request_body)
    logger.info(f'relevant node sequence for routing: {relevant_node_sequence}')
    logger.info(f'Constraints for Routing: {request_body.constraints}')
    token_list = get_token_list(request_body)
    orders_list = get_order_list(request_body)

    path_planning_start_time = time.time()
    logger.debug(f'Constraint Outside: {request_body.constraints}')
    if (config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.cbs or
        config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.ecbs or
        config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.cbs_djs or
        config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.ecbs_djs or
        config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.i_cbs or
        config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.i_ecbs):
        overall_shortest_paths = compute_shortest_paths_for_multi_agent_system(
            tokens=token_list,
            node_sequences_orders_amrs=relevant_node_sequence,
            layout_id=request_body.mapId,
            constraints_outside=request_body.constraints)
    elif config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.dijkstra:
        overall_shortest_paths = []
        for amr in relevant_node_sequence.keys():
            shortest_path = compute_shortest_paths_for_multi_agent_system(
                tokens=token_list,
                node_sequences_orders_amrs={amr: relevant_node_sequence[amr]},
                layout_id=request_body.mapId,
                constraints_outside=None)
            overall_shortest_paths.append(shortest_path[0])
    elif config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.cooperative_a_star:
        overall_shortest_paths = []
        for amr in relevant_node_sequence.keys():
            shortest_path = compute_shortest_paths_for_multi_agent_system(
                tokens=token_list,
                node_sequences_orders_amrs={amr: relevant_node_sequence[amr]},
                layout_id=request_body.mapId,
                constraints_outside=None)
            if shortest_path is not None:
                overall_shortest_paths.append(shortest_path[0])
                token_list = update_token_list(token_list, shortest_path[0], amr)
            else:
                overall_shortest_paths.append([])
    else:
        raise Exception('Error: No selected Path planning strategy')

    path_planning_comp_time = time.time() - path_planning_start_time

    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].path_planning_time += path_planning_comp_time

    if overall_shortest_paths is None:
        return [RouteResponse(nodes=[], edges=[])]

    # Transform the shortest paths with node ids to node and edge objects
    route_nodes_list, route_edges_list = transform_multi_agent_paths_to_node_and_edge_objects(
        overall_shortest_paths=overall_shortest_paths,
        orders=orders_list,
        layout_id=request_body.mapId)

    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].print_current_computational_time()

    route_response = []
    for i, item in enumerate(route_nodes_list):
        route_response.append(RouteResponse(nodes=item, edges=route_edges_list[i]))

    return route_response


def service_set_heuristic_for_a_star(request_body: HeuristicRequest):
    if config.config_file.PATH_PLANNING_HEURISTIC != data.enums.PathPlanningHeuristic(request_body.heuristic):
        config.config_file.PATH_PLANNING_HEURISTIC = data.enums.PathPlanningHeuristic(request_body.heuristic)
        heuristic = get_heuristic_interface()
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].change_heuristic(heuristic)
    return


def service_set_cbs_improvement(request_body: CBSImprovementRequest):
    config.config_file.CBS_COST_FUNCTION_IMPROVEMENT = request_body.useAdvancedCostFunction
    return


def service_get_parking_nodes(request_body: ParkingNodesRequest):
    """
    :param request_body: ParkingNodesRequest
    :return: Method to get possible parking nodes of the layout to ensure the solvability of the following mapd instance
             Each two arbitrary parking nodes most connected without traverse another endpoint
             Show at first if set of parking nodes is already computed
    """
    return mapf_algorithms.core.path_planning_init.path_planning_strategies[
           config.config_file.PATH_PLANNING_STRATEGY].parking_nodes_request(request_body)


def service_get_statistic_time_data():
    response_obj = StatisticTimeDataResponse(number_of_exceed_routing_time_threshold=
                                             mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_exceed_routing_time_threshold,
                                             number_of_failed_path_computations=
                                             mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_failed_path_computations,
                                             number_of_path_planning_requests=
                                             mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_path_planning_requests,
                                             number_of_generated_nodes_cbs=
                                             mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_generated_nodes_cbs,
                                             number_of_expanded_nodes_a_star=mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].number_of_expanded_nodes_a_star,
                                             path_planning_time=mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].path_planning_time
                                             )
    return response_obj


def service_set_parking_nodes_for_layout(request_body: SetParkingNodesRequest):
    mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].set_parking_nodes_from_layout(request_body.layoutId,
                                                                                 request_body.parkingNodes)
    return


def service_compute_layout_information_for_current_orders(request_body: LayoutInformation):
    layout_information = mapf_algorithms.core.path_planning_init.path_planning_strategies[
                            config.config_file.PATH_PLANNING_STRATEGY].compute_layout_information(request_body)
    return layout_information


def service_set_duration_edge(request_body: DurationEdgeRequest):
    config.config_file.DURATION_EDGE = request_body.duration
    return


def service_test_path_planning(request_body: PathPlanningTestRequest):
    paths, costs, _ = mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].compute_path(
        layout_id=request_body.layout_id,
        start_node_ids=request_body.start_node_ids,
        end_node_ids=request_body.end_node_ids,
        constraints=request_body.constraints,
        tokens=request_body.tokens
    )
    return paths, costs


def service_set_focal_heuristic(request_body: FocalHeuristicRequest):
    if request_body.heuristic is not None:
        config.config_file.ECBS_HEURISTIC = data.enums.ECBSHeuristic(request_body.heuristic)
        layouts = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts
        graph = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph
        exgraph = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].exgraph
        graph_with_stations = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph_with_stations
        travel_time_matrix = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].travel_time_matrix
        heuristic = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].heuristic

        path_planning_interface = get_path_planning_interface()
        heuristic_interface = heuristic
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY] = PathPlanningObj(
            os.environ['LIF_FILE'], path_planning_interface, heuristic_interface)
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts = layouts
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph = graph
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].exgraph = exgraph
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].graph_with_stations = graph_with_stations
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].travel_time_matrix = travel_time_matrix
    return


def service_solve_mapf_instance(request_body: PathPlanningRequest):
    start_time = time.monotonic()
    if request_body.path_planning_strategy is not None:
        service_set_path_planning_strategy(PathPlanningStrategy(pathPlanningStrategy=request_body.path_planning_strategy))
    if request_body.cost_function is not None:
        config.config_file.COST_FUNCTION = data.enums.CostFunction(request_body.cost_function)

    if request_body.boundary is not None:
        config.config_file.OPTIMALITY_BOUND = request_body.boundary

    if request_body.distance_heuristic is not None:
        if config.config_file.PATH_PLANNING_HEURISTIC != data.enums.PathPlanningHeuristic(request_body.distance_heuristic):
            config.config_file.PATH_PLANNING_HEURISTIC = data.enums.PathPlanningHeuristic(request_body.distance_heuristic)
            heuristic = get_heuristic_interface()
            mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].change_heuristic(heuristic)

    if request_body.focal_heuristic is not None:
        config.config_file.ECBS_HEURISTIC = data.enums.ECBSHeuristic(request_body.focal_heuristic)
    if request_body.boundary is not None:
        config.config_file.OPTIMALITY_BOUND = request_body.boundary

    if request_body.directed_graph is not None:
        config.config_file.DIRECTED_GRAPH = request_body.directed_graph

    if request_body.layouts is not None:
        mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].set_layout(request_body)
        edge_length = mapf_algorithms.core.path_planning_init.path_planning_strategies[
            config.config_file.PATH_PLANNING_STRATEGY].layouts[request_body.map_id].edges[0].length
        edge_duration = round(edge_length / config.config_file.MAX_SPEED_EDGE, 2)
        config.config_file.DURATION_EDGE = edge_duration
    else:
        if len(mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].layouts.keys()) < 1 or request_body.map_id is None:
            logger.exception('Error in solving MAPF request: No Layout assigned for path planning')
            raise Exception(f'Error in solving MAPF request: No Layout assigned for path planning with map id'
                            f' {request_body.map_id}')

    if len(request_body.start_node_ids) != len(request_body.end_node_ids):
        raise Exception('Error: Same number of start and end points needed!')

    logger.info(f'Start Points: {request_body.start_node_ids} and Goal Points: {request_body.end_node_ids}')

    if (data.enums.PathPlanningStrategy(request_body.path_planning_strategy) == data.enums.PathPlanningStrategy.i_cbs or
            data.enums.PathPlanningStrategy(request_body.path_planning_strategy) == data.enums.PathPlanningStrategy.i_ecbs):
        constraints = set()
    else:
        constraints = set()
    paths, costs, _ = mapf_algorithms.core.path_planning_init.path_planning_strategies[
        config.config_file.PATH_PLANNING_STRATEGY].compute_path(
        layout_id=request_body.map_id,
        start_node_ids=request_body.start_node_ids,
        end_node_ids=request_body.end_node_ids,
        constraints=constraints,
        tokens=[]
    )
    if paths is None:
        logger.exception(f'Error: No path found with {config.config_file.PATH_PLANNING_STRATEGY}!')
        raise Exception(f'Error: No path found with {config.config_file.PATH_PLANNING_STRATEGY}!')

    if request_body.show_solution is True:
        if (config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.i_ecbs or
                config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.i_cbs or
                config.config_file.PATH_PLANNING_STRATEGY == data.enums.PathPlanningStrategy.i_cbs_geo):
            show_lif_animated2(request_body.layouts[0], paths)
        else:
            show_lif_animated(request_body.layouts[0], paths)

    duration = time.monotonic() - start_time
    logger.info(f'Path planning solution: {paths}')
    logger.info(f'Path planning costs: {costs}')
    logger.info(f'Path planning total costs: {np.sum(costs)}')
    logger.info(f'Path planning duration: {duration} seconds')

    resp = {'costs': np.sum(costs),
            'nodes_cbs': mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].number_of_generated_nodes_cbs,
            'nodes_a_star': mapf_algorithms.core.path_planning_init.path_planning_strategies[
                config.config_file.PATH_PLANNING_STRATEGY].number_of_expanded_nodes_a_star}
    return resp
