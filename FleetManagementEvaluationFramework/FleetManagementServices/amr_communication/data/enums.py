from enum import Enum


class OrderStatus(str, Enum):
    NEW = 'NEW'
    PLANNED = 'PLANNED'
    STARTED = 'STARTED'
    PICKUP = 'PICKUP'
    DROPOFF = 'DROPOFF'
    FINISHED = 'FINISHED'


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class OperatingMode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    SEMIAUTOMATIC = "SEMIAUTOMATIC"
    MANUAL = "MANUAL"
    SERVICE = "SERVICE"
    TEACHIN = "TEACHIN"


class ConnectionState(str, Enum):
    ONLINE = "ONLINE",
    OFFLINE = "OFFLINE",
    CONNECTIONBROKEN = "CONNECTIONBROKEN"


class ActionStatus(str, Enum):
    WAITING = "WAITING",
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class ErrorLevel(str, Enum):
    WARNING = "WARNING"
    FATAL = "FATAL"


class InfoLevel(str, Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"


class EStop(str, Enum):
    AUTOACK = "AUTOACK"
    MANUAL = "MANUAL"
    REMOTE = "REMOTE"
    NONE = "NONE"


class MapStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
