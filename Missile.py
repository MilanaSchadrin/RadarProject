import Point

class Missile:
    def __init__(self, missileId, startPoint, endPoint, currentPosition, startTime, damageRadius):
        self.missileId = missileId
        self.startPoint = startPoint
        self.endPoint = endPoint
        self.currentPosition = currentPosition
        self.currLifeTime = startTime
        self.damageRadius = damageRadius