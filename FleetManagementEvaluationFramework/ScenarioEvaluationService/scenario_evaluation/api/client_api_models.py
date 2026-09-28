from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from data.enums import OrderStatus


class SystemTimeRequest(BaseModel):
    sysTime: str


class SystemTimeResponse(BaseModel):
    timestamp: datetime


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class NewOrderInfo(BaseModel):
    orderId: str
    sourceId: str
    sinkId: str | None = None
    publishTime: datetime | None = None
    startTime: datetime
    dueTime: datetime
    dimension: Dimension
    itemSkuId: str | None = None
    layoutId: str | None = None
    pickupTime: int | None = None
    dropoffTime: int | None = None
    priority: Optional[int] = None
    amrIds: Optional[List[str]] = None
    status: OrderStatus


class OrderInfoRequest(BaseModel):
    orderIds: List[str]


class MakeSpanRequest(BaseModel):
    earliestOrderId: str
    latestOrderId: str


class TaskAssignmentStrategy(BaseModel):
    dispatchingStrategy: str
    useImprovement: bool | None = None


class PathPlanningStrategy(BaseModel):
    pathPlanningStrategy: str
    boundary: float | None = None
    heuristic: str | None = None


class CollisionDetection(BaseModel):
    collisionDetection: bool


class FileNameRequest(BaseModel):
    orderFileName: str
    amrFileName: str
    routeFileName: str


class WaitingTimeRequest(BaseModel):
    waitingTime: float


class HeuristicRequest(BaseModel):
    heuristic: str


class CBSImprovementRequest(BaseModel):
    useAdvancedCostFunction: bool


class SetParkingNodesRequest(BaseModel):
    layoutId: str
    parkingNodes: List[str]


class DurationEdgeRequest(BaseModel):
    duration: float


class FocalHeuristicRequest(BaseModel):
    heuristic: str | None


class StatisticFileNames(BaseModel):
    AMRStatisticDataFileName: str
    GraphStatisticDataFileName: str

