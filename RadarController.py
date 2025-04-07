from enum import Enum

class TargetStatus(Enum):
    """Статусы цели для системы слежения."""
    DESTROYED = 0
    DISAPPEARED = 1
    DETECTED = 2
    FOLLOWED = 3

class Target:
    """Базовый класс для всех объектов, обнаруживаемых радаром."""

    def __init__(
        self,
        target_id: str,
        status: TargetStatus = TargetStatus.DETECTED,
        coords: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        speed: float = 0.0,
        speed_vector: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        self.id = target_id
        self.status = status
        self.coords = coords
        self.speed = speed
        self.speed_vector = speed_vector

    def get_coords(self) -> Tuple[float, float, float]:
        """Возвращает текущие координаты цели."""
        return self.coords

    def update_status(self, new_status: TargetStatus) -> None:
        """Обновляет статус объекта."""
        self.status = new_status

    def update_position(self, new_coords: Tuple[float, float, float]) -> None:
        """Обновляет координаты объекта."""
        self.coords = new_coords

    def update_speed_vector(self, new_speed_vector: Tuple[float, float, float]) -> None:
        """Обновляет вектор скорости объекта."""
        self.speed_vector = new_speed_vector

    def get_coords(self):
        return self.coords
    
class Plane(Target):
    """Класс самолета."""

    def __init__(
        self,
        target_id: str,
        priority: str = 'HIGH',
        status: TargetStatus = TargetStatus.DETECTED,
        coords: Tuple[float, float, float] = (0.0, 0.0, 0.0),
        speed: float = 0.0,
        speed_vector: Tuple[float, float, float] = (0.0, 0.0, 0.0),
    ) -> None:
        super().__init__(target_id, status, coords, speed, speed_vector)
        self.priority = priority
        self.attached_missiles: List[str] = []

    def attach_missile(self, missile_id: str) -> None:
        """Добавляет ракету к списку привязанных."""
        if missile_id not in self.attached_missiles:
            self.attached_missiles.append(missile_id)
            return True 
        else: return False

    def detach_missile(self, missile_id: str) -> bool:
        """Удаляет ракету из списка привязанных."""
        if missile_id in self.attached_missiles:
            self.attached_missiles.remove(missile_id)
            return True
        return False

    def can_be_removed(self) -> bool:
        """Проверяет, можно ли удалить цель."""
        return not self.attached_missiles

class Radar:
    """Класс, представляющий радар, который обнаруживает объекты в зоне видимости и передаёт данные в RadarController.

    Args:
        position (tuple[float, float, float]): Координаты радара в глобальной системе (X, Y, Z).
        range (float): Радиус зоны сканирования в метрах.
        detectedObjects (list[dict]): Список обнаруженных объектов.
        radarId (str): Уникальный идентификатор радара (например, "Radar-001").
        maxTargetCount (int): Максимальное количество целей, которые радар может сопровождать одновременно.
        currentTargetCount (int): Текущее количество сопровождаемых целей.
        noiseLevel (float): Уровень внутренних шумов радара (в dB). Влияет на точность обнаружения.
    """

    def init(self, position: tuple[float, float, float], range_: float, radar_id: str, max_target_count: int, noise_level: float):
        """
        Args:
            position (tuple[float, float, float]): Глобальные координаты радара (X, Y, Z).
            range_ (float): Радиус зоны сканирования (в метрах).
            radar_id (str): Уникальный идентификатор радара (например, "Radar-001").
            max_target_count (int): Максимальное количество целей, которые можно сопровождать одновременно.
            noise_level (float): Уровень шумов радара (в dB).
        """
        self.position = position
        self.range = range_
        self.detectedObjects = []
        self.radarId = radar_id
        self.maxTargetCount = max_target_count
        self.currentTargetCount = 0
        self.noiseLevel = noise_level
        self.detectedMissiles = []

    def scan(self) -> None:
        """Выполняет сканирование зоны видимости и обновляет списки обнаруженных объектов и ракет.

        Обновляет:
            - detectedObjects: Добавляет новые объекты и обновляет существующие.
        """
        pass

    def get_detected_objects(self) -> list[dict]:
        """Возвращает список всех обнаруженных объектов.

        Returns:
            list[dict]: Список словарей, где каждый словарь содержит:
                - id (str): Уникальный идентификатор объекта.
                - coordinates (tuple[float, float, float]): Относительные координаты (X, Y, Z).
                - type (str, optional): Тип объекта (самолёт, дрон, ракета и т. д.).
                - speed (float, optional): Скорость объекта (в м/с).
        """
        pass

    def track_target(self, target_id: str) -> None:
        """Начинает сопровождение цели с повышенной точностью.

        Args:
            target_id (str): Идентификатор цели, которую нужно сопровождать.

        Raises:
            ValueError: Если target_id не найден в detectedObjects.
            RuntimeError: Если достигнут лимит maxTargetCount.
        """
        pass

    def mark_target_as_destroyed(self, target_id: str) -> None:
        """Помечает цель как уничтоженную и прекращает её сопровождение.

        Args:
            target_id (str): Идентификатор уничтоженной цели.

        Raises:
            ValueError: Если target_id не найден среди сопровождаемых целей.
        """
        pass

class RadarController:
    """Контроллер радаров"""

    def init(self, control_center, dispatcher):
        self.control_center = control_center
        self.dispatcher = dispatcher  # Диспетчер сообщений
        self.radars = []
        self.all_detected_objects = []


    def update(self):
        """Метод для обновления состояния радаров и получения списка обнаруженных целей с каждого радара."""
        for radar in self._radars:
            # Логика обновления каждого радара
            pass

    def get_radars(self):
        """Возвращает список всех радаров."""
        return self._radars
    
    def get_all_detected_objects(self):
        return self.all_detected_objects
    
    def send_message():
        detected_objects = get_all_detected_objects(self)
        self.dispetcher.send_message(data=detected_objects)

    def get_message():

        


class Target:

    def init(self, id, type, priority, status=2, is_followed=False, coords=(0,0,0), speed=0):
        self.id = id
        self.type = type
        self.priority = priority
        self.status = status
        self.is_followed = is_followed
        self.coords = coords
        self.speed = speed
