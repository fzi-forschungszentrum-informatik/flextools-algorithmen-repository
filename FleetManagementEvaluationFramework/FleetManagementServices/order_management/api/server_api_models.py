from typing import List
from datetime import datetime

from pydantic import BaseModel

from data.enums import OrderStatus
from data.models import Order


class OrderUpdateRequest(BaseModel):
    amrId: str
    orderStatus: OrderStatus
    orderId: str
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None


class OrderInfoRequest(BaseModel):
    orderIds: List[str]


class OrderInfoResponse(BaseModel):
    orderId: str
    amrId: str | None = None
    orderStatus: OrderStatus
    startTime: datetime | None
    dueTime: datetime | None
    sourceNodeId: str | None
    sinkNodeId: str | None


class SKUInfoResponse(BaseModel):
    itemSkuId: str


class SetSKURequest(BaseModel):
    skuId: str
    orderId: str


class OrderStatusResponse(BaseModel):
    orderStatus: OrderStatus


class StationInfoRequest(BaseModel):
    orderId: str


class StationIdResponse(BaseModel):
    pickupStationId: str
    dropoffStationId: str


class RepositionOrder(BaseModel):
    amrId: str
    order: Order


class OrderDemo(BaseModel):
    sourceId: str | None = None
    sinkId: str | None = 'N_1'
    mapId: str | None = 'map'
