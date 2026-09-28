import numpy as np

from api.server_api_models import TravelTimeMatrixRequest, NodeInfoRequest, MapInfoRequest, \
    SetTravelTimeRequest, RoutingForOrdersRequest, Token, RoutingRequestObject, RoutingAMRInfo
from data.enums import PathPlanningStrategy, BlockingType
from data.models import Order, Node, NodePosition, Action
from mapf_algorithms.api_services.services import service_compute_routes, service_get_node_infos, service_get_map_info, \
    service_set_travel_time, service_routing_for_all_amr_after_timestep


def test_get_travel_time_matrix(path_planning_strategies_mock):
    response = path_planning_strategies_mock['dijkstra'].get_travel_time_matrix(TravelTimeMatrixRequest(mapId="map1"))
    print(response)
    ttm = {}
    for key, value in response.items():
        ttm[eval(key)] = np.mean(value)
    assert ttm[('A', 'A')] == 0
    assert ttm[('A', 'B')] == 25.0
    assert ttm[('A', 'C')] == 40.0
    assert ttm[('A', 'F')] == 65.0
    assert ttm[('A', 'I')] == 105.0
    assert ttm[('A', 'H')] == 90
    assert ttm[('H', 'H')] == 0
    assert ttm[('E', 'H')] == 55.0
    assert ttm[('F', 'C')] == 55.0
    assert ttm[('B', 'G')] == 65.0
    assert ttm[('D', 'H')] == 50.0


def test_routing_for_order_request_1(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)
    routing_for_order_request = RoutingForOrdersRequest(
            mapId="map1",
            lastNodeAmrId="F",
            orders=[
                Order(
                    orderId='1', orderUpdateId=0,
                    nodes=[
                        Node(
                            nodeId="A",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=60, y=0, mapId='map1'),
                            actions=[]
                        ),
                        Node(
                            nodeId="H",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=120, y=30, mapId='map1'),
                            actions=[]
                        ),
                    ],
                    edges=[]
                )
            ],
            tokens=[],
            amrId='1')

    response = service_compute_routes(routing_for_order_request)[0]
    solution_node_list = ['F', 'D', 'B', 'A', 'B', 'D', 'F', 'H']
    solution_edge_list = ['df', 'bd', 'ab', 'ab', 'bd', 'df', 'fh']
    node_list = []
    for node in response.nodes:
        node_list.append(node.nodeId)
    edge_list = []
    for edge in response.edges:
        edge_list.append(edge.edgeId)
    assert node_list == solution_node_list
    assert edge_list == solution_edge_list


def test_routing_for_order_request_2(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)

    routing_for_order_request = RoutingForOrdersRequest(
            mapId="map1",
            lastNodeAmrId="G",
            orders=[
                Order(
                    orderId='1', orderUpdateId=0,
                    nodes=[
                        Node(
                            nodeId="I",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=150, y=0, mapId='map1'),
                            actions=[]
                        ),
                        Node(
                            nodeId="C",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=50, y=30, mapId='map1'),
                            actions=[]
                        ),
                    ],
                    edges=[]
                )
            ],
            tokens=[],
            amrId='1')

    response = service_compute_routes(routing_for_order_request)[0]
    solution_node_list = ['G', 'I', 'G', 'E', 'C']
    solution_edge_list = ['ig', 'ig', 'eg', 'ce']
    node_list = []
    for node in response.nodes:
        node_list.append(node.nodeId)
    edge_list = []
    for edge in response.edges:
        edge_list.append(edge.edgeId)
    assert node_list == solution_node_list
    assert edge_list == solution_edge_list


def test_routing_for_order_request_3(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)

    routing_for_order_request = RoutingForOrdersRequest(
            mapId="map1",
            lastNodeAmrId="B",
            orders=[
                Order(
                    orderId='1', orderUpdateId=0,
                    nodes=[
                        Node(
                            nodeId="B",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=50, y=0, mapId='map1'),
                            actions=[]
                        ),
                        Node(
                            nodeId="E",
                            sequenceId=1,
                            released=True,
                            nodePosition=NodePosition(x=100, y=30, mapId='map1'),
                            actions=[]
                        ),
                    ],
                    edges=[]
                )
            ],
            tokens=[],
            amrId='1')
    response = service_compute_routes(routing_for_order_request)[0]
    solution_node_list = ['B', 'C', 'E']
    solution_edge_list = ['bc', 'ce']
    node_list = []
    for node in response.nodes:
        node_list.append(node.nodeId)
    edge_list = []
    for edge in response.edges:
        edge_list.append(edge.edgeId)
    assert node_list == solution_node_list
    assert edge_list == solution_edge_list


def test_get_node_infos(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)
    node_info_request = NodeInfoRequest(nodeIds=['A'], layoutId='map1')
    response = service_get_node_infos(node_info_request)

    assert response.nodes[0].nodePosition.x == 0
    assert response.nodes[0].nodePosition.y == 0


def test_get_map_infos(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)
    map_info_request = MapInfoRequest(mapId='map1')
    response = service_get_map_info(map_info_request)

    assert len(response.nodes) == 9
    assert len(response.edges) == 10


def test_set_travel_time(path_planning_strategies_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_strategies_mock)
    travel_time_request = SetTravelTimeRequest(mapId='map1', startNodeId='A', endNodeId='C', time=[60])
    service_set_travel_time(travel_time_request)


def test_conflict_based_search_1(path_planning_mapf_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_mapf_mock)
    monkeypatch.setattr("mapf_algorithms.api_services.services.config.config_file.PATH_PLANNING_STRATEGY", 'cbs')
    request_body = RoutingForOrdersRequest(mapId='map1',
                                           lastNodeAmrId='N_0_2',
                                           orders=[Order(orderId='No order', orderUpdateId=-1, nodes=[], edges=[]),
                                                     Order(orderId='T1', orderUpdateId=0,
                                                           nodes=[Node(nodeId="N_0_2", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=0, y=60,
                                                                                                mapId='map1'),
                                                                      actions=[]),
                                                                 Node(nodeId="N_3_1", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=90, y=30,
                                                                                                mapId='map1'),
                                                                      actions=[])],
                                                           edges=[])
                                                     ],
                                           tokens=[Token(amrId='1', tokens=['N_0_2', 'Event']),
                                                   Token(amrId='2', tokens=['N_0_3', 'Event'])],
                                           amrId='1')
    optimal_routs = service_compute_routes(request_body)
    assert len(optimal_routs) == 1
    assert optimal_routs[0].nodes[0].nodeId == 'N_0_2'


def test_conflict_based_search_2(path_planning_mapf_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_mapf_mock)
    monkeypatch.setattr("mapf_algorithms.api_services.services.config.config_file.PATH_PLANNING_STRATEGY", 'cbs')
    request_body = RoutingForOrdersRequest(mapId='map1',
                                           lastNodeAmrId='N_0_3',
                                           orders=[Order(orderId='T2', orderUpdateId=0,
                                                         nodes=[Node(nodeId="N_0_2", sequenceId=0, released=True,
                                                                       nodePosition=NodePosition(x=0, y=60,
                                                                                                 mapId='map1'),
                                                                       actions=[]),
                                                                 Node(nodeId="N_3_1", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=90, y=30,
                                                                                                mapId='map1'),
                                                                      actions=[])],
                                                         edges=[]),
                                                     Order(orderId='T1', orderUpdateId=0,
                                                           nodes=[Node(nodeId="N_0_3", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=0, y=90,
                                                                                                mapId='map1'),
                                                                      actions=[]),
                                                                 Node(nodeId="N_3_0", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=90, y=0,
                                                                                                mapId='map1'),
                                                                      actions=[])],
                                                           edges=[])],
                                           tokens=[Token(amrId='1', tokens=['N_0_2', 'Event', 'N_1_2', 'N_2_2', 'N_3_2',
                                                                               'N_3_1', 'Event']),
                                                     Token(amrId='2', tokens=['N_0_3', 'Event'])
                                                     ],
                                           amrId='2')

    optimal_routs = service_compute_routes(request_body)
    assert len(optimal_routs) == 1
    assert optimal_routs[0].nodes[0].nodeId == 'N_0_3'
    assert optimal_routs[0].nodes[1].nodeId == 'N_0_2'
    assert optimal_routs[0].nodes[2].nodeId == 'N_1_2'
    assert optimal_routs[0].nodes[3].nodeId == 'N_2_2'
    assert optimal_routs[0].nodes[4].nodeId == 'N_3_2'
    assert optimal_routs[0].nodes[5].nodeId == 'N_3_1'
    assert optimal_routs[0].nodes[6].nodeId == 'N_3_0'


def test_prioritized_path_planning(path_planning_mapf_mock2, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_mapf_mock2)
    monkeypatch.setattr("mapf_algorithms.api_services.services.config.config_file.PATH_PLANNING_STRATEGY",
                        PathPlanningStrategy.cooperative_a_star)
    request_body = RoutingForOrdersRequest(mapId='map1',
                                           lastNodeAmrId='N_0_3',
                                           orders=[Order(orderId='T3', orderUpdateId=0,
                                                         nodes=[Node(nodeId="N_0_3", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=0, y=2,
                                                                                               mapId='map1'),
                                                                     actions=[]),
                                                                Node(nodeId="N_1_1", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=1, y=1,
                                                                                               mapId='map1'),
                                                                     actions=[])],
                                                         edges=[])],
                                           tokens=[
                                               Token(amrId='1', tokens=['N_0_2', 'Event', 'N_0_2',
                                                                         'N_1_2', 'N_2_2', 'N_3_2',
                                                                         'N_3_1', 'Event'])
                                               ],
                                           amrId='2')
    route = service_compute_routes(request_body)[0]
    assert len(route.nodes) == 6
    assert len(route.edges) == 3
    assert route.nodes[0].nodeId == 'N_0_3'
    assert route.nodes[1].nodeId == 'N_0_3'
    assert route.nodes[2].nodeId == 'N_0_3'
    assert route.nodes[3].nodeId == 'N_0_2'
    assert route.nodes[4].nodeId == 'N_1_2'
    assert route.nodes[5].nodeId == 'N_1_1'


def test_initialize_graph_with_stations(path_planning_strategies_mock):
    assert len(path_planning_strategies_mock['dijkstra'].graph_with_stations['map1'].nodes) == 10
    number_of_edges = 0
    for key, item in path_planning_strategies_mock['dijkstra'].graph_with_stations['map1'].graph.items():
        number_of_edges += len(item.keys())
    number_of_edges = number_of_edges / 2  # the dictionary count one edge from both directions
    assert number_of_edges == 11


def test_heuristic_manhattan_distance(path_planning_strategies_mock2):
    cost_to_reach = path_planning_strategies_mock2['cooperative_a_star'].heuristic.heuristic_costs_to_goal(
        graph=path_planning_strategies_mock2['cooperative_a_star'].graph['map1'],
        goal='H',
        layout_id='map1'
        )
    assert cost_to_reach['H'] == 0
    assert cost_to_reach['I'] == 30
    assert cost_to_reach['G'] == 60
    assert cost_to_reach['A'] == 180
    assert cost_to_reach['F'] == 50
    assert cost_to_reach['D'] == 100


def test_heuristic_euclidean_distance(path_planning_strategies_mock3):
    cost_to_reach = path_planning_strategies_mock3['cooperative_a_star'].heuristic.heuristic_costs_to_goal(
        graph=path_planning_strategies_mock3['cooperative_a_star'].graph['map1'],
        goal='H',
        layout_id='map1'
        )
    assert cost_to_reach['H'] == 0
    assert cost_to_reach['I'] == 30
    assert cost_to_reach['G'] == 60
    assert round(cost_to_reach['A'], 2) == 152.97
    assert cost_to_reach['F'] == 50
    assert cost_to_reach['D'] == 100


def test_conflict_based_search_3(path_planning_mapf_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_mapf_mock)
    monkeypatch.setattr("mapf_algorithms.api_services.services.config.config_file.PATH_PLANNING_STRATEGY",
                        'cbs')
    request_body = RoutingForOrdersRequest(mapId='map1',
                                           lastNodeAmrId='N_0_3',
                                           orders=[Order(orderId='T2', orderUpdateId=0,
                                                         nodes=[Node(nodeId="N_0_2", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=0, y=2,
                                                                                               mapId='map1'),
                                                                     actions=[]),
                                                                 Node(nodeId="N_3_1", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=3, y=1,
                                                                                                mapId='map1'),
                                                                      actions=[])],
                                                         edges=[]),
                                                   Order(orderId='T0', orderUpdateId=0,
                                                         nodes=[Node(nodeId="N_1_1", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=1, y=1,
                                                                                               mapId='map1'),
                                                                     actions=[]),
                                                                Node(nodeId="N_3_3", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=3, y=3,
                                                                                               mapId='map1'),
                                                                     actions=[])],
                                                         edges=[]),
                                                   Order(orderId='T1', orderUpdateId=0,
                                                         nodes=[Node(nodeId="N_0_3", sequenceId=0, released=True,
                                                                     nodePosition=NodePosition(x=0, y=3,
                                                                                               mapId='map1'),
                                                                     actions=[]),
                                                                 Node(nodeId="N_3_0", sequenceId=0, released=True,
                                                                      nodePosition=NodePosition(x=3, y=0,
                                                                                                mapId='map1'),
                                                                      actions=[])],
                                                           edges=[])
                                                   ],
                                           tokens=[Token(amrId='1', tokens=['N_0_2', 'Event', 'N_1_2', 'N_2_2', 'N_3_2',
                                                                            'N_3_1', 'Event']),
                                                   Token(amrId='3', tokens=['N_1_1', 'Event', 'N_1_1', 'N_1_2', 'N_2_2',
                                                                            'N_3_2', 'N_3_3', 'Event']),
                                                   Token(amrId='2', tokens=['N_0_3', 'Event'])
                                                   ],
                                           amrId='2')

    optimal_routs = service_compute_routes(request_body)
    # for j, route in enumerate(optimal_routs):
    #     node_list = []
    #     for node in route.nodes:
    #         node_list.append(node.nodeId)
    #     print(f'Route AMR {j+1}: {node_list}')

    assert len(optimal_routs) == 1
    assert optimal_routs[0].nodes[0].nodeId == 'N_0_3'
    assert optimal_routs[0].nodes[1].nodeId == 'N_0_2'
    assert optimal_routs[0].nodes[2].nodeId == 'N_1_2'
    assert optimal_routs[0].nodes[3].nodeId == 'N_2_2'
    assert optimal_routs[0].nodes[4].nodeId == 'N_3_2'
    assert optimal_routs[0].nodes[5].nodeId == 'N_3_1'
    assert optimal_routs[0].nodes[6].nodeId == 'N_3_0'


def test_conflict_based_search_double_pickup_location(path_planning_warehouse_mock, monkeypatch):
    monkeypatch.setattr("mapf_algorithms.core.path_planning_init.path_planning_strategies", path_planning_warehouse_mock)
    monkeypatch.setattr("mapf_algorithms.api_services.services.config.config_file.PATH_PLANNING_STRATEGY", 'cbs')

    token1 = Token(amrId='1', tokens=['N_12_1'])
    token2 = Token(amrId='2', tokens=['N_12_2'])
    token3 = Token(amrId='3', tokens=['N_12_3'])

    order1 = Order(orderId='1', orderUpdateId=0, nodes=[Node(nodeId='N_1_2', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=1.0,y=2.0, mapId='map1'),
                                                             actions=[Action(actionId='1', actionType='pick',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])]),
                                                        Node(nodeId='N_13_1', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=13.0, y=1.0, mapId='map1'),
                                                             actions=[Action(actionId='2', actionType='drop',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])])
                                                        ], edges=[])

    order2 = Order(orderId='2', orderUpdateId=0, nodes=[Node(nodeId='N_1_2', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=1.0, y=2.0, mapId='map1'),
                                                             actions=[Action(actionId='3', actionType='pick',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])]),
                                                        Node(nodeId='N_13_2', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=13.0, y=2.0, mapId='map1'),
                                                             actions=[Action(actionId='4', actionType='drop',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])])
                                                        ], edges=[])

    order3 = Order(orderId='3', orderUpdateId=0, nodes=[Node(nodeId='N_1_2', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=1.0, y=2.0, mapId='map1'),
                                                             actions=[Action(actionId='5', actionType='pick',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])]),
                                                        Node(nodeId='N_12_3', sequenceId=0, released=True,
                                                             nodePosition=NodePosition(x=12.0, y=3.0, mapId='map1'),
                                                             actions=[Action(actionId='6', actionType='drop',
                                                                             blockingType=BlockingType.HARD,
                                                                             actionParameters=[])])
                                                        ], edges=[])

    routing_amr_list = [RoutingAMRInfo(amrId='1', lastNodeId='N_12_1', order=order1, token=token1),
                        RoutingAMRInfo(amrId='2', lastNodeId='N_12_2', order=order2, token=token2),
                        RoutingAMRInfo(amrId='3', lastNodeId='N_12_3', order=order3, token=token3)]
    request_body = RoutingRequestObject(mapId='map1', routingAMR=routing_amr_list, newOrderIds=['1', '2', '3'])

    optimal_routs = service_routing_for_all_amr_after_timestep(request_body)
    # for route in optimal_routs:
    #     print('Next Path')
    #     for node in route.nodes:
    #         print(node.nodeId)
    #         if len(node.actions) > 0:
    #             print('Event')
    assert len(optimal_routs) == 3


def create_node(name, cost, h_cost):
    return {
        'name': name,
        'costs': cost,
        'heuristic_cost': h_cost
    }


def check_invariants(focal):

    # Check: all focal items must satisfy o_val <=.f_min_o_val * w
    for elem in focal.focal:
        assert elem.payload['costs'] <= focal.f_min_o_val * focal.w

    # Check: all open items must satisfy o_val >.f_min_o_val * w
    for elem in focal.open:
        assert elem.primary > focal.f_min_o_val * focal.w

    # Check: focal is sorted by f_val
    f_vals = [elem.primary for elem in focal.focal]
    assert f_vals == sorted(f_vals), "Focal list is not sorted by f_val"

    # Check: open is sorted by o_val
    o_vals = [elem.primary for elem in focal.open]
    assert o_vals == sorted(o_vals), "Open list is not sorted by o_val"

