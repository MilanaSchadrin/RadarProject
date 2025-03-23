from typing import Dict, Any, List
from controllers import RadarController, PUController
from rocket_controller import RocketController


class PBU:
    """Пункт боевого управления (ПБУ)"""

    def __init__(self, dispatcher):
        self._radar_controller = RadarController(self)
        self._pu_controller = PUController(self)
        self._rocket_controller = RocketController(self)
        self._dispatcher = dispatcher  # Ссылка на диспетчер сообщений
        self._targets: Dict[str, Any] = {}  # Словарь целей (самолеты, ракеты)

    def update(self):
        """Обновляет состояние ПБУ: получает и обрабатывает сообщения, а также отправляет новые сообщения."""
        pass

    def get_targets(self) -> Dict[str, Any]:
        """Возвращает список целей (самолеты, ракеты)."""
        return self._targets

    def get_pus(self) -> List[Any]:
        """Возвращает список всех ПУ."""
        return self._pu_controller.get_pus()

    def get_radars(self) -> List[Any]:
        """Возвращает список всех радаров."""
        return self._radar_controller.get_radars()

    def get_radar_controller(self) -> RadarController:
        """Возвращает контроллер радаров."""
        return self._radar_controller

    def get_pu_controller(self) -> PUController:
        """Возвращает контроллер пусковых установок."""
        return self._pu_controller
