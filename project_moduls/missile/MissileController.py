from missile.Missile import Missile, MissileStatus
from radar.Target import Target, TargetStatus
from dispatcher.enums import *
from common.commin import TICKSPERCYCLERADAR,TICKSPERCYCLELAUNCHER,TICKSPERSECOND
from typing import List, Tuple
import numpy as np
from typing import List
import numpy as np
import math


def calculate_interception_point(target, missile):
    """Вычисляет точку встречи ракеты и цели."""

    r_pos = np.array(missile.currentCoords)
    r_vel = np.array(missile.velocity)
    t_pos = np.array(target.currentCoords)
    t_vel = np.array(target.currentSpeedVector)

    rel_pos = t_pos - r_pos
    rel_vel = t_vel

    missile_speed = np.linalg.norm(r_vel)
    rel_speed_sq = np.dot(rel_vel, rel_vel)
    rel_pos_dot_vel = np.dot(rel_pos, rel_vel)
    rel_pos_sq = np.dot(rel_pos, rel_pos)

    # Решаем квадратное уравнение: a*t^2 + b*t + c = 0
    a = rel_speed_sq - missile_speed**2
    b = 2 * rel_pos_dot_vel
    c = rel_pos_sq

    discriminant = b**2 - 4 * a * c

    if a == 0:
        # Скорости одинаковые или цель стоит: движемся по прямой
        t = np.linalg.norm(rel_pos) / missile_speed if missile_speed != 0 else 0
    elif discriminant < 0:
        # Нет действительного решения: ракета не может догнать цель, летим по прямой
        t = np.linalg.norm(rel_pos) / missile_speed if missile_speed != 0 else 0
    else:
        sqrt_d = np.sqrt(discriminant)
        t1 = (-b + sqrt_d) / (2 * a)
        t2 = (-b - sqrt_d) / (2 * a)
        t_candidates = [t for t in [t1, t2] if t > 0]
        t = min(t_candidates) if t_candidates else 0

    interception_point = t_pos + t_vel * t
    return tuple(interception_point)


def change_velocity(point, missile):
    """Изменяет направление ракете к предполагаемой точке встреми с целью."""
    distance = np.array(point) - np.array(missile.currentCoords)
    norm = np.linalg.norm(distance)
    e = distance / norm

    abs_velocity = np.linalg.norm(np.array(missile.velocity))
    missile.velocity = tuple(e * abs_velocity)


def calc_lifetime(point, missile, time_step):
    """Вычисляет время жизни ракеты, необходимое для достижения цели."""
    dist_vec = np.array(point) - np.array(missile.currentCoords)
    distance = np.linalg.norm(dist_vec)
    abs_velocity = np.linalg.norm(np.array(missile.velocity))

    time_seconds = distance / abs_velocity
    return int(time_seconds / time_step)



class MissileController:
    """Контроллер ракет"""

    """-------------public---------------"""

    def __init__(self, time_step):
        self._time_step = time_step
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
        if missile is None:
            return
        
        if self._target_not_in_module(target):
            self._destroy_missile(missile)

        if missile.status == MissileStatus.AUTOMATIC:
            missile.currLifeTime -= 1

        if missile.isDetected:
            if target.status == TargetStatus.DESTROYED: # уничтоженная цель
                missile.status = MissileStatus.INACTIVE
                self._unusefulMissiles.append(missile)

            elif target.status == TargetStatus.UNDETECTED:
                if missile.status == MissileStatus.ACTIVE:
                    self._change_to_auto(target, missile)


            elif self._collision(missile, target):
                self._destroy_missile(missile)

            else:
                self._change_to_active(target, missile)

        elif missile.status == MissileStatus.ACTIVE:
            self._change_to_auto(target, missile)

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
        distance = np.linalg.norm( np.array(mainObject.currentCoords) - np.array(other_object.currentCoords))
        print("distance: ", distance)
        print("damageRadius: ", mainObject.damageRadius)
        return distance < mainObject.damageRadius


    def _change_to_auto(self, target, missile):
        missile.status = MissileStatus.AUTOMATIC
        interception_point = calculate_interception_point(target, missile)
        change_velocity(interception_point, missile)
        missile.currLifeTime = calc_lifetime(interception_point, missile, self._time_step)


    def _change_to_active(self, target, missile):
        missile.status = MissileStatus.ACTIVE
        interception_point = calculate_interception_point(target, missile)
        change_velocity(interception_point, missile)

    def _target_not_in_module(self, target):
        return all(coord <= -15000 for coord in target.currentCoords[:3])


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
        C = np.dot(d, d) - (missile.damageRadius//2) ** 2

        if A == 0:
            return C < 0  # Уже в радиусе взрыва

        D = B ** 2 - 4 *A * C
        if D <= 0:
            return False  # Не будет взрыва

        t1 = (-B - np.sqrt(D)) / (2 * A)
        t2 = (-B + np.sqrt(D)) / (2 * A)

        life_time = missile.currLifeTime / TICKSPERSECOND

        return (t1 < 0 and t2 > 0) or (0 < t1 < life_time)

