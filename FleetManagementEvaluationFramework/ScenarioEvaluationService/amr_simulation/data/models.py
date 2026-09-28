from typing import List

from pydantic import BaseModel
from datetime import datetime
from data.enums import BlockingType, ActionStatus, OrderStatus


class NodePosition(BaseModel):
    x: float
    y: float
    theta: float | None = None
    mapId: str


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


class ControlPoint(BaseModel):
    x: float
    y: float
    weight: float | None = None


class Trajectory(BaseModel):
    degree: int
    knotVector: List[float]
    controlPoints: List[ControlPoint]


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
    description: str = ""
    batteryVoltage: float | None = None
    batteryHealth: float | None = None
    reach: float | None = None


class NodeState(BaseModel):
    nodeId: str
    sequenceId: int
    nodeDescription: str | None = None
    nodePosition: NodePosition | None = None
    released: bool


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


class Order(BaseModel):
    orderId: str
    orderUpdateId: int
    zoneSetId: str | None = None
    nodes: List[Node]
    edges: List[Edge]


class SimulationAllowedToRun(BaseModel):
    runAllowed: bool


class HeaderId(BaseModel):
    id: int


class NewAMRSystemRequest(BaseModel):
    amrId: str
    lastNodeId: str
    layoutId: str
    maxReachBattery: int


class NodeInfoRequest(BaseModel):
    nodeIds: List[str]
    layoutId: str


class AMRPauseRequest(BaseModel):
    amrId: str
    pause: bool


class CollisionCheckObject(BaseModel):
    nodeIds: List[str]
    edgeIds: List[str]
    checkCollisions: bool


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class NewOrderInfo(BaseModel):
    orderId: str
    sourceId: str | None = None
    sinkId: str | None = None
    sourceHandover: str | None = None
    sinkHandover: str | None = None
    publishTime: datetime | None = None
    startTime: datetime | None = None
    dueTime: datetime | None = None
    dimension: Dimension | None = None
    itemSkuId: str | None = None
    layoutId: str | None = None
    pickupTime: int | None = None
    dropoffTime: int | None = None
    priority: int | None = None
    amrIds: List[str] | None = None
    status: OrderStatus


class WaitingTimeRequest(BaseModel):
    waitingTime: float


class StationPosition(BaseModel):
    x: float
    y: float
    theta: float | None = None


class Station(BaseModel):
    stationId: str
    interactionNodeIds: List[str]
    stationName: str | None = None
    stationDescription: str | None = None
    stationHeight: float | None = None
    stationPosition: StationPosition | None = None


class Layout(BaseModel):
    layoutId: str
    layoutName: str | None = None
    layoutVersion: int | None = None
    layoutDescription: str | None = None
    nodes: List[Node]
    edges: List[Edge]
    stations: List[Station]


class MakeSpanRequest(BaseModel):
    earliestOrderId: str
    latestOrderId: str


class MakeSpanResponse(BaseModel):
    time: int
    total_service_time_driving: int | None = None
    total_service_time_empty_driving: int | None = None
