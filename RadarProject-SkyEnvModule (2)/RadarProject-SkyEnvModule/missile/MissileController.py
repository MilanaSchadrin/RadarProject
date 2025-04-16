from missile.Missile import Missile, MissileStatus
from radar.Target import Target
import numpy as np
from dispatcher.enums import *


class MissileController:
    """Контроллер ракет"""

    """-------------public---------------"""

    def __init__(self):
        self._missiles = [] # ракеты на данной итерации
        self._unusefulMissiles = [] # ненужные ракеты на данной итерации


    def process_missiles_of_target(self, target):
        """Обрабатывает список ракет у данной цели."""

        missiles = target.missilesFollowed

        for currMissile in missiles:
            currMissile.currLifeTime -= 3
            if target.status == 0: # уничтоженная цель
                currMissile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(currMissile)

            elif self._collision(currMissile, target):
                self._destroy_missile(currMissile)

            elif self._will_explode(target, currMissile) == False:
                currMissile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(currMissile)

        self._missiles.append(missiles)


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
        new_missile.currLifeTime -= 2;
        self._missiles.append(new_missile)


    def pop_missiles(self):
        """Удаляет и возвращает список всех ракет."""
        missiles = self._missiles
        self._missiles = []
        return missiles


    """-------------private---------------"""


    def _destroy_missile(self, missile):
        """Уменьшает счетчик времени жизни ракеты до нуля."""
        if missile.currLifeTime > 0:
            missile.currLifeTime = 0


    def _collision(self, mainObject, object1):
        """Проверяет наличие object1 в радиусе mainObject."""
        distance = ((object1.currentPosition.x - mainObject.currentPosition.x) ** 2 +
                   (object1.currentPosition.y - mainObject.currentPosition.y) ** 2 +
                   (object1.currentPosition.z - mainObject.currentPosition.z) ** 2) ** 0.5
        return distance < mainObject.damageRadius

    def _will_explode(self, target, missile):
        """Проверяет, что target будет в радиусе взрыва ракеты missile."""
        r_pos = missile.currentPosition.to_vector()
        r_vel = missile.velocity.to_vector()
        t_pos = target.currentPosition.to_vector()
        t_vel = target.speed.to_vector()

        # Вычисляем относительные позицию и скорость
        d = r_pos - t_pos
        v = r_vel - t_vel
        R_sq = missile.damageRadius ** 2

        # Коэффициенты квадратного уравнения A*t^2 + B*t + C < 0
        A = np.dot(v, v)
        B = 2 * np.dot(d, v)
        C = np.dot(d, d) -  R_sq

       # Анализ решения квадратного уравнения
        if A == 0:
            # Случай нулевой относительной скорости
            return C <= 0  # Уже в зоне поражения или на границе

        discriminant = B**2 - 4*A*C

        if discriminant < 0:
            return False  # Нет пересечений

        sqrt_discr = np.sqrt(discriminant)
        t1 = (-B - sqrt_discr) / (2*A)
        t2 = (-B + sqrt_discr) / (2*A)

        # Нас интересуют только будущие моменты времени (t >= 0)
        return (t1 >= 0 and t1 <= t2) or (t2 >= 0 and t1 <= 0)


