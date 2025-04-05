import Point
from enum import Enum

class MissileStatus(Enum):
    ACTIVE = 1  # ракета ещё нужна
    INACTIVE = 0  # ракета больше не нужна



class Missile:
    def __init__(self, missileID, velocity, currentPosition, startTime, damageRadius, status=MissileStatus.ACTIVE):
        self.missileID = missileID
        self.velocity = velocity
        self.currentPosition = currentPosition
        self.currLifeTime = startTime
        self.damageRadius = damageRadius
        self.status = status
