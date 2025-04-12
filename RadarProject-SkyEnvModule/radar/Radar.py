import random
import math

from typing import Dict, Tuple, List
from radar.Target import TargetStatus, Target
from dispatcher.dispatcher import Dispatcher


class Radar:
    """Класс радара. Еще не доделан"""

    def __init__(self, radarController, dispatcher, radarId,position,maxRange,coneAngleDeg,maxTargetCount,noiseLevel) -> None:
        self.radarController = radarController
        self.dispatcher: Dispatcher = dispatcher
        self.radarId: str = radarId
        self.position: Tuple[float, float, float] = position
        self.maxRange: float = maxRange
        self.coneAngleDeg: float = coneAngleDeg
        self.detectedObjects: Dict[str, Target] = {}
        self.maxTargetCount: int = maxTargetCount
        self.currentTargetCount: int = 0
        self.noiseLevel: float = noiseLevel
        self.followedTargets: Dict[str, Target] = {}

    def isTargetInRange(self, target: Target) -> bool:
        """Проверяет, находится ли цель в зоне действия радара."""
        targetPosition = target.currentCoords
        if targetPosition[2] < 0:
            return False

        dx = targetPosition[0] - self.position[0]
        dy = targetPosition[1] - self.position[1]
        dz = targetPosition[2] - self.position[2]
        
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        if distance > self.maxRange:
            return False

        if dz <= 0:
            return False

        horizontalDistance = math.sqrt(dx**2 + dy**2)
        angleRad = math.atan(horizontalDistance / dz)
        coneAngleRad = math.radians(self.coneAngleDeg) / 2
        
        return angleRad <= coneAngleRad

    def scan(self, currentStep: int) -> None:
        """Выполняет сканирование зоны на указанном шаге моделирования."""
        objectsData = self.dispatcher.getObjectsData()
        validTargets = [
            objId for objId, (startStep, _) in objectsData.items()
            if startStep <= currentStep and self.isTargetInRange(objectsData[objId])
        ]
        
        followedTargets = self.radarController.getFollowedTargets()
        
        for objId in validTargets:
            targetData = objectsData[objId]
            currentPos = self._getCurrentPosition(targetData, currentStep)
            currentSpeed = self._getCurrentSpeed(targetData, currentStep)
            
            noise = (random.random() - 0.5) * self.noiseLevel
            noisyPos = (
                currentPos[0] + noise,
                currentPos[1] + noise,
                currentPos[2] + noise
            )
            
            if objId in self.detectedObjects:
                target = self.detectedObjects[objId]
                target.updateCurrentCoords(noisyPos)
                target.updateSpeedVector(currentSpeed)
                
                if objId in followedTargets:
                    target.updateStatus(TargetStatus.FOLLOWED)
                    self.followedTargets[objId] = target
            else:
                newTarget = targetData.__class__(
                    targetId=objId,
                    coords=noisyPos,
                    speedVector=currentSpeed
                )
                self.detectedObjects[objId] = newTarget
                
                if objId in followedTargets:
                    newTarget.updateStatus(TargetStatus.FOLLOWED)
                    self.followedTargets[objId] = newTarget
                    self.currentTargetCount += 1

        self._removeOutdatedTargets(validTargets)

    def _getCurrentPosition(
        self, 
        targetData: Tuple[int, List[Tuple[float, float, float]]],
        currentStep: int
    ) -> Tuple[float, float, float]:
        """Возвращает позицию цели на текущем шаге."""
        startStep, coords = targetData
        idx = currentStep - startStep
        return coords[idx]

    def _getCurrentSpeed(
        self,
        targetData: Tuple[int, List[Tuple[float, float, float]]],
        currentStep: int
    ) -> Tuple[float, float, float]:
        """Возвращает вектор скорости на текущем шаге."""
        startStep, coords = targetData
        idx = currentStep - startStep
        nextIdx = idx + 1 if idx + 1 < len(coords) else idx
        
        return (
            coords[nextIdx][0] - coords[idx][0],
            coords[nextIdx][1] - coords[idx][1],
            coords[nextIdx][2] - coords[idx][2]
        )

    def _removeOutdatedTargets(self, validTargetIds: List[str]) -> None:
        """Удаляет цели, которые больше не в зоне действия."""
        for targetId in list(self.detectedObjects.keys()):
            if (targetId not in validTargetIds and 
                self.detectedObjects[targetId].canBeRemoved()):
                self.detectedObjects.pop(targetId)
                if targetId in self.followedTargets:
                    self.followedTargets.pop(targetId)
                    self.currentTargetCount -= 1

    def getDetectedObjects(self) -> Dict[str, Target]:
        """Возвращает обнаруженные цели."""
        return self.detectedObjects

    def trackTarget(self, targetId: str) -> None:
        """Начинает сопровождение цели."""
        if targetId in self.detectedObjects:
            target = self.detectedObjects[targetId]
            target.updateStatus(TargetStatus.FOLLOWED)
            self.followedTargets[targetId] = target
            self.currentTargetCount += 1

    def markTargetAsDestroyed(self, targetId: str) -> None:
        """Помечает цель как уничтоженную."""
        if targetId in self.detectedObjects:
            target = self.detectedObjects[targetId]
            target.updateStatus(TargetStatus.DESTROYED)
            
            if targetId in self.followedTargets:
                self.followedTargets.pop(targetId)
                self.currentTargetCount -= 1
            
            if target.canBeRemoved():
                self.detectedObjects.pop(targetId)