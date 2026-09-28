from typing import List

from pydantic import BaseModel
import datetime

from api.client_api_models import Error, Information, SafetyState
from data.enums import ConnectionState, OperatingMode, MapStatus
from data.models import Order, Node, Edge, NodeState, EdgeState, AMRPosition, Velocity, Load, ActionState, \
    BatteryState


class OrderStateRequest(BaseModel):
    timestamp: datetime.datetime
    amrId: str
    order: Order


class SystemTimeRequest(BaseModel):
    systemTime: datetime.datetime


class SystemTimeResponse(BaseModel):
    timestamp: datetime.datetime


class CollisionDetection(BaseModel):
    collisionDetection: bool


class PathRequest(BaseModel):
    path: str


class ConnectionStateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime.datetime | str
    version: str
    manufacturer: str
    serialNumber: str
    connectionState: ConnectionState

class Map(BaseModel):
    mapId: str
    mapVersion: str
    mapDescriptor: str | None = None
    mapStatus: MapStatus

class StateUpdateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime.datetime | str
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


class OrderUpdateVDABodyHeader(BaseModel):
    headerId: int
    timestamp: datetime.datetime | str
    version: str
    manufacturer: str
    serialNumber: str
    orderId: str
    orderUpdateId: int
    zoneSetId: str | None = None
    nodes: List[Node]
    edges: List[Edge]


class DispatchingStrategy(BaseModel):
    dispatchingStrategy: str
    useImprovement: bool | None = None


class SimulationStepResponse(BaseModel):
    simulationFinish: bool
    percentageFinish: float


class DrivingTimeResponse(BaseModel):
    drivingTimeLoaded: float
    drivingTimeUnloaded: float


class StatisticFileNames(BaseModel):
    AMRStatisticDataFileName: str
    GraphStatisticDataFileName: str
