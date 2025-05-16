import random
import math
from typing import Dict, Tuple, List
from radar.Target import TargetStatus
from dispatcher.dispatcher import Dispatcher


class Radar:
    def __init__(self, radarController, dispatcher, radarId, position, maxRange, maxFollowedCount) -> None:
        self.radarController = radarController
        self.dispatcher: Dispatcher = dispatcher
        self.radarId: str = radarId
        self.position: Tuple[float, float, float] = (
            position[0] * 1000, position[1] * 1000, position[2] * 1000)
        self.maxRange: float = maxRange
        self.noiseLevel: float = random.uniform(0.01, 0.1)
        self.maxFollowedCount: int = maxFollowedCount
        self.followedTargets: Dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float], int]] = {}
        self.detectedTargets: Dict[str, Tuple[Tuple[float, float, float], Tuple[float, float, float]]] = {}
        self.detectedMissiles: Dict[str, Tuple[float, float, float]] = {}

    def isTargetInRange(self, current_coords):
        dx = current_coords[0] - self.position[0]
        dy = current_coords[1] - self.position[1]
        dz = current_coords[2] - self.position[2]
        distance = math.sqrt(dx ** 2 + dy ** 2 + dz ** 2)
        return (distance <= self.maxRange), (dx, dy, dz) if distance <= self.maxRange else (0, 0, 0)

    def _process_target(self, target_env, currentStep, followedTargetsNow):
        current_coords = target_env.getCurrentCoords(currentStep)
        current_speed_vec = target_env.getCurrentSpeedVec(currentStep)
        priority = target_env.priority
        status = self.radarController.allTargets[target_env.targetId].status

        inRange, local_coords = self.isTargetInRange(current_coords)

        if inRange:
            if status == TargetStatus.FOLLOWED and target_env.targetId not in followedTargetsNow:
                self.followedTargets[target_env.targetId] = (
                    self._add_noise_to_position(local_coords, self.noiseLevel * 0.1),
                    self._add_noise_to_speed(current_speed_vec, self.noiseLevel * 0.1),
                    priority
                )
            elif status != TargetStatus.DESTROYED:
                self.detectedTargets[target_env.targetId] = (
                    self._add_noise_to_position(local_coords, self.noiseLevel),
                    self._add_noise_to_speed(current_speed_vec, self.noiseLevel)
                )

            if len(self.followedTargets) > self.maxFollowedCount:
                sorted_list = sorted(self.followedTargets.items(), key=lambda x: x[1][2])
                targetId = sorted_list[self.maxFollowedCount][0]
                target = self.radarController.allEnvTargets[targetId]
                coords = target.getCurrentCoords(currentStep)
                speed = target.getCurrentSpeedVec(currentStep)
                _, loc = self.isTargetInRange(coords)
                self.detectedTargets[targetId] = (
                    self._add_noise_to_position(loc, self.noiseLevel),
                    self._add_noise_to_speed(speed, self.noiseLevel)
                )
                self.followedTargets = dict(sorted_list[:self.maxFollowedCount])

    def _process_missile(self, missile_env):
        coords = missile_env.getCurrentCoords()
        inRange, local_coords = self.isTargetInRange(coords)
        if inRange:
            self.detectedMissiles[missile_env.missileId] = self._add_noise_to_position(local_coords, self.noiseLevel * 0.1)

    def _add_noise_to_position(self, position, noise):
        return (position[0] + noise, position[1] + noise, position[2] + noise)

    def _add_noise_to_speed(self, speed, noise):
        return (speed[0] + noise, speed[1] + noise, speed[2] + noise)

    def scan(self, currentStep: int, followedTargetsNow: List) -> Tuple[dict, dict, dict]:
        self.followedTargets.clear()
        self.detectedTargets.clear()
        self.detectedMissiles.clear()

        for target_env in self.radarController.allEnvTargets.values():
            self._process_target(target_env, currentStep, followedTargetsNow)

        for missile_env in self.radarController.allEnvMissiles.values():
            self._process_missile(missile_env)

        return self.followedTargets, self.detectedTargets, self.detectedMissiles
