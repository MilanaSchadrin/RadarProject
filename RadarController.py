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
        self._control_center = control_center
        self._dispatcher = dispatcher  # Диспетчер сообщений
        self._radars = []

    def update(self):
        """Метод для обновления состояния радаров."""
        for radar in self._radars:
            # Логика обновления каждого радара
            pass

    def get_radars(self):
        """Возвращает список всех радаров."""
        return self._radars