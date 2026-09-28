from typing import List

from pydantic import BaseModel
import datetime

from data.enums import BlockingType
from data.models import ActionParameter, StationPosition


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
    rotationAllowed: bool | None = None
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


