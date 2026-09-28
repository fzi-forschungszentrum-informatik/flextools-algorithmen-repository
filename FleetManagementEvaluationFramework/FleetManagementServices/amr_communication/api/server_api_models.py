from pydantic import BaseModel

from data.models import Order
from datetime import datetime


class OrderAMRRequest(BaseModel):
    timestamp: datetime
    amrId: str
    order: Order


class SimulationRunUntilOrderRequest(BaseModel):
    orderId: str | None


class HeaderIdRequest(BaseModel):
    headerId: int


class NextSimulationStepResponse(BaseModel):
    nextSimulationStep: bool




