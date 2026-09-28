from typing import List
from pydantic import BaseModel


class AmrPropertyRequest(BaseModel):
    x: float
    y: float
    z: float
    weight: float


class PossibleAMRsResponse(BaseModel):
    amrIds: List[str]


class AMRBaseDataRequest(BaseModel):
    amrIds: List[str]


class AMRBaseDataInfoResponse(BaseModel):
    maxSpeed: float
    accelerationMax: float
    decelerationMax: float


class PathRequest(BaseModel):
    path: str
