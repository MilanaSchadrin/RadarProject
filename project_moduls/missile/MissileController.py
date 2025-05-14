from missile.Missile import Missile, MissileStatus
from radar.Target import Target, TargetStatus
from dispatcher.enums import *
from common.commin import TICKSPERCYCLERADAR,TICKSPERCYCLELAUNCHER,TICKSPERSECOND
from typing import List
import numpy as np
from typing import List
import numpy as np


class MissileController:
    """Контроллер ракет"""

    """-------------public---------------"""

    def __init__(self):
        self._missiles: List[Missile] = [] # ракеты на данной итерации
        self._unusefulMissiles: List[Missile] = [] # ненужные ракеты на данной итерации (MissileStatus.INACTIVE)


    """Инварианты:
        1) ракета всегда достигает цели, если ей ничего не мешает
        2) если у ракеты missile.status == MissileStatus.INACTIVE, то цель,
         к которой прикреплена ракета, имеет статус target.status == TargetStatus.DESTROYED
        3) (1) & (2) => у цели всегда одна прикрепленная ракета
    """


    def process_missile_of_target(self, target):
        """Обрабатывает ракету у данной цели."""
        missile = next(iter(target.attachedMissiles.values()), None)

        if missile.isDetected:

            if target.status == TargetStatus.DESTROYED: # уничтоженная цель
                missile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(missile)

            elif target.status == TargetStatus.UNDETECTED:
                self._nullify_trajectory(missile)

            elif self._collision(missile, target):
                self._destroy_missile(missile)

            else:
                self._change_trajectory(target, missile)

        else:
            self._nullify_trajectory(missile)

        self._missiles.append(missile)


    def process_unuseful_missiles(self):
        """Обрабатывает список всех ненужных ракет"""
        for currMissile in self._unusefulMissiles:
            destroy = True
            for otherMissile in self._missiles:
                if (otherMissile.currLifeTime > 0) and (otherMissile.missileID != currMissile.missileID) and \
                   (otherMissile not in self._unusefulMissiles) and self._collision(currMissile, otherMissile):
                    destroy = False
                    break
            if destroy:
                self._destroy_missile(currMissile)

        self._unusefulMissiles.clear()


    def process_new_missile(self, new_missile):
        """Обрабатывает новую ракету"""
        self._missiles.append(new_missile)


    def pop_missiles(self):
        """Удаляет и возвращает список всех ракет."""
        missiles = self._missiles.copy()
        self._missiles.clear()
        return missiles


    """-------------private---------------"""


    def _destroy_missile(self, missile):
        """Уменьшает счетчик времени жизни ракеты до нуля."""
        if missile.currLifeTime > 0:
            missile.currLifeTime = 0


    def _collision(self, mainObject, other_object):
        """Проверяет наличие object1 в радиусе mainObject."""
        distance = np.linalg.norm( np.array(mainObject.currentCoords)*1000 - np.array(other_object.currentCoords)*1000)
        return distance < mainObject.damageRadius


    def _change_trajectory(self, target, missile):
        """Изменяет направление ракете."""
        distance = np.array(target.currentCoords) - np.array(missile.currentCoords)
        norm = np.linalg.norm(distance)
        e = distance / norm

        abs_velocity = np.linalg.norm(np.array(missile.velocity))
        missile.velocity = tuple(e * abs_velocity)


    def _nullify_trajectory(self, missile):
        missile.velocity = (0.0, 0.0, 0.0)


    # не используется в реализации
    def _will_explode(self, target, missile):
        """Проверяет, что target будет в радиусе взрыва ракеты missile."""
        r_pos = np.array(missile.currentCoords)
        r_vel = np.array(missile.velocity)
        t_pos = np.array(target.currentCoords)
        t_vel = np.array(target.currentSpeedVector)

        # Вычисляем относительные позицию и скорость
        d = r_pos - t_pos
        v = r_vel - t_vel

        # A*t^2 + B*t + C < 0
        A = np.dot(v, v)
        B = 2 * np.dot(d, v)
        C = np.dot(d, d) - missile.damageRadius ** 2

        if A == 0:
            return C < 0  # Уже в радиусе взрыва

        D = B ** 2 - 4 *A * C
        if D <= 0:
            return False  # Не будет взрыва

        t1 = (-B - np.sqrt(D)) / (2 * A)
        t2 = (-B + np.sqrt(D)) / (2 * A)

        life_time = missile.currLifeTime / TICKSPERSECOND

        return (t1 < 0 and t2 > 0) or (0 < t1 < life_time)