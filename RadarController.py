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
    """Класс радара."""

    def __init__(
        self,
        radar_controller: 'RadarController',
        dispatcher: 'Dispatcher',
        radar_id: str,
        position: Tuple[float, float, float],
        max_range: float,
        cone_angle_deg: float,
        max_target_count: int,
        noise_level: float,
    ) -> None:
        self.radar_controller = radar_controller
        self.dispatcher = dispatcher
        self.radar_id = radar_id
        self.position = position
        self.max_range = max_range
        self.cone_angle_deg = cone_angle_deg
        self.detected_objects: Dict[str, Target] = {}
        self.max_target_count = max_target_count
        self.current_target_count = 0
        self.noise_level = noise_level
        self.followed_targets: Dict[str, Target] = {}

    def is_target_in_range(self, target: Target) -> bool:
        """Проверяет, находится ли цель в зоне действия радара."""
        target_position = target.get_coords()
        if target_position[2] < 0:
            return False

        dx = target_position[0] - self.position[0]
        dy = target_position[1] - self.position[1]
        dz = target_position[2] - self.position[2]
        
        distance = math.sqrt(dx**2 + dy**2 + dz**2)
        if distance > self.max_range:
            return False

        if dz <= 0:
            return False

        horizontal_distance = math.sqrt(dx**2 + dy**2)
        angle_rad = math.atan(horizontal_distance / dz)
        cone_angle_rad = math.radians(self.cone_angle_deg) / 2
        
        return angle_rad <= cone_angle_rad

    def scan(self, current_step: int) -> None:
        """
        Выполняет сканирование зоны на указанном шаге моделирования.
        
        Args:
            current_step: Текущий шаг моделирования
        """
        objects_data = self.dispatcher.get_objects_data()
        valid_targets = [
            obj_id for obj_id, (start_step, _) in objects_data.items()
            if start_step <= current_step and self.is_target_in_range(objects_data[obj_id])
        ]
        
        followed_targets = self.radar_controller.get_followed_targets()
        
        for obj_id in valid_targets:
            target_data = objects_data[obj_id]
            current_pos = self._get_current_position(target_data, current_step)
            current_speed = self._get_current_speed(target_data, current_step)
            
            noise = (random.random() - 0.5) * self.noise_level
            noisy_pos = (
                current_pos[0] + noise,
                current_pos[1] + noise,
                current_pos[2] + noise
            )
            
            if obj_id in self.detected_objects:
                target = self.detected_objects[obj_id]
                target.update_position(noisy_pos)
                target.update_speed_vector(current_speed)
                
                if obj_id in followed_targets:
                    target.update_status(TargetStatus.FOLLOWED)
                    self.followed_targets[obj_id] = target
            else:
                new_target = target_data.__class__(
                    target_id=obj_id,
                    coords=noisy_pos,
                    speed_vector=current_speed
                )
                self.detected_objects[obj_id] = new_target
                
                if obj_id in followed_targets:
                    new_target.update_status(TargetStatus.FOLLOWED)
                    self.followed_targets[obj_id] = new_target
                    self.current_target_count += 1

        self._remove_outdated_targets(valid_targets)

    def _get_current_position(
        self, 
        target_data: Tuple[int, List[Tuple[float, float, float]]],
        current_step: int
    ) -> Tuple[float, float, float]:
        """Возвращает позицию цели на текущем шаге."""
        start_step, coords = target_data
        idx = current_step - start_step
        return coords[idx]

    def _get_current_speed(
        self,
        target_data: Tuple[int, List[Tuple[float, float, float]]],
        current_step: int
    ) -> Tuple[float, float, float]:
        """Возвращает вектор скорости на текущем шаге."""
        start_step, coords = target_data
        idx = current_step - start_step
        next_idx = idx + 1 if idx + 1 < len(coords) else idx
        
        return (
            coords[next_idx][0] - coords[idx][0],
            coords[next_idx][1] - coords[idx][1],
            coords[next_idx][2] - coords[idx][2]
        )

    def _remove_outdated_targets(self, valid_target_ids: List[str]) -> None:
        """Удаляет цели, которые больше не в зоне действия."""
        for target_id in list(self.detected_objects.keys()):
            if target_id not in valid_target_ids and self.detected_objects[target_id].can_be_removed():
                self.detected_objects.pop(target_id)
                if target_id in self.followed_targets:
                    self.followed_targets.pop(target_id)
                    self.current_target_count -= 1

    def get_detected_objects(self) -> Dict[str, Target]:
        """Возвращает обнаруженные цели."""
        return self.detected_objects

    def track_target(self, target_id: str) -> None:
        """Начинает сопровождение цели."""
        if target_id in self.detected_objects:
            target = self.detected_objects[target_id]
            target.update_status(TargetStatus.FOLLOWED)
            self.followed_targets[target_id] = target
            self.current_target_count += 1

    def mark_target_as_destroyed(self, target_id: str) -> None:
        """Помечает цель как уничтоженную."""
        if target_id in self.detected_objects:
            target = self.detected_objects[target_id]
            target.update_status(TargetStatus.DESTROYED)
            
            if target_id in self.followed_targets:
                self.followed_targets.pop(target_id)
                self.current_target_count -= 1
            
            if target.can_be_removed():
                self.detected_objects.pop(target_id)

class RadarController:
    """Контроллер радаров, обрабатывающий сообщения от системы моделирования"""
    
    def __init__(self, control_center, dispatcher):
        self.control_center = control_center
        self.dispatcher = dispatcher
        self.radars = []  # type: Dict[id: Radar]
        self.all_targets = {}  # type: Dict[id: Target]
        self.all_missiles = {}  # type: Dict[id: Missile]
        self.followed_targets = [] # type: List[int] 
        
    def add_radar(self, radar: Radar) -> None:
        """Добавляет радар под управление контроллера"""
        self.radars.append(radar)
        
    def update(self, current_step: int) -> None:
        """Обновляет состояние всех радаров"""
        for radar in self.radars:
            radar.scan()
            self.all_targets.extend(radar.get_detected_objects())
            
    def process_message(self) -> None:
        """Обрабатывает входящие сообщения"""
        messages = dispatcher.get_message()
        
        handlers = {
            'CCIoRadarFollowThisTarget': self._handle_follow_target,
            'CCIoRadarRocketAdd': self._handle_add_rocket,
            'CCioRadarRocketUpdate': self._handle_rocket_update,
            'RadarioCCPlanesDetected': self._handle_planes_detected,
            'RadarioCCPlaneKilled': self._handle_plane_killed,
            'RadarioCCRocketsLocation': self._handle_rockets_location,
            'RadarioGUICurrentTarget': self._handle_gui_target
        }
        for message in messages:
            msg_type = type(message)
            handlers[msg_type](message)

    def _handle_follow_target(self, message) -> bool:
        """
        Функция для переведения статуса цели в режим FOLLOWED
        """
        planeid = message.get_data()
        self.update()
        if planeid in self.all_targets:
            self.all_targets[planeid].update_status(new_status: TargetStatus.FOLLOWED)
            return True
        else: return False

    def _handle_add_rocket(self, message) -> bool:
        """
        Функция для привязки ракеты к цели
        """
        missleid, coords, planeid = message.get_data()
        self.update()
        if planeid in self.all_targets:
            self.all_targets[planeid].attach_missile(self, missile_id: str)
            return True
        else: return False

        
    def _handle_rocket_update(self, message):
        """
        ???
        """
        pass

    def _handle_planes_detected(self, message) -> None:
        """
        Функция для отправления списка замеченный целей  
        """
        self.update()
        targets = self.all_targets
        message = RadartoCCPlanesDetected(data=targets)
        self.dispatcher.send_message(message)
                
    def _handle_rockets_location(self, message) -> None:
        """Обрабатывает сообщение о местоположении ракет"""
        self.update()
        rockets = self.all_missiles
        message = RadartoCCRocketsLocation(rockets)
        self.dispatcher.send_message(message)

    def _handle_gui_target(self, message) -> None:
        """
        Отправка сопровождаемой цели GUI

        """
        pass
                      
    def get_all_radars(self) -> Dict[str: Radar]:
        """Возвращает список всех радаров"""
        return self.radars
        
    def get_all_detected_objects(self) -> Dict[str: Target]:
        """Возвращает список всех обнаруженных объектов"""
        return self.all_targets