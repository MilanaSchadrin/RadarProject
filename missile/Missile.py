from common.commin import *
from enum import Enum
from typing import Tuple


class MissileType(Enum):
    TYPE_1 = 1
    TYPE_2 = 2


MISSILE_TYPE_CONFIG = {
     MissileType.TYPE_1: {
         "speed": 300, # абсолютная величина скорости
         "currLifeTime": 1000,
         "damageRadius": 500
     },
     MissileType.TYPE_2: {
         "speed": 400,
         "currLifeTime": 1000,
         "damageRadius": 500
     }
 }

class MissileStatus(Enum):
    ACTIVE = 1  # ракета ещё нужна
    INACTIVE = 0  # ракета больше не нужна


class Missile:
    def __init__(self, missileID: str, missileType: MissileType, currentCoords: Tuple[float, float, float], velocity: Tuple[float, float, float], currLifeTime: int, damageRadius:int, status=MissileStatus.ACTIVE):
        config = MISSILE_TYPE_CONFIG[missileType]

        self.missileID: str = missileID
        self.missileType: MissileType = missileType
        self.currentCoords: Tuple[float, float, float] = tuple(currentCoords[:3]) if len(currentCoords) > 3 else tuple(currentCoords)
        self.velocity: Tuple[float, float, float] = tuple(velocity[:3]) if len(velocity) > 3 else tuple(velocity)
        self.currLifeTime: int = currLifeTime
        self.damageRadius: float = damageRadius
        self.status: MissileStatus = status

    def updateCurrentCoords(self, newCoords: Tuple[float, float, float]):
        self.currentCoords = tuple(newCoords[:3]) if len(newCoords) > 3 else tuple(newCoords)

    def updateSpeedVector(self, newSpeedVector: Tuple[float, float, float]):
        self.velocity = tuple(newSpeedVector[:3]) if len(newSpeedVector) > 3 else tuple(newSpeedVector)