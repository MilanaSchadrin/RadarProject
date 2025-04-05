import MissileController
import radarController
import launcherController
import dispatcher

class ControlCenter:
    """Центр управления"""

    """-------------public---------------"""

    def __init__(self, dispatcher):
        self._radarController = radarController(dispatcher)
        self._launcherController = launcherController(dispatcher)
        self._missileController = missileController()
        self._dispatcher = dispatcher
        self._position = Point(25, 25)
        self._targets = []



    def update(self):
        """Метод вызывается на каждой итерации, получает и обрабатывает сообщения."""
        messages = self._dispatcher.get_message(Modules.ControlCenter)

        for message in messages:

            if isinstance(message, RadarControllerObjects):

                self._targets = message.detected_objects
                self._update_priority_targets()
                self._process_targets()

            elif isinstance(message, LauncherControllerMissileLaunched):
                self._missile_controller.process_new_missiles(message.missiles)

        self._dispatcher.send_messege( CCToSkyEnv(Modules.SE, Priorities.STANDARD, self._get_missiles()) )


    def get_position(self):
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
        curr_priority_targets = []
        for target in self._targets:
            if target.status == 3: # цель в захвате радара
                curr_priority_targets.append(target)
        return curr_priority_targets


    def _find_priority_targets(self):
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
                signReverse = -1 if a >= 0 else 1

                active_missiles_count = sum(1 for missile in target.missilesFollowed if missile.status == MissileStatus.ACTIVE)
                launcher_pr_list.append( (active_missiles_count, signReverse, abs(projection), target) )

            launcher_pr_list.sort( key=lambda x: (x[0], x[1], x[2]) )
            pr_list.append( launcher_pr_list[0] )


        pr_list.sort(key=lambda x: (x[0], x[1], x[2]))

        return [item[3] for item in pr_list[:countPr]]




    def _direction(self, target):
        e = np.array([target.velocity.x, target.velocity.y])
        norm = np.linalg.norm(e)
        if norm == 0:
            return np.array([0.0, 0.0])
        return e / norm

