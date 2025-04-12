from enum import Enum
from common.commin import *

from typing import Tuple


class MissileStatus(Enum):
    ACTIVE = 1  # ракета ещё нужна
    INACTIVE = 0  # ракета больше не нужна


class Missile:
    def __init__(self, missileID, velocity, currentCoords, startTime, damageRadius, status=MissileStatus.ACTIVE):
        self.missileID: str = missileID
        self.velocity: Tuple[float, float, float] = velocity
        self.currentCoords: Tuple[float, float, float] = currentCoords
        self.currLifeTime: int = startTime
        self.damageRadius: float = damageRadius
        self.status: MissileStatus = status
