from enum import Enum


class Priorities(Enum):
    SUPERHIGH = 5
    HIGH = 4
    STANDARD = 3
    LOW = 2
    SUPERLOW = 1
    LOWERST = 0


class Modules(Enum):
    GUI = 0
    RadarMain = 1
    SE = 2
    LauncherMain = 3
    ControlCenter = 4