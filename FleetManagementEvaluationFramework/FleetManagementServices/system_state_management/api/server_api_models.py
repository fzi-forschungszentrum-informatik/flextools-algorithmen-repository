from typing import List
from pydantic import BaseModel
from datetime import datetime

from data.enums import ConnectionState
from data.models import Order


class GetAMRStateRequest(BaseModel):
    amrIds: List[str]


class SetAMRConnectionStateRequest(BaseModel):
    timestamp: datetime
    amrId: str
    connectionState: ConnectionState


class PlannedOrderIncoming(BaseModel):
    amrId: str
    order: Order
    index: int
    estimatedStartTime: datetime
    estimatedEndTime: datetime


class PlannedOrder(BaseModel):
    timestamp: datetime
    amrId: str
    order: Order


class AMRRequest(BaseModel):
    amrIds: List[str]


class OrderFinishRequest(BaseModel):
    amrId: str
    orderId: str


class SystemTimeResponse(BaseModel):
    timestamp: datetime


class SystemTimeRequest(BaseModel):
    sysTime: str


class SetAMRStateResponse(BaseModel):
    plannedOrders: List[PlannedOrder]
    terminate: bool | None = False


class AMRPauseRequest(BaseModel):
    amrId: str
    pause: bool


class PathRequest(BaseModel):
    path: str


class AMRPathRequest(BaseModel):
    amrId: str
    prev: bool


class AMRPORequest(BaseModel):
    amrId: str


class InstantOrder(BaseModel):
    amrId: str
    order: Order


class InstantOrders(BaseModel):
    instantOrders: List[InstantOrder]


class DispatchingStrategy(BaseModel):
    dispatchingStrategy: str
    useImprovement: bool | None = None


class PathPlanningInformation(BaseModel):
    number_to_find_path_again: List[int]