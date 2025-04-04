import Missile
import Target

class MissileController:
    """Контроллер ракет"""

    def __init__(self):
        self._missiles = []
        self._unusefulMissiles = []


    def process_missiles_of_target(self, target):
        """Обрабатывает список ракет у данной цели."""

        missiles = target.missilesFollowed

        for currMissile in missiles:
            currMissile.currLifeTime -= 3
            if target.status == 0: # уничтоженная цель
                self._unusefulMissiles.append(currMissile)

            elif self._collision(currMissile, target):
                self._destroy_missile(currMissile)

        self._missiles.append(missiles)


    def process_unuseful_missiles(self):
        for currMissile in self._unusefulMissiles:
            destroy = True
            for otherMissile in self._missiles:
                if (otherMissile.currLifeTime > 0) and (otherMissile.missileId != currMissile.missileId) and \
                   (otherMissile not in self._unusefulMissiles) and self._collision(currMissile, otherMissile):
                    destroy = False
                    break
            if destroy:
                self._destroy_missile(currMissile)

        self._unusefulMissiles = []


    def process_new_missiles(self, new_missiles):
        for new_missile in new_missiles:
            new_missile.currLifeTime -= 2;
            self._missiles.append(new_missile)


    def pop_missiles(self):
        """Удаляет и возвращает список всех ракет."""
        missiles = self._missiles
        self._missiles = []
        return missiles


    """--------------------"""


    def _destroy_missile(self, missile):
        missile.currLifeTime = 0


    def _collision(self, mainObject, object1):
        """Проверяет наличие object1 в радиусе mainObject."""
        return ((object1.currentPosition.x - main_object.currentPosition.x) ** 2 + \
                (object1.currentPosition.y - main_object.currentPosition.y) ** 2) ** 0.5 < mainObject.damageRadius
