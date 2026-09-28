from pydantic import BaseModel


############################################################
# Client api models only necessary for demo initialization #
############################################################


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



