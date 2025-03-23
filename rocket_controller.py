from typing import Dict, List, Any

if True:  
    from pbu import PBU  # Отложенный импорт


class RocketController:
    """Контроллер ракет"""

    def __init__(self, pbu: PBU):
        self._pbu = pbu  # Ссылка на ПБУ
        self._rockets: Dict[str, Any] = {}  # Словарь ракет, ключ — ID ракеты

    def change_rockets(self):
        """Изменяет траектории всех ракет"""
        pass

    def get_rockets(self) -> List[Any]:
        """Возвращает список всех ракет"""
        return list(self._rockets.values())

    def destroy_rocket(self, rocket_id: str):
        """Взрывает ракету"""
        pass
