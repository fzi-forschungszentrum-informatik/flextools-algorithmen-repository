from typing import List
from pydantic import BaseModel
from datetime import datetime

from data.enums import OrderStatus
from data.models import Order


class OrderDimensionRequest(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class PossibleAMRsRequest(BaseModel):
    amrIds: List[str]


class NodeInfoRequest(BaseModel):
    nodeIds: List[str]
    layoutId: str


class RouteRequest(BaseModel):
    mapId: str
    lastNodeAmrId: str
    order: List[Order]


class OrderUpdateRequest(BaseModel):
    amrId: str | None
    order: Order
    index: int | None
    estimatedStartTime: datetime | None
    estimatedEndTime: datetime | None


class TravelTimeMatrixRequest(BaseModel):
    mapId: str


class SystemTimeRequest(BaseModel):
    sysTime: str


class StationInfoRequest(BaseModel):
    layoutId: str
    stationIds: List[str]


class AssignedOrderUpdateRequest(BaseModel):
    amrId: str
    orderStatus: OrderStatus
    orderId: str
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None


class RepositionOrder(BaseModel):
    amrId: str
    order: Order


class TokensEndPositionsRequest(BaseModel):
    nodeAmr: str | None = None
    nodeIds: List[str]
    layoutId: str
    start: str
    goal: str


class ParkingNodesRequest(BaseModel):
    layoutId: str
    endpoints: List[str]
    numberOfParkingNodes: int

