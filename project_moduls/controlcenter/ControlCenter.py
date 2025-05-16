from missile.MissileController import MissileController
from radar.RadarController import RadarController
from radar.Radar import Radar
from launcher.launcher import LaunchController, Launcher
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import *
from dispatcher.messages import RadarControllerObjects,LaunchertoCCMissileLaunched,CCToSkyEnv,CCLaunchMissile,CCToRadarNewStatus
from missile.Missile import MissileStatus
from radar.Target import Target, TargetStatus
from common.commin import *
from typing import Tuple, List
import numpy as np
import datetime


class ControlCenter:
    """Центр управления"""

    """-------------public---------------"""

    def __init__(self, dispatcher:Dispatcher, position:Tuple[float, float, float], steps):
        self._radarController: RadarController = RadarController(dispatcher)
        self._launcherController: LaunchController = LaunchController(dispatcher)
        self._missileController: MissileController = MissileController(dispatcher.time_step)
        self._dispatcher: Dispatcher = dispatcher
        self._position: Tuple[float, float, float] = position
        self._targets: List[Target] = [] # все цели на данной итерации
        self.steps = steps
        self.currentStep = 0

    def start(self,db):
        self._dispatcher.register(Modules.ControlCenter)
        radars_data = db.load_radars()
        self._dispatcher.register(Modules.RadarMain)
        for radar_id, radar_info in radars_data.items():
            radar = Radar(
                radarController=self._radarController,
                dispatcher=self._dispatcher,
                radarId=str(radar_id),
                position=radar_info['position'],
                maxRange=radar_info['range_input']*1000,
                #coneAngleDeg=radar_info['angle_input'],
                maxFollowedCount=radar_info['max_targets']
                #maxTargetCount=radar_info['max_targets'],
            )
            self._radarController.addRadar(radar)
            
        launchers_data = db.load_launchers()
        self._dispatcher.register(Modules.LauncherMain)
        for launcher_id, launcher_info in launchers_data.items():
            launcher = Launcher(
                ctrl=self._launcherController,
                id=launcher_id,
                coord=launcher_info['position'],
                silos=launcher_info['cout_zur']
                #missile_speed1= launcher_info['vel_zur1'],
                #damage_radius1 = launcher_info['dist_zur1'],
                #missile_speed2= launcher_info['vel_zur2'],
                #damage_radius2 = launcher_info['dist_zur2']
            )
            self._launcherController.add_launcher(launcher)

    def update(self):
        message_queue = self._dispatcher.get_message(Modules.ControlCenter)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:
            if isinstance(message, RadarControllerObjects):
                self._targets = list(message.detected_objects.values())
                #self._targets = message.detected_objects
                self._update_priority_targets()
                self._process_targets()
            elif isinstance(message, LaunchertoCCMissileLaunched):
                self._missileController.process_new_missile(message.missile)
        self._radarController.update(self.currentStep)
        self._launcherController.update()
        t = self._get_missiles()
        if len(t)!=0:
            self._dispatcher.send_message(CCToSkyEnv(Modules.SE, Priorities.STANDARD,t) )
        self.currentStep+=1


    def get_position(self):
        """Возвращает позицию ПБУ."""
        return self._position


    def get_launchers(self):
        """Возвращает список всех установок для запуска (Launcher)."""
        return self._launcherController.get_launchers()


    def get_radars(self):
        """Возвращает список всех радаров."""
        return self._radarController.get_radars()


    def get_radar_controller(self):
        """Возвращает объект RadarController."""
        return self._radarController


    def get_launcher_controller(self):
        """Возвращает объект LauncherController."""
        return self._launcherController


    """-------------private---------------"""

    def _get_missiles(self):
        """Возвращает список всех ракет (одноразово)."""
        return self._missileController.pop_missiles()


    def _process_targets(self):
        """Обрабатывает цель."""
        for target in self._targets:
            missile_count = sum(1 for missile in target.attachedMissiles.values())
            if missile_count == 0 and target.gotMissile==False:
                if target.status == TargetStatus.FOLLOWED:
                    self._dispatcher.send_message(
                        CCLaunchMissile(Modules.LauncherMain, Priorities.HIGH, target))
            elif missile_count > 0 and target.gotMissile==True:
                self._missileController.process_missile_of_target(target)

        self._missileController.process_unuseful_missiles()

    def _update_priority_targets(self):
        """Обновляет приоритетность целям на данной итерации"""
        list_pr_targets = self._find_priority_targets()
        priority = 1
        for target in list_pr_targets:
            p = to_integer()
            data = (int(target.targetId), priority)
            self._dispatcher.send_message(CCToRadarNewStatus(
                recipient_id=Modules.RadarMain,
                priority = Priorities.STANDARD,
                priority_s=p,
                new_target_status =  data))
            priority += 1

    def _find_priority_targets(self):
        """Находит приоритетные цели на данной итерации"""
        pr_list = []

        for target in self._targets:
            if target.status in [TargetStatus.DESTROYED, TargetStatus.UNDETECTED]: # уничтоженная или необнаруженная цель
                continue

            direction = self._direction(target)
            launcher_pr_list = []

            for launcher in self.get_launchers():
                if launcher.available_missiles() == 0: # бесполезный ПУ
                    continue
    
                distance = np.array(launcher.coord) - np.array(target.currentCoords)
                projection = np.dot(distance, direction)
                time = projection / np.linalg.norm( np.array(target.currentSpeedVector) )
                signReverse = -1 if projection >= 0 else 1

                missile_count = sum(1 for missile in target.attachedMissiles.values())
                launcher_pr_list.append( (missile_count, signReverse, abs(time), target) )

            if launcher_pr_list:
                launcher_pr_list.sort(key=lambda x: (x[0], x[1], x[2]))
                pr_list.append(launcher_pr_list[0])


        pr_list.sort(key=lambda x: (x[0], x[1], x[2]))

        return [item[3] for item in pr_list]



    def _direction(self, target):
        """Вычисляет единичный вектор направления цели target в 3D"""
        v = np.array(target.currentSpeedVector)
        norm = np.linalg.norm(v)
        if norm == 0:
            return np.array([0.0, 0.0, 0.0])
        return v / norm


