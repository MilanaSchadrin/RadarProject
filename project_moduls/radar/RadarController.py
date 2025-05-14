from typing import Dict, Tuple, List
from radar.Target import TargetStatus, Target
from radar.Radar import Radar
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import Modules,Priorities
from missile.Missile import Missile
from dispatcher.messages import (
    CCToRadarNewStatus,
    RadarToGUICurrentTarget,
    RadarControllerObjects,
    SEKilled,
    SEStarting,
    SEAddRocketToRadar,
    RocketUpdate,
    TargetUnfollowedGUI
)

class TargetEnv:
    """Класс для хранения реальных координат цели, полученных от SkyEnv."""

    def __init__(self, targetId: str, clearCoords: List[Tuple[float, float, float]]) -> None:
        self.targetId: str = targetId
        self.clearCoords: List[Tuple[float, float, float]] = clearCoords
        self.isFollowed = False
        self.priority: int = 1000000

    def getCurrentCoords(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущие координаты цели на указанном шаге."""
        return self.clearCoords[step-1]

    def getCurrentSpeedVec(self, step: int) -> Tuple[float, float, float]:
        """Возвращает текущий вектор скорости цели."""
        return (
            self.clearCoords[step][0] - self.clearCoords[step-1][0],
            self.clearCoords[step][1] - self.clearCoords[step-1][1],
            self.clearCoords[step][2] - self.clearCoords[step-1][2],
        )


class MissileEnv:
    """Класс для хранения реальных координат ракеты, полученных от SkyEnv."""

    def __init__(
        self,
        missileId: str,
        targetId: str,
        currentCoords: Tuple[float, float, float],
    ) -> None:
        self.missileId: str = missileId
        self.targetId: str = targetId
        self.currentCoords: Tuple[float, float, float] = currentCoords

    def getCurrentCoords(self):
        return self.currentCoords

    def updateCoords(self, missile_coords):
        self.currentCoords = missile_coords



class RadarController:
    """Контроллер радаров, обрабатывающий сообщения от системы моделирования."""

    def __init__(self, dispatcher) -> None:
        self.dispatcher: Dispatcher = dispatcher
        self.radars: Dict[str, Radar] = {}
        self.allEnvTargets: Dict[str, TargetEnv] = {}
        self.allEnvMissiles: Dict[str, MissileEnv] = {}
        self.allTargets: Dict[str, Target] = {}

    def addRadar(self, radar: Radar) -> None:
        """Добавляет радар под управление контроллера."""
        self.radars[radar.radarId] = radar

    def getAbsoluteCoords(self, radar, local_coords):
        return (
            local_coords[0] + radar.position[0],
            local_coords[1] + radar.position[1],
            local_coords[2] + radar.position[2]
        )

    def update(self, step: int) -> None:
        """Обновляет состояние всех радаров, текущие координаты всех целей и ракет."""

        # 1. удаляем все объекты destroyed что были на предыдущей итерации
        destroyed_targets = [
        target_id 
        for target_id, target in self.allTargets.items()
        if target.status == TargetStatus.DESTROYED
    ]

        # Удаляем по собранным ключам
        for target_id in destroyed_targets:
            target = self.allTargets[target_id]
            
            # Удаляем привязанные ракеты
            for missile_id in list(target.attachedMissiles.keys()):  # list() для копии ключей
                self.allEnvMissiles.pop(missile_id, None)
                target.detachMissile(missile_id)
            
            # Удаляем саму цель
            self.allEnvTargets.pop(target_id, None)
            self.allTargets.pop(target_id, None)

        # 2.  обработка сообщений, обновление данных self.allEnvTargets и self.allEnvMissiles         
        self.processMessage() 

        temp_targets = list(self.allEnvTargets.keys())
        allDetectedMissiles = {}

        # 3. Обработка всех отслеживаемых целей(сюда попадают только цели со статусом FOLLOWED )

        followedTargetsNow = []

        for radar in self.radars.values():
            followedTargets, _, detectedMissile = radar.scan(step, followedTargetsNow)

            for target_id in list(followedTargets.keys()):
                if target_id in temp_targets:

                    target = self.allTargets[target_id]

                    if self.allEnvTargets[target_id].isFollowed == False:
                        self.sendCurrentTarget(radar.radarId, target_id, radar.maxRange//1000)
                        self.allEnvTargets[target_id].isFollowed = True
                    target.currentCoords = self.getAbsoluteCoords(radar, followedTargets[target_id][0])
                    #print(target.currentCoords)
                    target.currentSpeedVector = followedTargets[target_id][1]
 
                    temp_targets.remove(target_id)

                    followedTargetsNow += list(radar.followedTargets.keys())

                    allDetectedMissiles.update(detectedMissile)

            for targetId in temp_targets:
                if self.allEnvTargets[targetId].isFollowed == True:
                    self.allEnvTargets[targetId].isFollowed = False
                    #print('I was in here, so no ray')
                    self.sendUnfollowedGUI(radar.radarId, targetId)

            # 4. Обработка всех замеченных целей (здесьь не должнл быть DESTROYED)
  
            for radar in self.radars.values():
                _, detectedTargets, _ = radar.scan(step, _)

                for target_id in detectedTargets:

                    if target_id in temp_targets:

                        self.allEnvTargets[target_id].isFollowed = False

                        target = self.allTargets[target_id]
                        target.status = TargetStatus.DETECTED
                        
                        target.currentCoords = self.getAbsoluteCoords(radar, detectedTargets[target_id][0])
                        target.currentSpeedVector = detectedTargets[target_id][1]
                        temp_targets.remove(target_id)

            # 5. Обработка всех ракет(сначала делаем все ракеты isDetected = False, а потом меняем на True для всех замеченных ракет)
            for target in list(self.allTargets.values()):
                if len(target.attachedMissiles) > 0:
                    missile_id = next(iter(target.attachedMissiles))  # Получаем ключ
                    missile = target.attachedMissiles[missile_id]
                    missile.isDetected = False
                    missile.currentCoords = (0, 0, 0)  
            
            for radar in self.radars.values():
                _, _, detectedMissiles = radar.scan(step, _)           

            for missileId in list(detectedMissiles.keys()):
                targetId = self.allEnvMissiles[missileId].targetId
                target = self.allTargets[targetId]
                missile = target.attachedMissiles[missileId]
                if missile.isDetected == False:
                    missile.isDetected = True
                    if str(missileId) in detectedMissile:
                        missile.currentCoords = self.getAbsoluteCoords(radar, detectedMissile[str(missileId)])
                    else:
                        missile.currentCoords = (0, 0, 0)
                
        # Обработка всех оставшихся целей, которые не попали в область видимсоти ни одного из радаров

        for targetId in temp_targets:
            target = self.allTargets[targetId]
            if target.status != TargetStatus.DESTROYED:
                target.status = TargetStatus.UNDETECTED
                target.currentCoords = (0, 0, 0)

        self.sendAllObjects()

    def addDetectedTarget(self, target: Target) -> None:
        """Добавляет цель в список обнаруженных целей."""
        self.allTargets[target.targetId] = target

    def processMessage(self) -> None:
        message_queue = self.dispatcher.get_message(Modules.RadarMain)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for _,message in messages:
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

    def updateStatus(self, message: CCToRadarNewStatus) -> None:
        """Обновляет статус цели."""
        objectId, priority = message.new_target_status
        if objectId in self.allTargets:
            self.allTargets[objectId].updateStatus(TargetStatus.FOLLOWED)
            self.allTargets[objectId].priority = priority
            self.allEnvTargets[objectId].priority = priority

    def killObject(self, message: SEKilled) -> None:
        """Обновляет статус цели на DESTROYED"""
        killRocketId = message.rocket_id
        killTargetId = message.plane_id
        
        if killTargetId in self.allTargets:
            killedTarget = self.allTargets[killTargetId]
            killedTarget.updateStatus(TargetStatus.DESTROYED)
            
            if killRocketId in killedTarget.attachedMissiles:
                self.allEnvMissiles.pop(killRocketId)
                killedTarget.detachMissile(killRocketId)

    def start(self, message: SEStarting) -> None:
        """Получает начальные данны
        е о целях в небе."""
        for targetId, targetCoords in message.planes.items():
            self.allEnvTargets[targetId] = TargetEnv(targetId, targetCoords)
            self.allTargets[targetId] = Target(targetId, TargetStatus.UNDETECTED)

    def addRocket(self, message: SEAddRocketToRadar) -> None:
        """Добавляет новую ракету в список всех ракет."""
        missileEnv = MissileEnv(
            message.missile.missileID,
            message.planeId,
            message.rocket_coords
        )
        self.allEnvMissiles[message.missile.missileID] = missileEnv
    
    def rocketUpdate(self, message: RocketUpdate) -> None:
        "Обновляет текущие координаты ракеты"
        missile_id = message.rocket_id
        missile_coords = message.rocket_coords
        if missile_id in self.allEnvMissiles:
            self.allEnvMissiles[missile_id].updateCoords(missile_coords)

    def sendCurrentTarget(
        self,
        radarId: str,
        targetId: str,
        sectorSize: float
    ) -> None:
        """Отправляет сообщение о сопровождаемой цели."""
        message = RadarToGUICurrentTarget(Modules.GUI,Priorities.STANDARD, radarId, targetId, sectorSize)
        self.dispatcher.send_message(message)

    def sendAllObjects(self) -> None:
        """Отправляет список обнаруженных целей."""
        message = RadarControllerObjects(Modules.ControlCenter,Priorities.LOW,self.allTargets)
        self.dispatcher.send_message(message)

    def sendUnfollowedGUI(self, radarId: str, targetId: str):
        """Отправляет сообщение GUI о том, что цель перестала отслеживаться."""
        message = TargetUnfollowedGUI(Modules.GUI, Priorities.LOW, radarId, targetId)
        #print('was hereeeee, so send message')
        self.dispatcher.send_message(message)

    