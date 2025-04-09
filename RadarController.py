from enum import Enum
from _ import CCToRadarNewStatus, RadarToGUICurrentTarget, RadarControllerObjects, SEKilled, SEStarting, SEAddRocket
from _ import Missile

class TargetStatus(Enum):
    """Статусы цели для системы слежения."""
    DESTROYED = 0
    DETECTED = 1
    FOLLOWED = 2


class Target:
    """Базовый класс для всех объектов, обнаруживаемых радаром."""

    def __init__(
        self,
        target_id: str,
        clear_coords: list[(int, int, int)],
        status: TargetStatus = TargetStatus.DETECTED,
    ) -> None:
        self.id = target_id
        self.status = status
        self.clear_coords = clear_coords
        self.current_coords = (0, 0, 0)
        self.current_speed_vector = (0, 0, 0)
        self.attached_missiles = {}

    def update_current_coords(self, new_coords: tuple[int, int, int]):
        """Обновить текущие координаты"""
        self.current_coords = new_coords    

    def update_speed_vector(self, new_speed_vector: tuple[int, int, int]):
        """Обновить текущий вектор скорости"""
        self.current_speed_vector = new_speed_vector  

    def update_status(self, new_status: TargetStatus):
        """Обновляет статус объекта."""
        self.status = new_status

    def attach_missile(self, missile: Missile):
        """Добавляет ракету к списку привязанных."""
        self.attached_missiles[missile.missileID] = missile
        
    def detach_missile(self, missile_id: str):
        """Удаляет ракету из списка привязанных."""
        if missile_id in self.attached_missiles:
            self.attached_missiles.pop(missile_id)


class MissileStatus(Enum):
    ACTIVE = 1  # ракета ещё нужна
    INACTIVE = 0  # ракета больше не нужна

class Missile:
    def __init__(self, missileID, start_time, damageRadius, targetid, clear_coords, status=MissileStatus.ACTIVE):
        self.missileID = missileID
        self.status = status
        self.start_time = start_time
        self.damageRadius = damageRadius
        self.targetid = targetid
        self.clear_coords = clear_coords
        self.current_coords = (0, 0, 0)
        self.current_speed_vector = (0, 0, 0)

    def update_current_coords(self, new_coords: tuple[int, int, int]):
        """Обновить текущие координаты"""
        self.current_coords = new_coords    

    def update_speed_vector(self, new_speed_vector: tuple[int, int, int]):
        """Обновить текущий вектор скорости"""
        self.current_speed_vector = new_speed_vector   
    
    def update_status(self, newstaus: MissileStatus):
        """Сережа может поменять статус"""
        self.status = newstaus

class Radar:
    """Реализован ниже"""
    pass

class RadarController:
    """Контроллер радаров, обрабатывающий сообщения от системы моделирования"""
    
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.radars = {}, 
        self.all_targets = {},  
        self.detected_targets = {}, 
        self.all_missiles = {},
        
    def add_radar(self, radar: Radar):
        """Добавляет радар под управление контроллера"""
        self.radars[radar.radar_id] = radar
        
    def update(self, step: int):
        """Обновляет состояние всех радаров"""
        for radar in self.radars.values():
            radar.scan(step)
            
    def process_message(self):
        """Обрабатывает входящие сообщения(Я получаю список сообщений, или одно сообщение?)"""
        messages = self.dispatcher.get_message()
        for message in messages:
            if type(message) == CCToRadarNewStatus:
                self.update_status(message)
            if type(message) == SEKilled:
                self.kill_object(message)
            if type(message) == SEStarting:
                self.start(message)
            if type(message) == SEAddRocket:
                self.add_rocket(message)

    def update_status(self, message: CCToRadarNewStatus):
        """Обновление статуса цели"""
        object_id, new_status = message.target_new_status
        self.detected_targets[object_id].update_status(new_status)

    def kill_object(self, message: SEKilled):
        """Обновление статуса цели на DESTROYED и отвязка уничтоженной ракеты"""
        kill_rocket_id = message.rocketId
        kill_target_id = message.planeId
        killed_target = self.detected_target[kill_target_id]
        killed_target.update_status(TargetStatus.DESTROYED)
        killed_target.attached_missiles.pop(kill_rocket_id)
        if len(killed_target.attached_missiles) == 0:
            self.detected_targets.pop(kill_target_id)

    def start(self, message: SEStarting):
        """Функция для получения начальных данных о целях в небе"""
        targets = message.planes
        for targetid in targets.keys():
            target_coords = targets[targetid]
            new_target = Target(targetid, clear_coords=target_coords)
            self.all_targets[targetid] = new_target

    def add_rocket(self, message: SEAddRocket):
        """Добавить id ракет и их координаты в данные ракеты(??? не доделан)"""
        rocketId = message.rocketId
        rocketCoords = message.rocketCoords
        self.all_missiles[rocketId] = rocketCoords

    def send_current_target(self, radar_id, target_id, sector_size):
        """Отправить сообщение о приследуемой цели"""
        message = RadarToGUICurrentTarget(radar_id,target_id,sector_size)
        self.dispatcher.send_message(message)

    def send_detected_objects(self):
        """Отправить список замеченных целей"""
        message = RadarControllerObjects(detected_objects=self.detected_objects)
        self.dispatcher.send_message(message)

    
class Radar:
    """Класс радара. ЕЩЕ НЕ ДОДЕЛАН"""

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