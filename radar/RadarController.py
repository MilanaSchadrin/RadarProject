from enum import Enum
from typing import Dict, Tuple, List
from radar.Target  import TargetStatus, Target, TargetEnv
from radar.Radar import Radar
from dispatcher.messages import (
    CCToRadarNewStatus,
    RadarToGUICurrentTarget,
    RadarControllerObjects,
    SEKilled,
    SEStarting,
    SEAddRocketToRadar,
)
from missile.Missile import Missile
from dispatcher.dispatcher import Dispatcher

class MissileEnv:
    """Класс для хранения реальных координат ракеты, полученных от SkyEnv."""
    def __init__(
        self,
        missileId: str,
        targetId: str,
        clearCoords: List[Tuple[float, float, float]],
    ) -> None:
        self.missileId: str = missileId
        self.targetId: str = targetId
        self.clearCoords: List[Tuple[float, float, float]] = clearCoords

    def getCurrentCoords(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущие координаты ракеты на указанном шаге."""
        return self.clearCoords[step]

    def getCurrentSpeedVec(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущий вектор скорости ракеты."""
        return (
            self.clearCoords[step + 1][0] - self.clearCoords[step][0],
            self.clearCoords[step + 1][1] - self.clearCoords[step][1],
            self.clearCoords[step + 1][2] - self.clearCoords[step][2],
        )

class RadarController:
    """Контроллер радаров, обрабатывающий сообщения от системы моделирования."""

    def __init__(self, dispatcher: Dispatcher) -> None:
        self.dispatcher: Dispatcher = dispatcher
        self.radars: Dict[str, Radar] = {}
        self.allTargets: Dict[str, TargetEnv] = {}
        self.allMissiles: Dict[str, MissileEnv] = {}
        self.detectedTargets: Dict[str, Target] = {}

    def addRadar(self, radar: Radar) -> None:
        """Добавляет радар под управление контроллера."""
        self.radars[radar.radarId] = radar

    def update(self, step: int) -> None:
        """Обновляет состояние всех радаров, текущие координаты всех целей и ракет."""
        for radar in self.radars.values():
            radar.scan(step)

    def addDetectedTarget(self, target: Target) -> None:
        """Добавляет цель в список обнаруженных целей."""
        self.detectedTargets[target.targetId] = target

    def processMessage(self) -> None:
        """Обрабатывает входящие сообщения."""
        messages = self.dispatcher.getMessages()
        for message in messages:
            if isinstance(message, CCToRadarNewStatus):
                self.updateStatus(message)
            elif isinstance(message, SEKilled):
                self.killObject(message)
            elif isinstance(message, SEStarting):
                self.start(message)
            elif isinstance(message, SEAddRocketToRadar):
                self.addRocket(message)

    def updateStatus(self, message: CCToRadarNewStatus) -> None:
        """Обновляет статус цели."""
        objectId, newStatus = message.targetNewStatus
        if objectId in self.detectedTargets:
            self.detectedTargets[objectId].updateStatus(newStatus)

    def killObject(self, message: SEKilled) -> None:
        """Обновляет статус цели на DESTROYED и отвязывает уничтоженную ракету."""
        killRocketId = message.rocketId
        killTargetId = message.planeId
        
        if killTargetId in self.detectedTargets:
            killedTarget = self.detectedTargets[killTargetId]
            killedTarget.updateStatus(TargetStatus.DESTROYED)
            
            if killRocketId in killedTarget.attachedMissiles:
                killedTarget.detachMissile(killRocketId)
                
            if not killedTarget.attachedMissiles:
                self.detectedTargets.pop(killTargetId)

    def start(self, message: SEStarting) -> None:
        """Получает начальные данные о целях в небе."""
        for targetId, targetCoords in message.planes.items():
            self.allTargets[targetId] = TargetEnv(targetId, targetCoords)

    def addRocket(self, message: SEAddRocketToRadar) -> None:
        """Добавляет новую ракету в список всех ракет."""
        missileEnv = MissileEnv(
            message.missile.missileId,
            message.planeId,
            message.rocketCoords
        )
        self.allMissiles[message.missile.missileId] = missileEnv

    def sendCurrentTarget(
        self,
        radarId: str,
        targetId: str,
        sectorSize: float
    ) -> None:
        """Отправляет сообщение о сопровождаемой цели."""
        message = RadarToGUICurrentTarget(radarId, targetId, sectorSize)
        self.dispatcher.sendMessage(message)

    def sendDetectedObjects(self) -> None:
        """Отправляет список обнаруженных целей."""
        message = RadarControllerObjects(detectedObjects=self.detectedTargets)
        self.dispatcher.sendMessage(message)

    
