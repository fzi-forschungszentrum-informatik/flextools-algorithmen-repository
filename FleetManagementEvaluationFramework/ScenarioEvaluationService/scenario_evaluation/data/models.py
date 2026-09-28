from typing import List

from pydantic import BaseModel
from datetime import datetime

from data.enums import BlockingType


class ActionParameter(BaseModel):
    key: str
    value: float | bool | int | datetime


class Action(BaseModel):
    actionId: str
    actionType: str
    actionDescription: str | None = None
    blockingType: BlockingType
    actionParameter: List[ActionParameter] | None = None


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


class LIFObject(BaseModel):
    layouts: List[Layout]


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


class PathPlanningRequest(BaseModel):
    start_node_ids: List[str]
    end_node_ids: List[str]
    show_solution: bool = False
    path_planning_strategy: str | None = None
    boundary: float | None = None
    distance_heuristic: str | None = None
    focal_heuristic: str | None = None
    cost_function: str | None = None
    map_id: str | None = None
    layouts: List[Layout] | None = None
    directed_graph: bool = False


