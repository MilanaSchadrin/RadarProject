from dataclasses import dataclass
from typing import Union, Dict, List, Tuple
from dispatcher.enums import Priorities, Modules
from missile.Missile import Missile
from radar.Target import Target
import numpy as np
from numpy.typing import NDArray

@dataclass(order=True) 
class Message:
    recipient_id: Union[Modules, int]
    priority: Union[Priorities, int]

@dataclass
class SEStarting(Message):
    planes: Dict[int, NDArray[np.float64]]

@dataclass
class SEKilled(Message):
    rocket_id: int
    rocket_coords: NDArray[np.float64]
    plane_id: int
    plane_coords: NDArray[np.float64]
    collateral_damage: List[Tuple[int, NDArray[np.float64]]]

@dataclass
class SEKilledGUI(Message):
    rocket_id: int
    rocket_coords: NDArray[np.float64]
    death_range: int
    plane_id: int
    plane_coords: NDArray[np.float64]
    collateral_damage: List[Tuple[int, NDArray[np.float64]]]
    
@dataclass
class RocketInactivated(Message):
    rocket_id:int
    timeStep:int

@dataclass
class SEAddRocket(Message):
    rocket_id: int
    rocket_coords: NDArray[np.float64]

@dataclass
class SEAddRocketToRadar(Message):
    planeId: int
    missile: Missile
    rocket_coords: NDArray[np.float64]

@dataclass
class CCLaunchMissile(Message):
    target: Target

@dataclass(order=True) 
class CCToRadarNewStatus(Message):
    priority_s: int
    new_target_status: Tuple[int, int]

@dataclass
class CCToSkyEnv(Message):
    missiles: List[Missile]

@dataclass
class RadarToGUICurrentTarget(Message):
    radar_id: str
    target_id: str
    sector_size: float

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

@dataclass
class RocketUpdate(Message):
    rocket_id:int
    rocket_coords:Tuple

@dataclass
class TargetUnfollowedGUI(Message): 
    radarId:str
    targetId:str

@dataclass
class RocketDied(Message): 
     planeId: int
     rocketId: int