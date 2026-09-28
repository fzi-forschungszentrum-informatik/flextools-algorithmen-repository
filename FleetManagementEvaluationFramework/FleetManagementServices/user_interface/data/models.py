from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


from data.enums import OrderStatus, BlockingType


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class NewOrderInfo(BaseModel):
    orderId: str
    sourceId: str | None = None
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


class MapInfoRequest(BaseModel):
    mapId: str


class AMRRequests(BaseModel):
    amrIds: List[str]


class SystemTimeRequest(BaseModel):
    sysTime: str


class NewAMRSystemRequest(BaseModel):
    amrId: str
    lastNodeId: str
    layoutId: str
    maxReachBattery: int


class LoadDimension(BaseModel):
    length: float
    width: float
    height: float | None = None


class NewAMRRequest(BaseModel):
    amrId: str
    seriesName: str
    agvClass: str
    maxLoadMass: float
    maxSpeed: float
    loadDimension: LoadDimension
    length: float
    width: float
    height: float


class AMRPauseRequest(BaseModel):
    amrId: str
    pause: bool


class MakeSpanRequest(BaseModel):
    earliestOrderId: str
    latestOrderId: str


class DispatchingStrategy(BaseModel):
    dispatchingStrategy: str
    useImprovement: bool | None = None


class PathPlanningStrategy(BaseModel):
    pathPlanningStrategy: str
    boundary: float | None = None
    heuristic: str | None = None


class CollisionDetection(BaseModel):
    collisionDetection: bool


class SimulationRunUntilOrderRequest(BaseModel):
    orderId: str | None


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


class AMRPathRequest(BaseModel):
    amrId: str
    prev: bool


class AMRPORequest(BaseModel):
    amrId: str


class NextSimulationStepResponse(BaseModel):
    nextSimulationStep: bool


class SystemTimeResponse(BaseModel):
    timestamp: datetime


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


class Layout(BaseModel):
    layoutId: str
    layoutName: str | None = None
    layoutVersion: int | None = None
    layoutDescription: str | None = None
    nodes: List[Node]
    edges: List[Edge]
    stations: List[Station]


class LIFObject(BaseModel):
    layouts: List[Layout]