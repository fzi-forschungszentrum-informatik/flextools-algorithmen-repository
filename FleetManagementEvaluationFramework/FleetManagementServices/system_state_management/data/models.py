from typing import List
from pydantic import BaseModel

from data.enums import ActionStatus, BlockingType, OperatingMode, ConnectionState
from datetime import datetime


class AMRPosition(BaseModel):
    x: float
    y: float
    theta: float | None = None
    mapId: str
    mapDescription: str | None = None
    positionInitialized: bool


class Velocity(BaseModel):
    vx: float
    vy: float
    omega: float


class LoadDimension(BaseModel):
    length: float
    width: float
    height: float | None = None


class BoundingBoxReference(BaseModel):
    x: float
    y: float
    z: float
    theta: float | None = None


class Load(BaseModel):
    loadId: str | None = None
    loadType: str | None = None
    loadPosition: str | None = None
    boundingBoxReference: BoundingBoxReference | None = None
    loadDimension: LoadDimension | None = None
    weight: float | None = None


class BatteryState(BaseModel):
    batteryCharge: float
    charging: bool
    batteryVoltage: float | None = None
    batteryHealth: float | None = None
    reach: float | None = None


class NodePosition(BaseModel):
    x: float
    y: float
    theta: float | None = None
    mapId: str


class NodeState(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: str | None = None
    nodePosition: NodePosition | None = None
    released: bool


class ControlPoint(BaseModel):
    x: float
    y: float
    weight: float | None = None


class Trajectory(BaseModel):
    degree: int
    knotVector: List[float]
    controlPoints: List[ControlPoint]


class EdgeState(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: str | None = None
    released: bool
    trajectory: Trajectory | None = None


class ActionState(BaseModel):
    actionId: str
    actionStatus: ActionStatus
    actionDescription: str | None = None
    resultDescription: str | None = None
    actionType: str | None = None


class ActionParameter(BaseModel):
    key: str
    value: float | bool | int | str | datetime


class Action(BaseModel):
    actionId: str
    actionType: str
    actionDescription: str | None = None
    blockingType: BlockingType
    actionParameters: List[ActionParameter] | None = None


class Node(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: str | None = None
    released: bool
    nodePosition: NodePosition | None = None
    actions: List[Action]


class Edge(BaseModel):
    edgeId: str
    sequenceId: int
    edgeDescription: str | None = None
    released: bool
    startNodeId: str
    endNodeId: str
    maxSpeed: float | None = None
    maxHeight: float | None = None
    minHeight: float | None = None
    orientation: float | None = None
    orientationType: str | None = None
    direction: str | None = None
    rotationAllowed: bool | None = None
    maxRotationSpeed: float | None = None
    length: float | None = None
    trajectory: Trajectory | None = None
    actions: List[Action]


class Order(BaseModel):
    orderId: str
    orderUpdateId: int
    zoneSetId: str | None = None
    nodes: List[Node]
    edges: List[Edge]


class AMRState(BaseModel):
    timestamp: datetime
    amrId: str
    connectionState: ConnectionState
    orderId: str
    orderUpdateId: int
    zoneId: str | None = None
    lastNodeId: str
    lastNodeSequenceId: int
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


class PlannedOrderInfos(BaseModel):
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None
    order: Order


class SystemStateAMR(BaseModel):
    amrState: AMRState
    plannedOrders: List[PlannedOrderInfos]
    token: List[str]


class PlannedOrderSequenceIncoming(BaseModel):
    amrId: str
    orders: List[PlannedOrderInfos]


class Route(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class NewAMRSystemRequest(BaseModel):
    amrId: str
    lastNodeId: str
    layoutId: str
    maxReachBattery: int


class NodeInfoRequest(BaseModel):
    nodeIds: List[str]
    layoutId: str


class AMRDataResponse(BaseModel):
    amrId: str
    lastNodeId: str
    driving: bool
    connectionState: ConnectionState
    currentOrder: str
    numberOfPlannedOrders: int
    pause: bool
    plannedOrders: List[PlannedOrderInfos]
    batteryState: BatteryState
    actionsCurrentOrder: List[ActionState]
    x: int
    y: int
