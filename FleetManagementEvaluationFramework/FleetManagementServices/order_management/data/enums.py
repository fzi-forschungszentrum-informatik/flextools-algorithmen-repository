from enum import Enum


class OrderStatus(str, Enum):
    NEW = "NEW"
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FINISHED = "FINISHED"


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'
