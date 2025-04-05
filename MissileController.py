import Missile
import Target
import numpy as np


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


    def process_new_missiles(self, new_missiles):
        """Обрабатывает список новых ракет"""
        for new_missile in new_missiles:
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
        return ((object1.currentPosition.x - main_object.currentPosition.x) ** 2 + \
                (object1.currentPosition.y - main_object.currentPosition.y) ** 2) ** 0.5 < mainObject.damageRadius


    def _will_explode(self, target, missile):
        """Проверяет, что target будет в радиусе взрыва ракеты missile."""
        r_pos = np.array(missile.currentPosition)
        r_vel = np.array(missile.velocity)
        t_pos = np.array(target.currentPosition)
        t_vel = np.array(target.speed)

        d = r_pos - t_pos
        v = r_vel - t_vel

        # A*t^2 + B*t + C < 0
        A = np.dot(v, v)
        B = 2 * np.dot(d, v)
        C = np.dot(d, d) - missile.damageRadius ** 2

        if A == 0:
            if B == 0:
                return C < 0  # Уже в радиусе взрыва
            else:
                t_hit = -C / B
                return t_hit > 0

        D = B ** 2 - 4 *A * C

        if D <= 0:
            return False  # Не будет взрыва

        t1 = (-B - np.sqrt(D)) / (2 * A)
        t2 = (-B + np.sqrt(D)) / (2 * A)
        return t2 > 0


