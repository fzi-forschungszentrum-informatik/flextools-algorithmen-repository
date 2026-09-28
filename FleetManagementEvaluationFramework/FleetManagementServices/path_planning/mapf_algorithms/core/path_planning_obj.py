import json
import time
from typing import List, Dict
import logging
import copy

import rustworkx as rx

import config.config_file
from api.server_api_models import TravelTimeResponse, SetTravelTimeRequest, TravelTimeMatrixRequest, LIFObject, \
    ParkingNodesRequest, ParkingNodesResponse, PathPlanningRequest
from config.config_file import MAX_SPEED_EDGE, LOGGER_NAME
from data.data_structures.extended_graph import ExtendedGraph
from data.models_lif_file_generator import LIFFile
from interfaces.path_planning_heuristic_interface import Heuristic

from mapf_algorithms.methods.initialization_methods_travel_time import (init_graph_with_edges, compute_length_edge,
                                                                        compute_edge_list, init_extended_graph)
from interfaces.path_planning_interface import PathPlanning
from data.enums import BlockingType
from data.models import Layout, Node, NodePosition, Action, Edge, Station, StationPosition

logger = logging.getLogger(LOGGER_NAME)


class PathPlanningObj:

    def __init__(self, data_file: str, path_planning_interface: PathPlanning, heuristic_interface: Heuristic):
        self.path_planning_time = 0  # For all path planning algorithms
        self.computational_time = 0
        self.number_of_exceed_routing_time_threshold = 0
        self.number_of_failed_path_computations = 0
        self.number_of_path_planning_requests = 0
        self.number_of_generated_nodes_cbs = 0
        self.number_of_expanded_nodes_a_star = 0
        # heuristic for a star
        self.heuristic = heuristic_interface
        # initialize layouts
        self.layouts = {}
        self.__initialize_layouts_for_lif_file(data_file)

        self.__initialize_heuristic_with_layouts()

        # initialize graphs for all layouts
        self.graph = {}
        self.graph_with_stations = {}
        self.exgraph: Dict[str, ExtendedGraph] = {}

        self.__initialize_graphs_for_layout()

        self.path_planning_interface = path_planning_interface

        self.travel_time_matrix = {}
        self.__compute_ttms_for_layouts()
        self.__parking_nodes = {}

    ##########
    # public #
    ##########
    def get_travel_time_matrix(self, travel_time_matrix_request: TravelTimeMatrixRequest):
        if travel_time_matrix_request.mapId in self.travel_time_matrix.keys():
            requested_travel_times = self.travel_time_matrix[travel_time_matrix_request.mapId].ttm
        else:
            logger.info(f'Error: No Travel Time Matrix found for layout {travel_time_matrix_request.mapId} !')
            requested_travel_times = None
        return requested_travel_times

    def set_travel_time(self, set_travel_time_request: SetTravelTimeRequest):
        self.travel_time_matrix[set_travel_time_request.mapId].ttm[str((set_travel_time_request.startNodeId,
                                                                        set_travel_time_request.endNodeId))] =\
            set_travel_time_request.time

    def compute_path(self, layout_id: str, start_node_ids: List[str], end_node_ids: List[str],
                     constraints=None, _graph=None, tokens=None):

        graph = self.exgraph[layout_id]

        if graph is None:
            graph = self.graph[layout_id]
        if tokens is None:
            tokens = []
        path, costs, generated_nodes_cbs, generated_nodes_astar, path_constraints =\
            self.path_planning_interface.path_planning(graph=graph,
                                                       layout_id=layout_id,
                                                       start_node_ids=start_node_ids,
                                                       end_node_ids=end_node_ids,
                                                       constraints=constraints,
                                                       tokens=tokens,
                                                       heuristic=self.heuristic)
        logger.info(f'Generated nodes CBS: {generated_nodes_cbs}')
        logger.info(f'Expanded nodes A Star: {generated_nodes_astar}')
        self.number_of_generated_nodes_cbs += generated_nodes_cbs
        self.number_of_expanded_nodes_a_star += generated_nodes_astar
        return path, costs, path_constraints

    def set_layout(self, request_body: LIFObject | PathPlanningRequest):
        for layout in request_body.layouts:
            self.layouts[layout.layoutId] = layout
            self.__initialize_heuristic_with_single_layout(layout.layoutId)
            self.__initialize_graph_for_single_layout(layout.layoutId)
            self.__compute_ttm_with_rustworkx(layout.layoutId)

    def print_current_computational_time(self):
        logger.debug(f'CPU Time for path computation after last reset: {self.computational_time} seconds')

    ###########
    # private #
    ###########

    def __initialize_layouts_for_lif_file(self, path_to_lif_file):
        if path_to_lif_file == '':  # empty initialization
            return
        f = open(path_to_lif_file, "r")
        data = json.load(f)
        f.close()
        for item in data['layouts']:
            node_list = []
            for node in item['nodes']:
                action_list = []
                if 'vehicleTypeNodeProperties' in node.keys():
                    for action in node['vehicleTypeNodeProperties'][0]['actions']:
                        action_list.append(Action(actionId='',
                                                  actionType=action['actionType'],
                                                  blockingType=BlockingType.HARD))
                    node_list.append(Node(nodeId=node['nodeId'], sequenceId=0, released=True,
                                          nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                                    y=node['nodePosition']['y'],
                                                                    mapId=node['mapId']),
                                          actions=action_list))
                else:
                    node_list.append(Node(nodeId=node['nodeId'], sequenceId=0, released=True,
                                          nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                                    y=node['nodePosition']['y'],
                                                                    mapId=node['nodePosition']['mapId']),
                                          actions=action_list))
            if 'edges' in item.keys():
                if len(item['edges']) > 0:
                    edge_list = []
                    for edge in item['edges']:
                        action_list_edge = []
                        if "vehicleTypeEdgeProperties" in edge.keys():
                            for action in edge['vehicleTypeEdgeProperties'][0]['actions']:
                                action_list_edge.append(Action(actionId='',
                                                               actionType=action['actionType'],
                                                               blockingType=BlockingType.HARD))
                            length = compute_length_edge(edge['startNodeId'], edge['endNodeId'], node_list)
                            edge_list.append(Edge(edgeId=edge['edgeId'], sequenceId=0, released=True,
                                                  startNodeId=edge['startNodeId'],
                                                  endNodeId=edge['endNodeId'],
                                                  maxSpeed=edge['vehicleTypeEdgeProperties'][0]['maxSpeed'],
                                                  length=length, actions=action_list_edge))
                        else:
                            length = compute_length_edge(edge['startNodeId'], edge['endNodeId'], node_list)
                            edge_list.append(Edge(edgeId=edge['edgeId'], sequenceId=0, released=True,
                                                  startNodeId=edge['startNodeId'],
                                                  endNodeId=edge['endNodeId'],
                                                  maxSpeed=10,
                                                  length=length, actions=action_list_edge))

                else:
                    edge_list = compute_edge_list(node_list)
            else:
                edge_list = compute_edge_list(node_list)
            station_list = []
            for station in item['stations']:
                station_list.append(Station(stationId=station['stationId'],
                                            interactionNodeIds=station['interactionNodeIds'],
                                            stationName=station['stationName'],
                                            stationPosition=StationPosition(x=station['stationPosition']['x'],
                                                                            y=station['stationPosition']['y'])))

            layout = Layout(layoutId=item['layoutId'], nodes=node_list, edges=edge_list, stations=station_list)
            self.layouts[layout.layoutId] = layout

    def set_lif_object(self, request_body: LIFFile):
        for item in request_body.layouts:
            node_list = []
            for node in item.nodes:
                action_list = []
                for action in node.vehicleTypeNodeProperties[0].actions:
                    action_list.append(Action(actionId='',
                                              actionType=action.actionType,
                                              blockingType=BlockingType.HARD))
                node_list.append(Node(nodeId=node.nodeId, sequenceId=0, released=True,
                                      nodePosition=NodePosition(x=node.nodePosition.x,
                                                                y=node.nodePosition.y,
                                                                mapId=node.mapId),
                                      actions=action_list))

            if len(item.edges) > 0:
                edge_list = []
                for edge in item.edges:
                    if edge.vehicleTypeEdgeProperties[0].rotationAllowed is not None:
                        if edge.vehicleTypeEdgeProperties[0].rotationAllowed is False:
                            config.config_file.DIRECTED_GRAPH = True
                        else:
                            config.config_file.DIRECTED_GRAPH = False
                    else:
                        config.config_file.DIRECTED_GRAPH = True
                    action_list_edge = []
                    for action in edge.vehicleTypeEdgeProperties[0].actions:
                        action_list_edge.append(Action(actionId='',
                                                       actionType=action.actionType,
                                                       blockingType=BlockingType.HARD))
                    length = compute_length_edge(edge.startNodeId, edge.endNodeId, node_list)
                    edge_list.append(Edge(edgeId=edge.edgeId, sequenceId=0, released=True,
                                          startNodeId=edge.startNodeId,
                                          endNodeId=edge.endNodeId,
                                          maxSpeed=edge.vehicleTypeEdgeProperties[0].maxSpeed,
                                          length=length, actions=action_list_edge))
                    if (config.config_file.DIRECTED_GRAPH is False and
                            edge.vehicleTypeEdgeProperties[0].rotationAllowed is True):
                        # for the case of uni- and bidirectional edges
                        edge_list.append(Edge(edgeId=edge.edgeId, sequenceId=0, released=True,
                                              startNodeId=edge.endNodeId,
                                              endNodeId=edge.startNodeId,
                                              maxSpeed=edge.vehicleTypeEdgeProperties[0].maxSpeed,
                                              length=length, actions=action_list_edge))
            else:
                edge_list = compute_edge_list(node_list)
            station_list = []
            for station in item.stations:
                station_list.append(Station(stationId=station.stationId,
                                            interactionNodeIds=station.interactionNodeIds,
                                            stationName=station.stationName,
                                            stationPosition=StationPosition(x=station.stationPosition.x,
                                                                            y=station.stationPosition.y)))
            layout = Layout(layoutId=item.layoutId, nodes=node_list, edges=edge_list, stations=station_list)
            self.layouts[layout.layoutId] = layout
            self.__initialize_heuristic_with_single_layout(layout.layoutId)
            self.__initialize_graph_for_single_layout(layout.layoutId)
            self.__compute_ttm_with_rustworkx(layout.layoutId)

    def __initialize_graphs_for_layout(self):
        for layout_id in self.layouts.keys():
            self.__initialize_graph_for_single_layout(layout_id)

    def __compute_ttms_for_layouts(self):
        for key in self.graph_with_stations.keys():
            self.__compute_ttm_with_rustworkx(key)

    def __initialize_graph_for_single_layout(self, layoutId: str):
        edges = copy.deepcopy(self.layouts[layoutId].edges)
        additional_edges = copy.deepcopy(self.layouts[layoutId].edges)
        for station in self.layouts[layoutId].stations:
            for node_id in station.interactionNodeIds:
                for edge in self.layouts[layoutId].edges:
                    if edge.startNodeId == node_id:
                        if str(f'E-{station.stationId}-{edge.endNodeId}') not in edges:
                            additional_edges.append(Edge(edgeId=str(f'E-{station.stationId}-{edge.endNodeId}'),
                                                         sequenceId=0,
                                                         released=True,
                                                         startNodeId=station.stationId,
                                                         endNodeId=edge.endNodeId,
                                                         maxSpeed=MAX_SPEED_EDGE,
                                                         length=edge.length,
                                                         actions=[]))
                    if edge.endNodeId == node_id:
                        if str(f'E-{edge.startNodeId}-{station.stationId}') not in edges:
                            additional_edges.append(Edge(edgeId=str(f'E-{edge.startNodeId}-{station.stationId}'),
                                                         sequenceId=0,
                                                         released=True,
                                                         startNodeId=edge.startNodeId,
                                                         endNodeId=station.stationId,
                                                         maxSpeed=MAX_SPEED_EDGE,
                                                         length=edge.length,
                                                         actions=[]))

        self.exgraph[layoutId] = init_extended_graph(self.layouts[layoutId])
        graph = init_graph_with_edges(edges)
        graph_with_stations = init_graph_with_edges(additional_edges)
        self.graph[layoutId] = graph
        self.graph_with_stations[layoutId] = graph_with_stations

    def __compute_ttm_with_rustworkx(self, layout_id):
        nodes = [node.nodeId for node in self.layouts[layout_id].nodes]
        node_index = {node_id: i for i, node_id in enumerate(nodes)}

        edges = []
        weights = []
        seen = set()

        ttm_start_time = time.time()
        for u, neighbors in self.graph[layout_id].graph.items():
            for v, w in neighbors.items():
                u_i = node_index[u]
                v_i = node_index[v]
                if config.config_file.DIRECTED_GRAPH is True:
                    edges.append((u_i, v_i))
                    weights.append(w)
                else:
                    edge = tuple(sorted((u_i, v_i)))
                    if edge in seen:
                        continue
                    seen.add(edge)
                    edges.append(edge)
                    weights.append(w)


        if config.config_file.DIRECTED_GRAPH is True:
            g = rx.PyDiGraph(multigraph=False)
        else:
            g = rx.PyGraph(multigraph=False)
        g.add_nodes_from([None] * len(nodes))
        g.add_edges_from([(u, v, float(w)) for (u, v), w in zip(edges, weights)])

        dist_map = rx.all_pairs_dijkstra_path_lengths(g, edge_cost_fn=float)

        ttm_dict = {}
        for i, u in enumerate(nodes):
            source_distance = dist_map[i] if i in dist_map else {}
            for j, v in enumerate(nodes):
                if i == j:
                    ttm_dict[str((u, v))] = [0]
                    continue
                distance = source_distance[j] if j in source_distance else None
                if distance is None:
                    ttm_dict[str((u, v))] = [None]
                else:
                    ttm_dict[str((u, v))] = [distance]
        ttm_time_end = time.time() - ttm_start_time
        logger.info(f'TTM building: {ttm_time_end} seconds')
        self.travel_time_matrix[layout_id] = TravelTimeResponse(ttm=ttm_dict)

    def __initialize_heuristic_with_layouts(self):
        for layout_id in self.layouts.keys():
            self.__initialize_heuristic_with_single_layout(layout_id)

    def __initialize_heuristic_with_single_layout(self, layout_id):
        self.heuristic.set_layout(layout_id, self.layouts[layout_id])

    def change_heuristic(self,  heuristic_interface: Heuristic):
        self.heuristic = heuristic_interface
        self.__initialize_heuristic_with_layouts()

    def set_parking_nodes_from_layout(self, layout_id: str, parking_nodes: List[str]):
        self.__parking_nodes[layout_id] = parking_nodes

    def parking_nodes_request(self, request_body: ParkingNodesRequest):
        if request_body.layoutId not in self.__parking_nodes.keys():
            self.compute_parking_nodes_for_total_graph(request_body)
        parking_nodes = copy.deepcopy(self.__parking_nodes[request_body.layoutId])

        for task_endpoint in request_body.endpoints:
            if task_endpoint in parking_nodes:
                parking_nodes.remove(task_endpoint)
        return ParkingNodesResponse(parkingNodes=parking_nodes)

    def compute_parking_nodes_for_total_graph(self, request_body: ParkingNodesRequest):
        """
        :param request_body: ParkingNodesRequest
        :return: Method to get possible parking nodes of the layout to ensure the solvability of the following mapd instance
                Each two arbitrary parking nodes most connected without traverse another endpoint
        """
        graph = copy.deepcopy(self.graph[request_body.layoutId])
        graph_copy = copy.deepcopy(graph)
        possible_nodes = copy.deepcopy(graph_copy.nodes)

        parking_nodes = []
        endpoint_list = []
        for node in possible_nodes:
            next_node = False
            endpoint_list_copy = copy.deepcopy(endpoint_list)
            endpoint_list_copy.append(node)
            for index, end_node_1 in enumerate(endpoint_list_copy):
                for index2, end_node_2 in enumerate(endpoint_list_copy[index + 1:]):
                    graph_copy = copy.deepcopy(graph)
                    for end_point in endpoint_list_copy:
                        if end_point != end_node_1 and end_point != end_node_2:
                            graph_copy.remove_node(end_point)
                    is_connected = graph_copy.are_connected(end_node_1, end_node_2)
                    if is_connected is False:
                        next_node = True
                if index == len(endpoint_list_copy) - 1:
                    break
            if next_node is False:  # All endpoints connected with all endpoints
                parking_nodes.append(node)
                endpoint_list.append(node)
                logger.debug(f'Add parking node {node} to parking nodes{parking_nodes} and endpoints {endpoint_list}')
            if node == possible_nodes[-1]:
                logger.debug(f'No further endpoints found')
        self.__parking_nodes[request_body.layoutId] = copy.deepcopy(parking_nodes)
        return

