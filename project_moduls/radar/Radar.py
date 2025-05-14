import random
import math

from typing import Dict, Tuple, List
from radar.Target import TargetStatus, Target
from dispatcher.dispatcher import Dispatcher


class Radar:
    """Класс радара"""
    
    def __init__(self, radarController, dispatcher, radarId, position, maxRange, maxFollowedCount) -> None:
        self.radarController = radarController
        self.dispatcher: Dispatcher = dispatcher
        self.radarId: str = radarId
        self.position: Tuple[float, float, float] = (position[0]*1000,position[1]*1000,position[2]*1000)
        print(self.position)
        self.maxRange: float = maxRange
        self.noiseLevel: float = random.uniform(0.01, 0.1)

        self.maxFollowedCount: int = maxFollowedCount
        self.followedTargets: Dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float], int]] = {}
        self.detectedTargets: Dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = {}
        self.detectedMissiles: Dict[str, Tuple[float, float, float]] = {}
        

    def isTargetInRange(self, current_coords):
        """Проверяет, находится ли объект в зоне действия радара."""

        dx = current_coords[0] - self.position[0]
        dy = current_coords[1] - self.position[1]
        dz = current_coords[2] - self.position[2]
        
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        

        if (distance <= self.maxRange):
            #print(distance,self.maxRange,True)
            return True, (dx, dy, dz)
        else:
            #print(distance,self.maxRange,False)
            return False, (0, 0, 0)

    def _process_target(self, target_env, currentStep, followedTargetsNow):
        """Обрабатывает цель"""
        target = target_env
        current_coords = target.getCurrentCoords(currentStep)
        current_speed_vec = target.getCurrentSpeedVec(currentStep)
        priority = target.priority
        status = self.radarController.allTargets[target.targetId].status

        isTargetInRange, local_coords = self.isTargetInRange(current_coords)

        if isTargetInRange:
            if status == TargetStatus.FOLLOWED and target.targetId not in followedTargetsNow:
                noise_coords = self._add_noise_to_position(local_coords, self.noiseLevel * 0.1)
                noise_speed_vec = self._add_noise_to_speed(current_speed_vec, self.noiseLevel * 0.1)
                
                self.followedTargets[target.targetId] = (noise_coords, noise_speed_vec, priority)

            elif status != TargetStatus.DESTROYED:
                noise_coords = self._add_noise_to_position(local_coords, self.noiseLevel)
                noise_speed_vec = self._add_noise_to_speed(current_speed_vec, self.noiseLevel)
                self.detectedTargets[target.targetId] = (noise_coords, noise_speed_vec)

            if len(self.followedTargets) > self.maxFollowedCount:
                sorted_list = sorted(self.followedTargets.items(), key=lambda x: x[1][2])
                
                targetId = sorted_list[self.maxFollowedCount][0]

                target = self.radarController.allEnvTargets[targetId]
                current_coords = target.getCurrentCoords(currentStep)
                current_speed_vec = target.getCurrentSpeedVec(currentStep)

                isTargetInRange, local_coords = self.isTargetInRange(current_coords)
                
                noise_coords = self._add_noise_to_position(local_coords, self.noiseLevel)
                noise_speed_vec = self._add_noise_to_speed(current_speed_vec, self.noiseLevel)
                self.detectedTargets[targetId] = (noise_coords, noise_speed_vec) 

                sorted_list.pop(self.maxFollowedCount)

                self.followedTargets = dict(sorted_list)        

    def _process_missile(self, missile_env):
        """Обрабатывает ракету"""

        missile = missile_env
        current_coords = missile.getCurrentCoords()

        isMissileInRange, local_coords = self.isTargetInRange(current_coords)

        if isMissileInRange:
            noise_coords = self._add_noise_to_position(local_coords, self.noiseLevel* 0.1)
            self.detectedMissiles[missile.missileId] = noise_coords

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

    def scan(self, currentStep: int, followedTargetsNow:List) -> None:
        """Основная функция сканирования"""

        self.followedTargets.clear() 
        self.detectedTargets.clear()
        self.detectedMissiles.clear()

        # Обработка целей
        for target_env in self.radarController.allEnvTargets.values():
            self._process_target(target_env, currentStep, followedTargetsNow)

        # Обработка ракет
        for missile_env in self.radarController.allEnvMissiles.values():
            self._process_missile(missile_env) 

        return self.followedTargets, self.detectedTargets, self.detectedMissiles