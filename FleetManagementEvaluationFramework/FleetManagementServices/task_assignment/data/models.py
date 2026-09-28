from datetime import datetime
from typing import List, Set, Union, Tuple
from pydantic import BaseModel

from data.enums import BlockingType, ActionStatus, ConnectionState, OperatingMode


class ActionParameter(BaseModel):
    key: str
    value: float | bool | int | str | datetime


class Action(BaseModel):
    actionId: str
    actionType: str
    actionDescription: str | None = None
    blockingType: BlockingType
    actionParameters: List[ActionParameter] | None = None


class NodePosition(BaseModel):
    x: float
    y: float
    theta: float | None = None
    mapId: str


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


class AMRState(BaseModel):
    amrId: str
    connectionState: ConnectionState
    orderUpdateId: int
    zoneId: str | None = None
    orderId: str
    lastNodeId: str
    lastNodeSequenceId: int
    nodeStates: List[NodeState]
    edgeStates: List[EdgeState]
    actionStates: List[ActionState]
    driving: bool
    paused: bool | None = None
    distanceSinceLastNode: float
    operatingMode: OperatingMode
    amrPosition: AMRPosition | None = None
    velocity: Velocity | None = None
    loads: List[Load] | None = None
    batteryState: BatteryState


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class PlannedOrderInfo(BaseModel):
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None
    order: Order


class SystemStateAMR(BaseModel):
    amrState: AMRState
    plannedOrders: List[PlannedOrderInfo]
    token: List[str]


class OrderSequenceUpdateRequest(BaseModel):
    amrId: str
    orders: List[PlannedOrderInfo]


class ActionIdCounter(BaseModel):
    nextActionId: int


class InstantOrder(BaseModel):
    amrId: str
    order: Order


class InstantOrders(BaseModel):
    instantOrders: List[InstantOrder]


class Token(BaseModel):
    amrId: str
    tokens: List[str]


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
