from typing import List
from pydantic import BaseModel

from data.enums import OrderStatus
from data.models import Dimension, Order, SystemStateAMR
from datetime import datetime


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


class DispatchingStrategy(BaseModel):
    dispatchingStrategy: str
    useImprovement: bool | None = None


class StoredOrderInfo(BaseModel):
    order: Order
    orderInfo: NewOrderInfo
    assigned: bool | None = None


class RequestOrderAMR(BaseModel):
    amrId: str | None = None
    systemStatesAmr: List[SystemStateAMR]


class DeleteOrderRequest(BaseModel):
    orderId: str


class ReleaseOrderRequest(BaseModel):
    orderId: str


class ReservedNodeRequest(BaseModel):
    amrId: str
    nodes: List[str]
