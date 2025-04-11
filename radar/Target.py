from enum import Enum
from typing import Dict, Tuple, List
from missile.Missile import Missile


class TargetStatus(Enum):
    """Статусы цели для системы слежения."""
    DESTROYED = 0
    DETECTED = 1
    FOLLOWED = 2


class Target:
    """Базовый класс для всех объектов, обнаруживаемых радаром."""
    def __init__(
        self,
        targetId: str,
        status: TargetStatus = TargetStatus.DETECTED,
    ) -> None:
        self.targetId: str = targetId
        self.status: TargetStatus = status
        self.currentCoords: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.currentSpeedVector: Tuple[float, float, float] = (0.0, 0.0, 0.0)
        self.attachedMissiles: Dict[str, Missile] = {}

    def updateCurrentCoords(self, newCoords: Tuple[float, float, float]) -> None:
        """Обновить текущие координаты."""
        self.currentCoords = newCoords

    def updateSpeedVector(self, newSpeedVector: Tuple[float, float, float]) -> None:
        """Обновить текущий вектор скорости."""
        self.currentSpeedVector = newSpeedVector

    def updateStatus(self, newStatus: TargetStatus) -> None:
        """Обновляет статус объекта."""
        self.status = newStatus

    def attachMissile(self, missile: Missile) -> None:
        """Добавляет ракету к списку привязанных."""
        self.attachedMissiles[missile.missileId] = missile

    def detachMissile(self, missileId: str) -> None:
        """Удаляет ракету из списка привязанных."""
        if missileId in self.attachedMissiles:
            self.attachedMissiles.pop(missileId)

class TargetEnv:
    """Класс для хранения реальных координат цели, полученных от SkyEnv."""

    def __init__(self, targetId: str, clearCoords: List[Tuple[float, float, float]]) -> None:
        self.targetId: str = targetId
        self.clearCoords: List[Tuple[float, float, float]] = clearCoords

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