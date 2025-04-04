from dataclasses import dataclass
from typing import Union, Dict, List, Tuple
from enums import Priorities, Modules


class Message:
    recipient_id: Union[Modules.GUI, Modules.RadarMain, Modules.SE,
                        Modules.LauncherMain, Modules.ControlCenter]
    priority: Union[Priorities.LOW, Priorities.STANDARD, Priorities.HIGH]


@dataclass
class SEStarting(Message):
    planes: Dict[int, List[float]]


@dataclass
class SeKilled(Message):
    objects: Dict[int, List[float]]  # TODO что-то непонятное


@dataclass
class SEAddRocket(Message):
    rockets: Dict[int, List[float]]


@dataclass
class CCLaunchMissile:
    target: int  # TODO int -> Target


@dataclass
class CCToRadarNewStatus:
    new_target_status: Tuple[int]


@dataclass
class CCToSkyEnv:
    missiles: List[int]  # TODO int -> Missiles


@dataclass
class RadarToGUICurrentTarget:
    radar_id: int  # TODO все поля - непонятно что
    target_id: int
    sector_size: int


@dataclass
class RadarControllerObjects:
    detected_objects: List[int]  # TODO int -> Target


@dataclass
class LauncherControllerMissileLaunched:
    missiles: Dict[int, List]  # TODO что-то непонятное
