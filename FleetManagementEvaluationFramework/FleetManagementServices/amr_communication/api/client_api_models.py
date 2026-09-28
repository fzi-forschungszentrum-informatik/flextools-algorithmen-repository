from pydantic import BaseModel
from typing import List

from data.enums import ConnectionState, OperatingMode, OrderStatus, ErrorLevel, InfoLevel, EStop, MapStatus
from data.models import AMRPosition, Velocity, Load, BatteryState, NodeState, EdgeState, ActionState, Order, Node, Edge
from datetime import datetime


class SetAMRConnectionStateRequest(BaseModel):
    timestamp: datetime
    amrId: str
    connectionState: ConnectionState


class SetAMRStateRequest(BaseModel):
    timestamp: datetime
    amrId: str
    connectionState: ConnectionState
    orderId: str
    orderUpdateId: int
    zoneId: str | None = None
    lastNodeId: str
    lastNodeSequenceId: int | None = None
    driving: bool
    paused: bool | None = None
    distanceSinceLastNode: float
    operatingMode: OperatingMode
    amrPosition: AMRPosition | None = None
    velocity: Velocity | None = None
    loads: List[Load] | None = None
    batteryState: BatteryState
    nodeStates: List[NodeState]
    edgeStates: List[EdgeState]
    actionStates: List[ActionState]


class ErrorReference(BaseModel):
    referenceKey: str
    referenceValue: str


class Error(BaseModel):
    errorType: str
    errorReferences: List[ErrorReference]
    errorDescription: str | None = None
    errorHint: str | None = None
    errorLevel: ErrorLevel


class InfoReference(BaseModel):
    referenceKey: str
    referenceValue: str


class Information(BaseModel):
    infoType: str
    infoReferences: List[InfoReference]
    infoDescription: str | None = None
    infoLevel: InfoLevel


class SafetyState(BaseModel):
    eStop: EStop
    fieldViolation: bool


class OrderUpdateRequest(BaseModel):
    amrId: str
    orderStatus: OrderStatus
    orderId: str
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None


class OrderFinishRequest(BaseModel):
    amrId: str
    orderId: str


class SystemTimeRequest(BaseModel):
    timestamp: datetime


class StatisticsAMRRequest(BaseModel):
    amrId: str
    timestamp: datetime
    orderId: str
    orderStatus: OrderStatus
    nodeId: str | None = None


class SkusRetrieveRequestBody(BaseModel):
    locationId: str
    skuId: str
    storedAt: str | None = None
    retrievedAt: str | None = None


class SkusStoreRequestBody(BaseModel):
    locationId: str
    skuId: str | None = None
    itemId: str | None = None
    storedAt: str | None = None
    retrievedAt: str | None = None


class OrderInfoRequest(BaseModel):
    orderIds: List[str]


class StationInfoRequest(BaseModel):
    orderId: str


class OrderUpdateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime | str
    version: str
    manufacturer: str
    serialNumber: str
    orderId: str
    orderUpdateId: int
    zoneSetId: str | None = None
    nodes: List[Node]
    edges: List[Edge]


class ConnectionStateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime | str
    version: str
    manufacturer: str
    serialNumber: str
    connectionState: ConnectionState


class Map(BaseModel):
    mapId: str
    mapVersion: str
    mapDescription: str | None = None
    mapStatus: MapStatus


class StateUpdateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime | str
    version: str
    manufacturer: str
    serialNumber: str
    maps: List[Map] | None = None
    orderId: str
    orderUpdateId: int
    zoneId: str | None = None
    lastNodeId: str
    lastNodeSequenceId: int
    driving: bool
    paused: bool | None = None
    newBaseRequest: bool | None = None
    distanceSinceLastNode: float | None = None
    operatingMode: OperatingMode
    nodeStates: List[NodeState]
    edgeStates: List[EdgeState]
    agvPosition: AMRPosition | None = None
    velocity: Velocity | None = None
    loads: List[Load] | None = None
    actionStates: List[ActionState]
    batteryState: BatteryState
    errors: List[Error]
    information: List[Information] | None = None
    safetyState: SafetyState

