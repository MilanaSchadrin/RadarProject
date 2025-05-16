from typing import Dict, Tuple, List, Optional
from radar.Target import TargetStatus, Target
from radar.Radar import Radar
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import Modules, Priorities
from missile.Missile import Missile
from dispatcher.messages import (
    CCToRadarNewStatus,
    RadarToGUICurrentTarget,
    RadarControllerObjects,
    SEKilled,
    SEStarting,
    SEAddRocketToRadar,
    RocketUpdate,
    TargetUnfollowedGUI,
    RocketDied
)

class TargetEnv:
    def __init__(self, targetId: str, clearCoords: List[Tuple[float, float, float]]) -> None:
        self.targetId: str = targetId
        self.clearCoords: List[Tuple[float, float, float]] = clearCoords
        self.isFollowed = False
        self.priority: int = 1000000
        self.lastDetectedBy: Optional[str] = None
        self.lastKnownCoords: Tuple[float, float, float] = (0, 0, 0)

    def getCurrentCoords(self, step: int) -> Tuple[float, float, float]:
        return self.clearCoords[step-1]

    def getCurrentSpeedVec(self, step: int) -> Tuple[float, float, float]:
        return (
            self.clearCoords[step][0] - self.clearCoords[step-1][0],
            self.clearCoords[step][1] - self.clearCoords[step-1][1],
            self.clearCoords[step][2] - self.clearCoords[step-1][2],
        )

class MissileEnv:
    def __init__(self, missileId: str, targetId: str, currentCoords: Tuple[float, float, float]) -> None:
        self.missileId: str = missileId
        self.targetId: str = targetId
        self.currentCoords: Tuple[float, float, float] = currentCoords

    def getCurrentCoords(self):
        return self.currentCoords

    def updateCoords(self, missile_coords):
        self.currentCoords = missile_coords

class RadarController:
    def __init__(self, dispatcher) -> None:
        self.dispatcher: Dispatcher = dispatcher
        self.radars: Dict[str, Radar] = {}
        self.allEnvTargets: Dict[str, TargetEnv] = {}
        self.allEnvMissiles: Dict[str, MissileEnv] = {}
        self.allTargets: Dict[str, Target] = {}

    def addRadar(self, radar: Radar) -> None:
        self.radars[radar.radarId] = radar

    def getAbsoluteCoords(self, radar, local_coords):
        return (
            local_coords[0] + radar.position[0],
            local_coords[1] + radar.position[1],
            local_coords[2] + radar.position[2]
        )

    def update(self, step: int) -> None:
        # Удаление уничтоженных целей
        destroyed_targets = [
            target_id for target_id, target in self.allTargets.items()
            if target.status == TargetStatus.DESTROYED
        ]

        for target_id in destroyed_targets:
            target = self.allTargets[target_id]
            for missile_id in list(target.attachedMissiles.keys()):
                self.allEnvMissiles.pop(missile_id, None)
                target.detachMissile(missile_id)
            self.allEnvTargets.pop(target_id, None)
            self.allTargets.pop(target_id, None)

        self.processMessage()
        
        # Сохраняем предыдущее состояние всех целей
        previous_status = {}
        for target_id, target in self.allTargets.items():
            env_target = self.allEnvTargets.get(target_id)
            if env_target:
                previous_status[target_id] = {
                    'status': target.status,
                    'radar_id': env_target.lastDetectedBy,
                    'is_followed': env_target.isFollowed,
                    'coords': env_target.lastKnownCoords
                }

        temp_targets = list(self.allEnvTargets.keys())
        followed_targets_now = []
        newly_detected = set()

        radar_follow_counts = {radar.radarId: 0 for radar in self.radars.values()}
        alreadySent = set()

        # Обработка сопровождаемых целей
        for radar in self.radars.values():
            followedTargets, _, _ = radar.scan(step, followed_targets_now)
            
            for target_id, (local_coords, speed_vec, priority) in followedTargets.items():
                if target_id not in temp_targets:
                    continue
                if radar_follow_counts[radar.radarId] >= radar.maxFollowedCount:
                    continue
                target = self.allTargets[target_id]
                env_target = self.allEnvTargets[target_id]
                prev_status = previous_status.get(target_id, {})
                
                # Обновляем информацию о цели
                abs_coords = self.getAbsoluteCoords(radar, local_coords)
                env_target.lastKnownCoords = abs_coords
                env_target.lastDetectedBy = radar.radarId
                env_target.isFollowed = True
                env_target.priority = priority
                
                target.currentCoords = abs_coords
                target.currentSpeedVector = speed_vec
                target.status = TargetStatus.FOLLOWED
                target.priority = priority
                
                # Проверяем, была ли цель обнаружена другим радаром
                if (radar.radarId, target_id) not in alreadySent:
                    self.sendCurrentTarget(radar.radarId, target_id, radar.maxRange)
                    alreadySent.add((radar.radarId, target_id))
                
                radar_follow_counts[radar.radarId] += 1
                temp_targets.remove(target_id)
                followed_targets_now.append(target_id)
                newly_detected.add(target_id)

        # Обработка обнаруженных (но не сопровождаемых) целей
        for radar in self.radars.values():
            _, detectedTargets, _ = radar.scan(step, followed_targets_now)
            
            for target_id, (local_coords, speed_vec) in detectedTargets.items():
                if target_id not in temp_targets:
                    continue

                if radar_follow_counts[radar.radarId] >= radar.maxFollowedCount:
                    continue
                    
                target = self.allTargets[target_id]
                env_target = self.allEnvTargets[target_id]
                prev_status = previous_status.get(target_id, {})
                
                # Обновляем информацию о цели
                abs_coords = self.getAbsoluteCoords(radar, local_coords)
                env_target.lastKnownCoords = abs_coords
                env_target.lastDetectedBy = radar.radarId
                env_target.isFollowed = False
                
                target.currentCoords = abs_coords
                target.currentSpeedVector = speed_vec
                target.status = TargetStatus.DETECTED
                
                # Если цель перешла от другого радара
                if not prev_status.get('is_followed', False) and env_target.priority < 500:
                    if (radar.radarId, target_id) not in alreadySent:
                        print(f"[AUTO-FOLLOW] Цель {target_id} подхвачена радаром {radar.radarId}")
                        self.sendCurrentTarget(radar.radarId, target_id, radar.maxRange)
                        alreadySent.add((radar.radarId, target_id))
                        env_target.isFollowed = True
                        target.status = TargetStatus.FOLLOWED
                        radar_follow_counts[radar.radarId] += 1
                        followed_targets_now.append(target_id)
                
                temp_targets.remove(target_id)
                newly_detected.add(target_id)

        # Обработка ракет
        for target in self.allTargets.values():
            for missile in target.attachedMissiles.values():
                missile.isDetected = False # сначала у всех ракет статус "не обнаружена"
                # missile.currentCoords = (0, 0, 0) теперь не обнуляем координаты

        all_detected_missiles = {}
        for radar in self.radars.values():
            _, _, detected_missiles = radar.scan(step, [])
            for missile_id, coords in detected_missiles.items():
                all_detected_missiles[missile_id] = (radar, coords)

        # обрабатываем все ракеты. Если ракета если в списке замеченных, ставим isDetected = True и \
        # missile.currentCoords = абсолютные координаты с ошибкой
        # если ракеты нет в списке обнаруженных, ставим missile.currentCoords = последней координате, которая пришла от SkyEnv
        for missile_id, missile_env in self.allEnvMissiles.items():
            target_id = missile_env.targetId
            if target_id in self.allTargets:
                missile = self.allTargets[target_id].attachedMissiles.get(missile_id)
                if missile:
                    if missile_id in all_detected_missiles:
                        (radar, coords) = all_detected_missiles[missile_id]  
                        missile.currentCoords = self.getAbsoluteCoords(radar, coords)
                        missile.isDetected = True # если в  списке замеченных, меняем статус  на True
                    else:
                        missile.currentCoords = missile_env.getCurrentCoords()

        # Обработка целей, которые больше не обнаруживаются
        for target_id in temp_targets:
            target = self.allTargets[target_id]
            env_target = self.allEnvTargets[target_id]
            prev_status = previous_status.get(target_id, {})
            
            if prev_status.get('status') in [TargetStatus.FOLLOWED, TargetStatus.DETECTED]:
                target.status = TargetStatus.UNDETECTED
                # target.currentCoords = (0, 0, 0) - теперь координаты не зануляются
                # ставим координаты, которые получили от SkyEnv на данном шаге
                target.currentCoords = self.allEnvTargets[target_id].getCurrentCoords(step)
                target.currentSpeedVector = self.allEnvTargets[target_id].getCurrentSpeedVec(step)
                if env_target.isFollowed:
                    env_target.isFollowed = False
                    any_radar = next(iter(self.radars.values()))
                    self.sendUnfollowedGUI(any_radar.radarId, target_id)

        self.sendAllObjects()

    # Остальные методы остаются без изменений
    def addDetectedTarget(self, target: Target) -> None:
        self.allTargets[target.targetId] = target

    def processMessage(self) -> None:
        message_queue = self.dispatcher.get_message(Modules.RadarMain)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for _, message in messages:
            if isinstance(message, CCToRadarNewStatus):
                self.updateStatus(message)
            elif isinstance(message, SEKilled):
                self.killObject(message)
            elif isinstance(message, SEStarting):
                self.start(message)
            elif isinstance(message, SEAddRocketToRadar):
                self.addRocket(message)
            elif isinstance(message, RocketUpdate):
                self.rocketUpdate(message)
            elif isinstance(message, RocketDied):
                self.rocketDied(message)

    def updateStatus(self, message: CCToRadarNewStatus) -> None:
        objectId, priority = message.new_target_status
        if objectId in self.allTargets:
            self.allTargets[objectId].updateStatus(TargetStatus.FOLLOWED)
            self.allTargets[objectId].priority = priority
            self.allEnvTargets[objectId].priority = priority

    def killObject(self, message: SEKilled) -> None:
        killRocketId = message.rocket_id
        killTargetId = message.plane_id

        if killTargetId in self.allTargets:
            killedTarget = self.allTargets[killTargetId]
            killedTarget.updateStatus(TargetStatus.DESTROYED)
            if killRocketId in killedTarget.attachedMissiles:
                self.allEnvMissiles.pop(killRocketId, None)
                killedTarget.detachMissile(killRocketId)

    def start(self, message: SEStarting) -> None:
        for targetId, targetCoords in message.planes.items():
            self.allEnvTargets[targetId] = TargetEnv(targetId, targetCoords)
            self.allTargets[targetId] = Target(targetId, TargetStatus.UNDETECTED)

    def addRocket(self, message: SEAddRocketToRadar) -> None:
        missileEnv = MissileEnv(message.missile.missileID, message.planeId, message.rocket_coords)
        self.allEnvMissiles[message.missile.missileID] = missileEnv

    def rocketUpdate(self, message: RocketUpdate) -> None:
        missile_id = message.rocket_id
        missile_coords = message.rocket_coords
        if missile_id in self.allEnvMissiles:
            self.allEnvMissiles[missile_id].updateCoords(missile_coords)
    
    def rocketDied(self, message: RocketDied):
        killRocketId = message.rocketId
        targetId = message.planeId

        target = self.allTargets[targetId]
        target.gotMissile = False

        if killRocketId in target.attachedMissiles:
            self.allEnvMissiles.pop(killRocketId)
            target.detachMissile(killRocketId)

    def sendCurrentTarget(self, radarId: str, targetId: str, sectorSize: float) -> None:
        message = RadarToGUICurrentTarget(Modules.GUI, Priorities.STANDARD, radarId, targetId, sectorSize)
        self.dispatcher.send_message(message)

    def sendAllObjects(self) -> None:
        message = RadarControllerObjects(Modules.ControlCenter, Priorities.LOW, self.allTargets)
        self.dispatcher.send_message(message)

    def sendUnfollowedGUI(self, radarId: str, targetId: str):
        message = TargetUnfollowedGUI(Modules.GUI, Priorities.LOW, radarId, targetId)
        self.dispatcher.send_message(message)

    