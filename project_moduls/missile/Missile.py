from common.commin import *
from enum import Enum
from typing import Tuple


class MissileType(Enum):
    TYPE_1 = 1
    TYPE_2 = 2


MISSILE_TYPE_CONFIG = {
     MissileType.TYPE_1: {
         "speed": 100, # абсолютная величина скорости
         "currLifeTime": 30,
         "damageRadius": 20
     },
     MissileType.TYPE_2: {
         "speed": 150,
         "currLifeTime": 20,
         "damageRadius": 25
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
        self.currentCoords: Tuple[float, float, float] = currentCoords
        self.velocity: Tuple[float, float, float] = velocity
        self.currLifeTime: int = currLifeTime
        self.damageRadius: float = damageRadius
        self.status: MissileStatus = status
        self.isDetected = False

    def updateCurrentCoords(self, newCoords: Tuple[float, float, float]):
        self.currentCoords = newCoords

    def updateSpeedVector(self, newSpeedVector: Tuple[float, float, float]):
        self.velocity = newSpeedVector