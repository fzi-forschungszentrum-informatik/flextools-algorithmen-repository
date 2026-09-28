from enum import Enum


class OperatingMode(str, Enum):
    AUTOMATIC = "AUTOMATIC"
    SEMIAUTOMATIC = "SEMIAUTOMATIC"
    MANUAL = "MANUAL"
    SERVICE = "SERVICE"
    TEACHIN = "TEACHIN"


class ConnectionState(str, Enum):
    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"
    CONNECTIONBROKEN = "CONNECTIONBROKEN"


class ActionStatus(str, Enum):
    WAITING = "WAITING"
    INITIALIZING = "INITIALIZING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    FAILED = "FAILED"


class BlockingType(str, Enum):
    NONE = 'NONE'
    SOFT = 'SOFT'
    HARD = 'HARD'


class TaskAssignmentStrategy(str, Enum):
    push_back = "push_back"
    greedy = "greedy"
    greedy_completion_time = "greedy_completion_time"
    token_passing = "token_passing"
    central = "central"


class PathPlanningIntegration(str, Enum):
    complete_cbs = "complete_cbs"
    two_stage = "two_stage"

