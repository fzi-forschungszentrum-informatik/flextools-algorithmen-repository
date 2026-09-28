from pydantic import BaseModel


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
