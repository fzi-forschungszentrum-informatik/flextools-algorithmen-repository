from typing import List, Set, Union, Tuple
from pydantic import BaseModel

from data.models import Order, SystemStateAMR, Node


class Token(BaseModel):
    amrId: str
    tokens: List[str]


class StationPosition(BaseModel):
    x: float
    y: float
    theta: float


class Station(BaseModel):
    stationId: str
    stationName: str
    stationDescription: str
    interactionNodeIds: List[str]
    stationPosition: StationPosition
    type: str


class RequestOrderAMR(BaseModel):
    amrId: str | None = None
    systemStatesAmr: List[SystemStateAMR]


class RoutingForOrdersRequest(BaseModel):
    mapId: str
    lastNodeAmrId: str
    orders: List[Order]
    tokens: List[Token]
    amrId: str


class NodesResponse(BaseModel):
    nodes: List[Node]


class RoutingStartGoalRequest(BaseModel):
    starts: List[str]
    goals: List[str]
    orders: List[Order]
    mapId: str


class DeleteOrderRequest(BaseModel):
    orderId: str


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


class ReleaseOrderRequest(BaseModel):
    orderId: str


class StartGoal(BaseModel):
    start_node_id: str
    goal_node_id: str


class LayoutInformation(BaseModel):
    layout_id: str
    start_goals_orders: List[StartGoal]


class ReservedNodeRequest(BaseModel):
    amrId: str
    nodes: List[str]