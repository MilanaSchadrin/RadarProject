from typing import Dict, Tuple, List
from radar.Target import TargetStatus, Target
from radar.Radar import Radar
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import Modules,Priorities
from dispatcher.messages import (
    CCToRadarNewStatus,
    RadarToGUICurrentTarget,
    RadarControllerObjects,
    SEKilled,
    SEStarting,
    SEAddRocketToRadar,
)

class TargetEnv:
    """Класс для хранения реальных координат цели, полученных от SkyEnv."""

    def __init__(self, targetId: str, clearCoords: List[Tuple[float, float, float]]) -> None:
        self.targetId: str = targetId
        self.clearCoords: List[Tuple[float, float, float]] = clearCoords
        self.isFollowed = False

    def getCurrentCoords(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущие координаты цели на указанном шаге."""
        return self.clearCoords[step]

    def getCurrentSpeedVec(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущий вектор скорости цели."""
        return (
            self.clearCoords[step + 1][0] - self.clearCoords[step][0],
            self.clearCoords[step + 1][1] - self.clearCoords[step][1],
            self.clearCoords[step + 1][2] - self.clearCoords[step][2],
        )


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
        self.sendDetectedObjects()
        self.processMessage()

    def addDetectedTarget(self, target: Target) -> None:
        """Добавляет цель в список обнаруженных целей."""
        self.detectedTargets[target.targetId] = target

    def processMessage(self) -> None:
        """Обрабатывает входящие сообщения."""
        message_queue = self.dispatcher.get_message(Modules.RadarMain)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:
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
        objectId, priority = message.new_target_status
        if objectId in self.detectedTargets:
            self.detectedTargets[objectId].updateStatus(TargetStatus.FOLLOWED)
            self.detectedTargets[objectId].priority = priority

    def killObject(self, message: SEKilled) -> None:
        """Обновляет статус цели на DESTROYED и отвязывает уничтоженную ракету."""
        killRocketId = message.rocket_id
        killTargetId = message.plane_id
        
        if killTargetId in self.detectedTargets:
            killedTarget = self.detectedTargets[killTargetId]
            killedTarget.updateStatus(TargetStatus.DESTROYED)
            
            if killRocketId in killedTarget.attachedMissiles:
                killedTarget.detachMissile(killRocketId)
                
            if not killedTarget.attachedMissiles:
                self.detectedTargets.pop(killTargetId)
                self.allTargets.pop(killTargetId)
                self.allMissiles.pop(killRocketId)

    def start(self, message: SEStarting) -> None:
        """Получает начальные данные о целях в небе."""
        for targetId, targetCoords in message.planes.items():
            self.allTargets[targetId] = TargetEnv(targetId, targetCoords)

    def addRocket(self, message: SEAddRocketToRadar) -> None:
        """Добавляет новую ракету в список всех ракет."""
        missileEnv = MissileEnv(
            message.missile.missileID,
            message.planeId,
            message.rocket_coords
        )
        self.allMissiles[message.missile.missileID] = missileEnv

    def sendCurrentTarget(
        self,
        radarId: str,
        targetId: str,
        sectorSize: float
    ) -> None:
        """Отправляет сообщение о сопровождаемой цели."""
        message = RadarToGUICurrentTarget(Modules.GUI,Priorities.STANDARD, radarId, targetId, sectorSize)
        self.dispatcher.send_message(message)

    def sendDetectedObjects(self) -> None:
        """Отправляет список обнаруженных целей."""
        message = RadarControllerObjects(Modules.ControlCenter,Priorities.LOW,self.detectedTargets)
        self.dispatcher.send_message(message)

    