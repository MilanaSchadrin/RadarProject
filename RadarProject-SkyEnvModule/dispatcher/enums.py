from enum import Enum


class Priorities(Enum):
    HIGH = 1
    STANDARD = 2
    LOW = 3


class Modules(Enum):
    GUI = 0
    RadarMain = 1
    SE = 2
    LauncherMain = 3
    ControlCenter = 4