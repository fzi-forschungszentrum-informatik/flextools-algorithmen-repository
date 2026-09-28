import json
import log_config.log

from api.api_config import set_service_urls
from api.client_api import solve_mapf_instances
from config.config_file import LOGGER_NAME
from data.models import PathPlanningRequest, Action, Node, NodePosition, Edge, Station, StationPosition, Layout
import data.enums
from logic.help_functions import compute_length_edge, compute_edge_list

logger = log_config.log.set_logger(LOGGER_NAME)


def main():
    set_service_urls()
    mapf_file = rf'./mapf_instances/mapf_example.json'

    layout_file = rf'./lif_files/LIF_example.json'
    show_solution = True
    directed_graph = True
    path_planning_strategy = data.enums.PathPlanningStrategy.i_cbs_geo
    focal_heuristic = data.enums.ECBSHeuristic.h1_fast
    distance_heuristic = data.enums.PathPlanningHeuristic.euclidean
    w = 1.0
    start_nodes, end_nodes = get_start_and_end_nodes(mapf_file)

    layout_list = get_layout(layout_file)

    for i, start_node_batch in enumerate(start_nodes):
        request_object = PathPlanningRequest(start_node_ids=start_node_batch,
                                             end_node_ids=end_nodes[i],
                                             show_solution=show_solution,
                                             path_planning_strategy=path_planning_strategy,
                                             boundary=w,
                                             distance_heuristic=distance_heuristic,
                                             focal_heuristic=focal_heuristic,
                                             cost_function=None,
                                             map_id='map1',
                                             layouts=layout_list,
                                             directed_graph=directed_graph)
        res = solve_mapf_instances(request_object).json()

        if res is not None:
            logger.info('Costs: {}'.format(res['costs']))
            logger.info('Generated Nodes CBS: {}'.format(res['nodes_cbs']))
            logger.info('Expanded Nodes A Star: {}'.format(res['nodes_a_star']))
    return


def get_start_and_end_nodes(mapf_file):
    start_nodes = []
    end_nodes = []

    f = open(mapf_file, "r")
    data = json.load(f)
    f.close()

    for item in data:
        start_nodes.append(item['start_nodes'])
        end_nodes.append(item['end_nodes'])

    return start_nodes, end_nodes


def get_layout(layout_file):
    f = open(layout_file, "r")
    data = json.load(f)
    f.close()

    layout_list = []
    for item in data['layouts']:
        node_list = []
        for node in item['nodes']:
            action_list = []
            for action in node['vehicleTypeNodeProperties'][0]['actions']:
                action_list.append(Action(actionId='',
                                          actionType=action['actionType'],
                                          blockingType=data.enums.BlockingType.HARD))
            node_list.append(Node(nodeId=node['nodeId'], sequenceId=0, released=True,
                                  nodePosition=NodePosition(x=node['nodePosition']['x'],
                                                            y=node['nodePosition']['y'],
                                                            mapId=node['mapId']),
                                  actions=action_list))
        if 'edges' in item.keys():
            if len(item['edges']) > 0:
                edge_list = []
                for edge in item['edges']:
                    action_list_edge = []
                    for action in edge['vehicleTypeEdgeProperties'][0]['actions']:
                        action_list_edge.append(Action(actionId='',
                                                       actionType=action['actionType'],
                                                       blockingType=data.enums.BlockingType.HARD))
                    length = compute_length_edge(edge['startNodeId'], edge['endNodeId'], node_list)
                    edge_list.append(Edge(edgeId=edge['edgeId'], sequenceId=0, released=True,
                                          startNodeId=edge['startNodeId'],
                                          endNodeId=edge['endNodeId'],
                                          maxSpeed=edge['vehicleTypeEdgeProperties'][0]['maxSpeed'],
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
        layout_list.append(layout)
    return layout_list


if __name__ == "__main__":
    main()
