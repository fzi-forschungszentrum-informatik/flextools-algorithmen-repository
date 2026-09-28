from api.api_config import app
from api.server_api_models import SetTravelTimeRequest, \
    TravelTimeMatrixRequest, NodeInfoRequest, MapInfoRequest, PathPlanningStrategy, PathRequest, \
    StationInfoRequest, RoutingForOrdersRequest, TokensEndPositionsRequest, LIFObject, RoutingStartGoalRequest, \
    RoutingRequestObject, HeuristicRequest, CBSImprovementRequest, ParkingNodesRequest, SetParkingNodesRequest, \
    LayoutInformation, DurationEdgeRequest, PathPlanningTestRequest, FocalHeuristicRequest, PathPlanningRequest
from data.models_lif_file_generator import LIFFile
from mapf_algorithms.api_services.services import service_travel_time_matrix, service_set_travel_time, \
    service_get_node_infos, service_get_stations_info, service_get_map_info, service_set_path_planning_strategy, \
    service_set_lif_file, service_set_lif_file_as_object, service_set_lif_object, service_get_info_graph_connected, \
    service_compute_routes, service_reset_travel_time, service_reset_time, service_get_computational_time, \
    service_get_duration_edge, service_get_current_map_id, \
    service_routing_for_all_amr_after_timestep, service_set_heuristic_for_a_star, \
    service_set_cbs_improvement, service_get_parking_nodes, service_get_statistic_time_data, \
    service_set_parking_nodes_for_layout, service_compute_layout_information_for_current_orders, \
    service_set_duration_edge, service_test_path_planning, service_set_focal_heuristic, service_solve_mapf_instance


######################
# Rest-API Endpoints #
######################
@app.get("/travel-time-matrix")
async def travel_time_matrix_request(request_body: TravelTimeMatrixRequest):
    return service_travel_time_matrix(request_body)


@app.put("/travel-time")
async def set_travel_time_request(request_body: SetTravelTimeRequest):
    return service_set_travel_time(request_body)


@app.get("/nodes-info")
async def get_nodes_for_order(request_body: NodeInfoRequest):
    return service_get_node_infos(request_body)


@app.get("/stations-info")
async def get_station_infos(request_body: StationInfoRequest):
    return service_get_stations_info(request_body)


@app.get("/map-info")
async def get_map_info(request_body: MapInfoRequest):
    return service_get_map_info(request_body)


@app.put("/path-planning-strategy")
async def set_path_planning_strategy(request_body: PathPlanningStrategy):
    return service_set_path_planning_strategy(request_body)


@app.get('/health')
async def health():
    pass


@app.put("/lif-file")
async def set_lif_file_new(request_body: PathRequest):
    return service_set_lif_file(request_body)


@app.post("/lif-file-object")
async def set_lif_file_as_object(request_body: LIFFile):
    return service_set_lif_file_as_object(request_body)


@app.post("/lif")
async def set_lif_object(request_body: LIFObject):
    return service_set_lif_object(request_body)


@app.get("/info-graph-connected")
async def get_new_lif_file(request_body: TokensEndPositionsRequest):
    return service_get_info_graph_connected(request_body)


@app.post("/routing-for-amrs")
async def compute_routes_for_amrs(request_body: RoutingForOrdersRequest):
    return service_compute_routes(request_body)


@app.post("/reset")
async def reset_travel_time():
    return service_reset_travel_time()


@app.post("/reset-time")
async def reset_time():
    return service_reset_time()


@app.get("/computational-time")
async def get_computational_time():
    return service_get_computational_time()


@app.get("/duration-edge")
async def get_duration_edge(request_body: MapInfoRequest):
    return service_get_duration_edge(request_body)


@app.get("/map-id")
async def get_current_map_id():
    return service_get_current_map_id()


@app.post("/routing-for-all-amrs")
async def routing_for_all_amrs(request_body: RoutingRequestObject):
    return service_routing_for_all_amr_after_timestep(request_body)


@app.put("/heuristic")
async def set_heuristic_for_a_star(request_body: HeuristicRequest):
    return service_set_heuristic_for_a_star(request_body)


@app.put("/cbs-improvement")
async def set_cbs_improvement(request_body: CBSImprovementRequest):
    return service_set_cbs_improvement(request_body)


@app.put("/focal-heuristic")
async def set_focal_heuristic(request_body: FocalHeuristicRequest):
    return service_set_focal_heuristic(request_body)


@app.get("/parking-nodes")
async def get_parking_nodes(request_body: ParkingNodesRequest):
    return service_get_parking_nodes(request_body)


@app.get("/statistic-time-data")
async def get_statistic_time_data():
    return service_get_statistic_time_data()


@app.put("/parking-nodes")
async def set_parking_nodes_of_layout(request_body: SetParkingNodesRequest):
    return service_set_parking_nodes_for_layout(request_body)


@app.post("/layout-information-for-order")
async def compute_layout_information_for_orders(request_body: LayoutInformation):
    return service_compute_layout_information_for_current_orders(request_body)


@app.put("/duration-edge")
async def set_duration_edge(request_body: DurationEdgeRequest):
    return service_set_duration_edge(request_body)


@app.put("/start_path_planning_test")
async def start_path_planning_test(request_body: PathPlanningTestRequest):
    paths, costs = service_test_path_planning(request_body)
    return {
        "paths": paths,
        "costs": costs
    }


@app.post("/solve-path-planning-request")
async def routing_for_all_amrs(request_body: PathPlanningRequest):
    return service_solve_mapf_instance(request_body)

