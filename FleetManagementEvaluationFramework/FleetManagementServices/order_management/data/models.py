from datetime import datetime
from typing import List
from pydantic import BaseModel

from data.enums import BlockingType, OrderStatus


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


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


class Order(BaseModel):
    orderId: str
    orderUpdateId: int
    zoneSetId: str | None = None
    nodes: List[Node]
    edges: List[Edge]


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


class OrderState(BaseModel):
    newOrderInfo: NewOrderInfo
    order: Order
    amrId: str | None = None
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None
