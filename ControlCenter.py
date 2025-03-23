from typing import Dict, Any, List
from controllers import RadarController, PUController
from rocket_controller import RocketController


class ControlCenter:
    """Центр управления"""

    def __init__(self, radar_controller, launcher_controller, rocket_controller, dispatcher):
        self._radar_controller = radar_controller
        self._launcher_controller = launcher_controller
        self._rocket_controller = rocket_controller
        self._dispatcher = dispatcher
        self._targets = {}

    def update(self):
        """Метод вызывается на каждой итерации, получает и обрабатывает сообщения."""
        pass

    def get_targets(self):
        """Возвращает список всех известных целей."""
        return self._targets

    def get_launchers(self):
        """Возвращает список всех установок для запуска (Launcher)."""
        return self._launcher_controller.get_launchers()

    def get_radars(self):
        """Возвращает список всех радаров."""
        return self._radar_controller.get_radars()

    def get_radar_controller(self):
        """Возвращает объект RadarController."""
        return self._radar_controller

    def get_launcher_controller(self):
        """Возвращает объект LauncherController."""
        return self._launcher_controller
