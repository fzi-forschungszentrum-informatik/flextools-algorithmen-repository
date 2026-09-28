from enum import Enum


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class OrderStatus(str, Enum):
    NEW = "NEW"
    PLANNED = "PLANNED"
    STARTED = "STARTED"
    PICKUP = "PICKUP"
    DROPOFF = "DROPOFF"
    FINISHED = "FINISHED"


class ActionStatus(str, Enum):
    WAITING = "WAITING",
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"



