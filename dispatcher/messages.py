from dataclasses import dataclass
from typing import Union, Dict, List
from enums import Priorities, Modules


@dataclass
class Message:
    recipient_id: Union[Modules.GUI, Modules.RadarMain, Modules.SE,
                        Modules.LauncherMain, Modules.ControlCenter]
    priority: Union[Priorities.LOW, Priorities.STANDARD, Priorities.HIGH]
    timeSend: int


@dataclass
class SEUpdateRocket(Message):
    rocket: Dict[int, List[float]]


@dataclass
class SEStarting(Message):
    planes: Dict[int, List[float]]


@dataclass
class PlaneKilled(Message):
    killed: Dict[str, Dict[int, List[float]]]
    collateralDamage: List[int]


@dataclass
class AddRocket(Message):
    rocket: Dict[int, List[float]]
