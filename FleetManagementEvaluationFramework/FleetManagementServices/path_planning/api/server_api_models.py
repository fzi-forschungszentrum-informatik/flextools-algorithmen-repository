import datetime
from typing import List, Union, Set, Tuple
from pydantic import BaseModel

from data.models import Node, Edge, Order, Station, Layout


class TravelTimeMatrixRequest(BaseModel):
    mapId: str


class SetTravelTimeRequest(BaseModel):
    mapId: str
    startNodeId: str
    endNodeId: str
    time: List[int]


class NodeInfoRequest(BaseModel):
    nodeIds: List[str]
    layoutId: str


class TravelTimeResponse(BaseModel):
    ttm: dict[str, List[float | None]]


class NodesResponse(BaseModel):
    nodes: List[Node]


class MapInfoRequest(BaseModel):
    mapId: str


class MapResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    stations: List[Station]


class RouteResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class Token(BaseModel):
    amrId: str
    tokens: List[str]


class PathPlanningStrategy(BaseModel):
    pathPlanningStrategy: str
    boundary: float | None = None
    heuristic: str | None = None


class PathRequest(BaseModel):
    path: str


class StationInfoRequest(BaseModel):
    layoutId: str
    stationIds: List[str]


class StationInfoResponse(BaseModel):
    stationId: str
    interactionNodes: List[str]


class RoutingForOrdersRequest(BaseModel):
    mapId: str
    lastNodeAmrId: str
    orders: List[Order]
    tokens: List[Token]
    amrId: str


class TokensEndPositionsRequest(BaseModel):
    nodeAmr: str | None = None
    nodeIds: List[str]
    layoutId: str
    start: str
    goal: str


class GraphConnectedInfo(BaseModel):
    isConnected: bool


class ComputationalTimeResponse(BaseModel):
    compTime: datetime.timedelta


class LIFObject(BaseModel):
    layouts: List[Layout]


class EdgeDurationResponse(BaseModel):
    duration: float


class MapIdResponse(BaseModel):
    mapId: str | None


class RoutingStartGoalRequest(BaseModel):
    starts: List[str]
    goals: List[str]
    orders: List[Order]
    mapId: str


class RoutingAMRInfo(BaseModel):
    amrId: str
    lastNodeId: str
    order: Order
    token: Token | None


class RoutingRequestObject(BaseModel):
    mapId: str
    routingAMR: List[RoutingAMRInfo]
    newOrderIds: List[str]
    deliveryOrderIds: List[str] | None = None
    planOrderIds: List[str] | None = None
    constraints: Set[Tuple[Union[str, Tuple[str, str]], Union[int, Tuple[int, float]]]] | None = None


class HeuristicRequest(BaseModel):
    heuristic: str


class CBSImprovementRequest(BaseModel):
    useAdvancedCostFunction: bool


class ParkingNodesRequest(BaseModel):
    layoutId: str
    endpoints: List[str]
    numberOfParkingNodes: int


class ParkingNodesResponse(BaseModel):
    parkingNodes: List[str]


class StatisticTimeDataResponse(BaseModel):
    number_of_failed_path_computations: int | None = None
    number_of_exceed_routing_time_threshold: int | None = None
    number_of_path_planning_requests: int | None = None
    number_of_generated_nodes_cbs: int | None = None
    number_of_expanded_nodes_a_star: int | None = None
    path_planning_time: float | None = None


class SetParkingNodesRequest(BaseModel):
    layoutId: str
    parkingNodes: List[str]


class StartGoal(BaseModel):
    start_node_id: str
    goal_node_id: str


class LayoutInformation(BaseModel):
    layout_id: str
    start_goals_orders: List[StartGoal]


class LayoutInformationResponse(BaseModel):
    betweenness_centrality_value: float
    number_shortest_paths: List[int] | None = None
    crossing_bottlenecks: List[List[float]] | None = None
    total_betweenness_centrality_layout: float
    max_betweenness_centrality_orders: List[float]


class DurationEdgeRequest(BaseModel):
    duration: float


class PathPlanningTestRequest(BaseModel):
    layout_id: str
    start_node_ids: List[str]
    end_node_ids: List[str]
    constraints: Set[Tuple[Union[str, Tuple[str, str]], Union[int, Tuple[int, float]]]] | None = None
    tokens:  List[Token] | None = None


class FocalHeuristicRequest(BaseModel):
    heuristic: str | None


class PathPlanningRequest(BaseModel):
    start_node_ids: List[str]
    end_node_ids: List[str]
    show_solution: bool = False
    path_planning_strategy: str | None = None
    boundary: float | None = None
    distance_heuristic: str | None = None
    focal_heuristic: str | None = None
    cost_function: str | None = None
    map_id: str | None = None
    layouts: List[Layout] | None = None
    directed_graph: bool = False





