from typing import List

from pydantic import BaseModel
import datetime
from enum import Enum


class ActionParameter(BaseModel):
    key: str
    value: float | bool | int | datetime.datetime


class StationPosition(BaseModel):
    x: float
    y: float
    theta: float | None = None


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class MetaInformation(BaseModel):
    projectIdentification: str
    exportTimestamp: datetime.datetime
    lifVersion: str
    creator: str


class NodePositionLIF(BaseModel):
    x: float
    y: float


class ActionLIF(BaseModel):
    actionType: str
    actionDescription: str | None
    requirementType: str | None = None
    blockingType: BlockingType
    actionParameters: List[ActionParameter]


class VehicleTypeNodeProperty(BaseModel):
    vehicleTypeId: str
    theta: float | None = None
    actions: List[ActionLIF]


class NodeLIF(BaseModel):
    nodeId: str
    nodeName: str | None = None
    nodeDescription: str | None = None
    mapId: str | None = None
    nodePosition: NodePositionLIF
    vehicleTypeNodeProperties: List[VehicleTypeNodeProperty]


class LoadRestriction(BaseModel):
    unloaded: bool
    loaded: bool
    loadSetNames: List[str]


class VehicleTypeEdgeProperty(BaseModel):
    vehicleTypeId: str
    vehicleOrientation: float | None = None
    orientationType: str | None = None
    rotationAllowed: bool
    rotationAtStartNodeAllowed: str | None = None
    rotationAtEndNodeAllowed: str | None = None
    maxSpeed: float | None = None
    maxRotationSpeed: float | None = None
    minHeight: float | None = None
    maxHeight: float | None = None
    loadRestriction: LoadRestriction | None = None
    actions: List[ActionLIF]


class EdgeLIF(BaseModel):
    edgeId: str
    edgeName: str | None = None
    edgeDescription: str | None = None
    startNodeId: str
    endNodeId: str
    vehicleTypeEdgeProperties: List[VehicleTypeEdgeProperty]


class StationLIF(BaseModel):
    stationId: str
    interactionNodeIds: List[str]
    stationName: str | None = None
    stationDescription: str | None = None
    stationHeight: float | None = None
    stationPosition: StationPosition | None = None


class LIFLayout(BaseModel):
    layoutId: str
    layoutName: str | None = None
    layoutVersion: str | None = None
    layoutDescription: str | None = None
    nodes: List[NodeLIF]
    edges: List[EdgeLIF]
    stations: List[StationLIF]


class LIFFile(BaseModel):
    metaInformation: MetaInformation
    layouts: List[LIFLayout]


class DemoRequest(BaseModel):
    lifObject: LIFFile
    amrId: str
    currentNode: str
    mapId: str | None = 'map'


class AMRPositionFile(BaseModel):
    x: float
    y: float
    theta: float = 0
    map_id: str = 'map_1'
    map_description: str | None = None
    position_initialized: bool = True


class BatteryStateFile(BaseModel):
    battery_charge: float = 1
    charging: bool = False
    batteryVoltage: float | None = None
    batteryHealth: float | None = None
    reach: float


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


class ActionStatus(str, Enum):
    WAITING = "WAITING"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class ActionState(BaseModel):
    actionId: str
    actionStatus: ActionStatus
    actionDescription: str | None = None
    resultDescription: str | None = None
    actionType: str | None = None


class SystemStateFile(BaseModel):
    amr_id: str
    order_id: str = ""
    order_update_id: int = 0
    last_node_id: str
    driving: bool = False
    paused: bool = False
    distance_since_last_node: float = 0
    AMRPosition: AMRPositionFile
    BatteryState: BatteryStateFile
    node_states: List[NodeState] = []
    edge_states: List[EdgeState] = []
    action_states: List[ActionState] = []


class OrderStatus(str, Enum):
    NEW = "NEW"
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FINISHED = "FINISHED"


class Dimension(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class NewOrderInfo(BaseModel):
    orderId: str
    sourceId: str
    sinkId: str | None = None
    publishTime: datetime.datetime | None = None
    startTime: datetime.datetime | None = None
    dueTime: datetime.datetime | None = None
    dimension: Dimension | None = None
    itemSkuId: str | None = None
    layoutId: str | None = None
    pickupTime: int | None = None
    dropoffTime: int | None = None
    priority: int | None = None
    amrIds: List[str] | None = None
    status: OrderStatus
