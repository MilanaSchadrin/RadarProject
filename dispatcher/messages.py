from dataclasses import dataclass
from typing import Union, Dict, List, Tuple
from dispatcher.enums import Priorities, Modules
from missile.Missile import Missile
from radar.Target import Target
import numpy as np
from numpy.typing import NDArray

@dataclass
class Message:
    recipient_id: Union[Modules, int]
    priority: Union[Priorities, int]


@dataclass
class SEStarting(Message):
    planes: Dict[int, NDArray[np.float64]]


@dataclass
class SEKilled(Message):
    collision_step: int
    rocket_id: int
    rocket_coords: NDArray[np.float64]
    plane_id: int
    plane_coords: NDArray[np.float64]
    collateral_damage: List[Tuple[int, NDArray[np.float64]]]

@dataclass
class SEAddRocket(Message):
    startTime: int
    rocket_id: int
    rocket_coords: NDArray[np.float64]

@dataclass
class SEAddRocketToRadar(Message):
    startTime: int
    planeId: int
    missile: Missile
    rocket_coords: NDArray[np.float64]

@dataclass
class CCLaunchMissile(Message):
    target: Target


@dataclass
class CCToRadarNewStatus(Message):
    new_target_status: Tuple[int]

@dataclass
class CCToSkyEnv(Message):
    missiles: List[Missile]

@dataclass
class RadarToGUICurrentTarget(Message):
    radar_id: int 
    target_id: int
    sector_size: int

@dataclass
class RadarControllerObjects(Message):
    detected_objects: List[Target]

@dataclass
class LaunchertoSEMissileLaunched(Message):
    targetId: int
    missile: Missile

@dataclass
class LaunchertoCCMissileLaunched(Message):
    missile: Missile

@dataclass
class ToGuiRocketInactivated(Message):
    rocketId: int