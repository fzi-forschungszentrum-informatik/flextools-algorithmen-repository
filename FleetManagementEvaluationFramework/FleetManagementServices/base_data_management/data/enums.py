from enum import Enum


class AGVKinematic(str, Enum):
    DIFF = "DIFF"
    OMNI = "OMNI"
    THREEWHEEL = "THREEWHEEL"


class AGVClass(str, Enum):
    FORKLIFT = "FORKLIFT"
    CONVEYOR = "CONVEYOR"
    TUGGER = "TUGGER"
    CARRIER = "CARRIER"


class LocalizationType(str, Enum):
    NATURAL = "NATURAL"
    REFLECTOR = "REFLECTOR"
    RFID = "RFID"
    DMC = "DMC"
    SPOT = "SPOT"
    GRID = "GRID"


class NavigationType(str, Enum):
    PHYSICAL_LINE_GUIDED = "PHYSICAL_LINE_GUIDED"
    VIRTUAL_LINE_GUIDED = "VIRTUAL_LINE_GUIDED"
    AUTONOMOUS = "AUTONOMOUS"


class ParameterSupport(str, Enum):
    SUPPORTED = "SUPPORTED"
    REQUIRED = "REQUIRED"


class ActionScope(str, Enum):
    INSTANT = "INSTANT"
    NODE = "NODE"
    EDGE = "EDGE"