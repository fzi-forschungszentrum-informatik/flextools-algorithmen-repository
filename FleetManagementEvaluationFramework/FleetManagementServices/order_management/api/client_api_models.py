from pydantic import BaseModel
from datetime import datetime

from data.models import Order


class OrderUpdateResponse(BaseModel):
    amrId: str
    order: Order
    estimatedStartTime: datetime | None = None
    estimatedEndTime: datetime | None = None


class StorageLocationRequest(BaseModel):
    inputData: str
    algorithm: str


class NewItemRequest(BaseModel):
    number: str
    description: str


class SkusStoreRequestBody(BaseModel):
    locationId: str
    skuId: str | None = None
    itemId: str | None = None
    storedAt: str | None = None
    retrievedAt: str | None = None

