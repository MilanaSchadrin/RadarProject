import random
import math

from typing import Dict, Tuple, List
from radar.Target import TargetStatus, Target
from dispatcher.dispatcher import Dispatcher


class Radar:
    """Класс радара"""
    
    def __init__(self, radarController, dispatcher, radarId, position, maxRange, coneAngleDeg, maxFollowedCount) -> None:
        self.radarController = radarController
        self.dispatcher: Dispatcher = dispatcher
        self.radarId: str = radarId
        self.position: Tuple[float, float, float] = position
        self.maxRange: float = maxRange
        self.coneAngleDeg: float = coneAngleDeg
        self.maxFollowedCount: int = maxFollowedCount
        self.currentTargetCount: int = 0
        self.followedTargets: Dict[str, Target] = {}
        self.noiseLevel: float = random.uniform(0.1, 1)

    def isTargetInRange(self, target, currentStep) -> bool:
        """Проверяет, находится ли цель в зоне действия радара."""
        targetPosition = target.getCurrentCoords(currentStep)
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

    def _process_target(self, target_id, target_env, currentStep):
        """Обрабатывает обнаруженную цель"""
        noise = self.noiseLevel
        if target_id in self.radarController.detectedTargets:
            target = self.radarController.detectedTargets[target_id]
            if target.status == TargetStatus.FOLLOWED and target_env.isFollowed == False:
                if self.currentTargetCount < self.maxFollowedCount:
                    target_env.isFollowed = True
                    self.currentTargetCount += 1
                    self.followedTargets[target_id] = target
                    self.radarController.sendCurrentTarget(self.radarId, target_id, self.coneAngleDeg)

                else:
                    self.followedTargets[target_id] = target
                    min_priority_target = max(self.followedTargets.values(), key=lambda x: x.priority)
                    self.followedTargets.pop(min_priority_target.targetId)
                    self.radarController.detectedTargets[min_priority_target.targetId].updateStatus(TargetStatus.DETECTED)
                    #isFollowed needed
                    self.radarController.allTargets[min_priority_target.targetId].isFollowed  = False
                    if target_id in self.followedTargets:
                        target_env.isFollowed = True
                        self.radarController.sendCurrentTarget(self.radarId, target_id, self.coneAngleDeg)          

                noise = 0.1 * self.noiseLevel
        else: 
            target = Target(target_id)
            self.radarController.addDetectedTarget(target)

        currentPos = target_env.getCurrentCoords(currentStep)
        noisyPos = self._add_noise_to_position(currentPos, noise)

        speedVector = target_env.getCurrentSpeedVec(currentStep)
        noisySpeedVector = self._add_noise_to_speed(speedVector, noise)

        target.updateCurrentCoords(noisyPos)
        target.updateSpeedVector(noisySpeedVector)
        return target

    def _process_missile(self, missile_id, missile_env, currentStep):
        """Обрабатывает обнаруженную ракету"""
        noise = self.noiseLevel
        missile = self.radarController.detectedTargets[missile_env.targetId].attachedMissiles[missile_id]

        currentPos = missile_env.getCurrentCoords(currentStep)
        noisyPos = self._add_noise_to_position(currentPos, noise)

        speedVector = missile_env.getCurrentSpeedVec(currentStep)
        noisySpeedVector = self._add_noise_to_speed(speedVector, noise)

        missile.updateCurrentCoords(noisyPos)
        missile.updateSpeedVector(noisySpeedVector)
        return missile

    def _add_noise_to_position(self, position, noise):
        """Добавляет шум к координатам позиции"""
        return (
            position[0] + noise,
            position[1] + noise,
            position[2] + noise
        )

    def _add_noise_to_speed(self, speed, noise):
        """Добавляет шум к вектору скорости"""
        return (
            speed[0] + noise,
            speed[1] + noise,
            speed[2] + noise
        )

    def scan(self, currentStep: int) -> None:
        """Основная функция сканирования"""
        #dict not list
        self.followedTargets.clear() 
        self.currentTargetCount = 0

        # Обработка целей
        for target_id, target_env in self.radarController.allTargets.items():
            if self.isTargetInRange(target_env, currentStep):
                self._process_target(target_id, target_env, currentStep)
        # Обработка ракет
        for missile_id, missile_env in self.radarController.allMissiles.items():
            if self.isTargetInRange(missile_env, currentStep):
                self._process_missile(missile_id, missile_env, currentStep)  