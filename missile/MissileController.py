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
        self._unusefulMissiles: List[Missile] = [] # ненужные ракеты на данной итерации


    def process_missiles_of_target(self, target):
        """Обрабатывает список ракет у данной цели."""
        for currMissile in target.attachedMissiles.values():
            currMissile.currLifeTime -= TICKSPERCYCLERADAR
            if target.status == TargetStatus.DESTROYED: # уничтоженная цель
                currMissile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(currMissile)

            elif self._collision(currMissile, target):
                self._destroy_missile(currMissile)

            elif self._will_explode(target, currMissile) == False:
                currMissile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(currMissile)

            self._missiles.append(currMissile)


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

        self._unusefulMissiles = []


    def process_new_missile(self, new_missile):
        """Обрабатывает новую ракету"""
        new_missile.currLifeTime -= TICKSPERCYCLELAUNCHER;
        self._missiles.append(new_missile)


    def pop_missiles(self):
        """Удаляет и возвращает список всех ракет."""
        missiles = self._missiles
        #print("Sending missiles:", type(missiles), [type(m) for m in missiles])
        self._missiles = []
        return missiles


    """-------------private---------------"""


    def _destroy_missile(self, missile):
        """Уменьшает счетчик времени жизни ракеты до нуля."""
        if missile.currLifeTime > 0:
            missile.currLifeTime = 0


    def _collision(self, mainObject, other_object):
        """Проверяет наличие object1 в радиусе mainObject."""
        distance = np.linalg.norm( np.array(mainObject.currentCoords) - np.array(other_object.currentCoords))
        return distance < mainObject.damageRadius


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
            if B == 0:
                return C < 0  # Уже в радиусе взрыва

        D = B ** 2 - 4 *A * C
        if D <= 0:
            return False  # Не будет взрыва

        t1 = (-B - np.sqrt(D)) / (2 * A)
        t2 = (-B + np.sqrt(D)) / (2 * A)

        life_time = missile.currLifeTime / TICKSPERSECOND

        return (t1 < 0 and t2 > 0) or (0 < t1 < life_time)