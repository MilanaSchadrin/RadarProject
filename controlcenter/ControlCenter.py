from missile.MissileController import MissileController
from radar.RadarController import RadarController
from radar.Radar import Radar
from launcher.launcher import LaunchController, Launcher
from dispatcher.dispatcher import Dispatcher
from dispatcher.enums import *
from dispatcher.messages import RadarControllerObjects,LaunchertoCCMissileLaunched,CCToSkyEnv,CCLaunchMissile,CCToRadarNewStatus
from missile.Missile import MissileStatus
from common.commin import Point
import numpy as np


class ControlCenter:
    """Центр управления"""

    """-------------public---------------"""

    def __init__(self, dispatcher:Dispatcher,position):
        self._radarController = RadarController(dispatcher)
        self._launcherController = LaunchController(dispatcher)
        self._missileController = MissileController()
        self._dispatcher = dispatcher
        self._position = position
        self._targets = [] # все цели на данной итерации

    def start(self,db):
        self._dispatcher.register(Modules.ControlCenter)
        radars_data = db.load_radars()
        for radar_id, radar_info in radars_data.items():
            radar = Radar(
                radarController=self._radarController,
                dispatcher=self._dispatcher,
                radarId=str(radar_id),
                position=radar_info['position'],
                maxRange=radar_info['range_input'],
                coneAngleDeg=radar_info['angle_input'],
                maxTargetCount=radar_info['max_targets'],
                noiseLevel=0.1  # Значение по умолчанию
            )
            self._radarController.addRadar(radar)
        launchers_data = db.load_launchers()
        for launcher_id, launcher_info in launchers_data.items():
            launcher = Launcher(
                ctrl=self._launcherController,
                id=launcher_id,
                coord=launcher_info['position'],
                silos=launcher_info['cout_zur'],
                #dist=launcher_info['dist_zur'],
                #velocity=launcher_info['velocity_zur']
            )
            self._launcherController.add_launcher(launcher)

    def update(self):
        """Метод вызывается на каждой итерации, получает и обрабатывает сообщения."""
        message_queue = self._dispatcher.get_message(Modules.ControlCenter)
        messages = []
        while not message_queue.empty():
            messages.append(message_queue.get())
        for priority, message in messages:

            if isinstance(message, RadarControllerObjects):

                self._targets = message.detected_objects
                self._update_priority_targets()
                self._process_targets()

            elif isinstance(message, LaunchertoCCMissileLaunched):
                self._missile_controller.process_new_missile(message.missile)

        self._dispatcher.send_message(CCToSkyEnv(Modules.SE, Priorities.STANDARD, self._get_missiles()) )


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

            if target.status != 0: # неуничтоженная цель
                active_missiles_count = sum(1 for missile in target.missilesFollowed if missile.status == MissileStatus.ACTIVE)
                if target.status == 3 and active_missiles_count == 0:
                    self._dispatcher.send_messege( CCLaunchMissile(Modules.LauncherMain, Priorities.HIGH, target) )
            self._missileController.process_missiles_of_target(target)
        self._missileController.process_unuseful_missiles()


    def _update_proirity_targets(self):
        """Изменяет приоритетность целям на данной итерации"""
        old_pr_targets = self._current_priority_targets()
        new_pr_targets = self._find_priority_targets()

        # уменьшить приоритет
        for target in old_pr_targets:
            if (target not in new_pr_targets):
                self._dispatcher.send_messege( CCToRadarNewStatus(Modules.RadarMain, Priorities.STANDARD, (target.targetID, 2)) )

        # увеличить приоритет
        for target in new_pr_targets:
            if (target not in old_pr_targets):
                self._dispatcher.send_messege( CCToRadarNewStatus(Modules.RadarMain, Priorities.STANDARD, (target.targetID, 3)) )        
            

    def _current_priority_targets(self):
        """Находит старые приоритетные цели прошлой итерации"""
        return [target for target in self._targets if target.status == 3]


    def _find_priority_targets(self):
        """Находит приоритетные цели на данной итерации"""
        pr_list = []
        countPr = self._radarController.get_priority_count()

        for target in self._targets:
            if target.status == 0: # уничтоженная цель
                continue

            direction = self._direction(target)
            launcher_pr_list = []
            for launcher in self.get_launchers():
                if launcher.countMissiles == 0: # бесполезный ПУ
                    continue
    
                distance = np.array([
                    launcher.coord.x - target.currentPosition.x,
                    launcher.coord.y - target.currentPosition.y ])

                projection = np.dot(distance, direction)
                signReverse = -1 if  projection >= 0 else 1

                active_missiles_count = sum(1 for missile in target.missilesFollowed if missile.status == MissileStatus.ACTIVE)
                launcher_pr_list.append( (active_missiles_count, signReverse, abs(projection), target) )

            launcher_pr_list.sort( key=lambda x: (x[0], x[1], x[2]) )
            pr_list.append( launcher_pr_list[0] )


        pr_list.sort(key=lambda x: (x[0], x[1], x[2]))

        return [item[3] for item in pr_list[:countPr]]


    def _direction(self, target):
        """Вычисляет единичный вектор направления цели target"""
        e = np.array([target.velocity.x, target.velocity.y])
        norm = np.linalg.norm(e)
        if norm == 0:
            return np.array([0.0, 0.0])
        return e / norm

