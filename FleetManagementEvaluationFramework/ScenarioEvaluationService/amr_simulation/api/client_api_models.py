from typing import List

from pydantic import BaseModel

from data.enums import ConnectionState, OperatingMode, ErrorLevel, InfoLevel, EStop
from data.models import AMRPosition, Velocity, Load, BatteryState, NodeState, EdgeState, ActionState


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


class AMRStateVDA(BaseModel):
    orderId: str
    orderUpdateId: int
    zoneId: str | None = None
    lastNodeId: str
    lastNodeSequenceId: int
    driving: bool
    paused: bool | None = None
    newBaseRequest: bool | None = None
    distanceSinceLastNode: float
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


class AMRBaseDataRequest(BaseModel):
    amrIds: List[str]


class ConnectionStateVDA(BaseModel):
    connectionState: ConnectionState


class HeaderIdRequest(BaseModel):
    headerId: int

