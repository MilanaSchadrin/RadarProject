import math
import time
import numpy as np
from typing import List, Tuple
from typing import Dict
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen, QConicalGradient
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QTransform, QFont


class Icon(QLabel):
    def __init__(self, image_path, size, parent=None):
        super().__init__(parent)
        self.setFixedSize(*size)
        self._angle = 0
        self.original_pixmap = QPixmap(image_path)
        self.update_pixmap()

    def update_pixmap(self):
        scaled = self.original_pixmap.scaled(self.size(), Qt.KeepAspectRatio,Qt.SmoothTransformation)
        transform = QTransform()
        transform.rotate(self._angle)
        rotated = scaled.transformed(transform,Qt.SmoothTransformation)
        new_pixmap = QPixmap(self.size())
        new_pixmap.fill(Qt.transparent)
        painter = QPainter(new_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.drawPixmap((new_pixmap.width() - rotated.width()) // 2,(new_pixmap.height() - rotated.height()) // 2,rotated)
        painter.end()
        self.setPixmap(new_pixmap)

    def rotate_to(self, angle_degrees):
        self._angle = angle_degrees
        self.update_pixmap()


class RocketIcon(Icon):
    def __init__(self, image_path, parent=None):
        super().__init__(image_path, size=(30, 30), parent=parent)


class PlaneImageIcon(Icon):
    def __init__(self, image_path, parent=None):
        super().__init__(image_path, size=(20, 20), parent=parent)


class RadarIcon(QLabel):
    def __init__(self, image_path, x, y, radius=200, parent=None):
        super().__init__(parent)
        self.radar_image = QPixmap(image_path)
        self.setPixmap(self.radar_image)
        self.setScaledContents(True)
        self.setFixedSize(30, 30)
        self.move(int(x),int(y))
        self.x_pos = x
        self.y_pos = y
        self.radius = radius
        self.setAttribute(Qt.WA_TranslucentBackground)

class PIcon(QLabel):
    def __init__(self, pu_path, x, y, size_x, size_y,parent=None):
        super().__init__(parent)
        self.pu_image = QPixmap(pu_path)
        self.setPixmap(self.pu_image)
        self.setScaledContents(True)
        self.setFixedSize(size_x, size_y)
        self.move(x, y)
        self.setAttribute(Qt.WA_TranslucentBackground)


class MapView(QFrame):
    def __init__(self, db_manager):
        super().__init__()
        self.setStyleSheet("background-color: white;")
        self.trails = {}  # {id: [points]}
        #self.background_image = QPixmap('./vizualization/pictures/background.png')
        #self.pu_image = PUIcon('./vizualization/pictures/pu.png', 650, 450, parent=self)
        self.pu_image = []
        self.cc_icon = None
        #обработка коллизий
        self.explosions = {}
        self.damage_markers = {}
        self.explosion_clouds = {}
        self.visible_objects={}
        #РЛС
        self.radars = {} #{radar_id:{'icon': RadarIcon, 'radius': int, 'view_angle':int}}
        self.target_smoothing={}
        self.smoothing_steps=10
        self.rls_radius = 300
        self.view_angle = 45
        self.tracked_targets = {} #{target_id: {'radar_id':int, 'azimuth': float}
        self.scan_angle = 0
        self.scan_speed =2
        self.scan_width = 45
        self.detection_effects = []        
        self.current_step = 0
        self.max_step = 0
        self.simulation_data = []
        #отрисовка осей
        self.grid_step = 100
        self.axis_width=2
        self.axis_offset = 20
        self.font = QFont('Arial', 8)
        self.axis_color = Qt.black
        self.grid_color = QColor(220, 220, 220,150)
        self.db_manager = db_manager
        self.load_radars_from_db()
        self.load_and_draw_launchers()
        self.load_and_draw_cc()

    def load_radars_from_db(self):
        if self.db_manager:
            radars_data = self.db_manager.load_radars()
            for radar_id, radar in radars_data.items():
                self.add_radar(radar_id, x=radar['position'][0], y=radar['position'][1], radius=radar['range_input'],view_angle=radar['angle_input'])

    def add_radar(self, radar_id, x, y, radius, view_angle):
        self.radars[radar_id] = {'icon': RadarIcon('./vizualization/pictures/radar.png', x, y, radius, self), 'radius': radius, 'view_angle': view_angle, 'scan_angle': 0}

    def load_and_draw_launchers(self):
        launchers = self.db_manager.load_launchers()
        for launcher_id, launcher_data in launchers.items():
            x, y = launcher_data['position'][0], launcher_data['position'][1]
            pu_icon = PIcon('./vizualization/pictures/pu.png', int(x), int(y),70,70, parent = self)
            self.pu_image.append(pu_icon)
    def load_and_draw_cc(self):
        cc_data = self.db_manager.load_cc()
        if cc_data:
            first_cc = next(iter(cc_data.values()))
            x, y = first_cc['position'][0],  first_cc['position'][1]
            self.cc_icon = PIcon('./vizualization/pictures/pbu.png',  int(x), int(y), 40, 40, parent=self)

    def set_simulation_data(self, simulation_data):
        self.simulation_data = simulation_data
        self.max_step = len(simulation_data) - 1
        self.current_step = 0
        self.prepare_visual_objects()
        self.update()

    def prepare_visual_objects(self):
        self.visible_objects = {'planes': {}, 'rockets': {}, 'explosions': {},'damages': {}}
        for step in range(self.max_step + 1):
            step_data = self.simulation_data[step]
            for msg in step_data['messages']:
                self._process_message_for_visual(msg, step)

    def _process_message_for_visual(self, msg, step):
        if msg['type'] == 'plane_start':
            for plane_id, coords in msg['data'].planes.items():
                if plane_id not in self.visible_objects['planes']:
                    self.visible_objects['planes'][plane_id] = {'coords': [], 'steps': []}
                self.visible_objects['planes'][plane_id]['coords'].append(coords)
                self.visible_objects['planes'][plane_id]['steps'].append(step)
        elif msg['type'] == 'rocket_add':
            rocket = msg['data']
            self.visible_objects['rockets'][rocket.rocket_id] = {'coords': [rocket.rocket_coords], 'steps': [step]}
        elif msg['type'] == 'explosion':
            explosion = msg['data']
            self.visible_objects['explosions'][f"{explosion.rocket_id}_{explosion.plane_id}"] = {'center': QPoint( int((explosion.rocket_coords[0] + explosion.plane_coords[0]) / 2), int((explosion.rocket_coords[1] + explosion.plane_coords[1]) / 2)),
                                                                                                'step': step, 'radius': self.calculate_blast_radius(QPoint(int((explosion.rocket_coords[0] + explosion.plane_coords[0]) / 2),int((explosion.rocket_coords[1] + explosion.plane_coords[1]) / 2)),
                                                                                                [QPoint(int(explosion.rocket_coords[0]), int(explosion.rocket_coords[1])),
                                                                                                QPoint(int(explosion.plane_coords[0]), int(explosion.plane_coords[1]))]),'max_steps': 20}
    def set_current_step(self, step):
        if 0 <= step <= self.max_step:
            self.current_step = step
            self.update_target_azimuths()
            self.update_effects()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_scale(painter)
        #if not self.background_image.isNull():
            # painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
        self.draw_radar_sector(painter)
        for exp in self.explosions.values():
            steps_passed = self.current_step - exp['start_step']
            if 0 <= steps_passed < exp['duration']:
                core_color = QColor(255, 165, 0, exp['alpha'])
                painter.setPen(QPen(core_color, 4))
                painter.setBrush(QBrush(core_color, Qt.SolidPattern))
                painter.drawEllipse(exp['center'], exp['current_radius'], exp['current_radius'])
                if steps_passed < exp['duration'] * 0.7:
                    wave_alpha = int(exp['alpha'] * 0.7)
                    wave_color = QColor(255, 100, 0, wave_alpha)
                    painter.setPen(QPen(wave_color, 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawEllipse(exp['center'], int(exp['current_radius'] * 1.3), int(exp['current_radius'] * 1.3))
        for dmg in self.damage_markers.values():
            steps_passed = self.current_step - dmg['start_step']
            if 0 <= steps_passed < dmg['duration']:
                size = 8 + int(10 * (1 - steps_passed / dmg['duration']))
                dmg_color = QColor(255, 50, 0, dmg['alpha'])
                painter.setPen(QPen(dmg_color, 2))
                pos = dmg['position']
                painter.drawLine(pos.x()-size, pos.y()-size, pos.x()+size, pos.y()+size)

    def draw_scale(self, painter):
        painter.save()
        w, h = self.width(), self.height()
        painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
        for x in range(0, w, self.grid_step):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, self.grid_step):
            painter.drawLine(0, y, w, y)
        painter.setPen(QPen(self.axis_color, self.axis_width))
        x_axis_y = self.axis_offset
        painter.drawLine(self.axis_offset, x_axis_y, w - self.axis_offset, x_axis_y)
        y_axis_x = self.axis_offset
        painter.drawLine(y_axis_x, self.axis_offset, y_axis_x, h - self.axis_offset)
        arrow_size = 10
        painter.drawLine(w - self.axis_offset, x_axis_y,  w - self.axis_offset - arrow_size, x_axis_y + arrow_size//2)
        painter.drawLine(w - self.axis_offset, x_axis_y, w - self.axis_offset - arrow_size, x_axis_y - arrow_size//2)
        painter.drawLine(y_axis_x, h - self.axis_offset, y_axis_x - arrow_size//2, h - self.axis_offset - arrow_size)
        painter.drawLine(y_axis_x, h - self.axis_offset, y_axis_x + arrow_size//2, h - self.axis_offset - arrow_size)
        painter.setFont(self.font)
        for x in range(0, w, self.grid_step):
            if self.axis_offset <= x <= w - self.axis_offset:
                painter.drawText(x - 10, x_axis_y - 5, f"{x}")
        for y in range(0, h, self.grid_step):
            if self.axis_offset <= y <= h - self.axis_offset:
                painter.drawText(y_axis_x + 5, y + 5, f"{y}")
        painter.drawText(w - self.axis_offset + 10, x_axis_y - 5, "X")
        painter.drawText(y_axis_x - 15, self.axis_offset + 15, "Y")
        painter.restore()

    def update_radar_targets(self, targets):
        for target_id, radar_data in targets.items():
            for radar_id, (x, y) in radar_data.items():
                radar = self.radars[radar_id]
                radar_center = QPoint(radar.x_pos + radar.width()//2, radar.y_pos + radar.height()//2)
                trail_key = (radar_id, target_id)
                if trail_key not in self.trails:
                    self.trails[trail_key] = []
                self.trails[trail_key].append(QPoint(x, y))
                '''
                if len(self.trails[trail_key]) > 50:
                        self.trails[trail_key] = self.trails[trail_key][-50:]
                '''
                dx = x - radar_center.x()
                dy = radar_center.y() - y
                azimuth = math.degrees(math.atan2(dy, dx)) % 360
                distance = math.sqrt(dx*dx + dy*dy)
                if target_id not in self.tracked_targets:
                    self.tracked_targets[target_id] = {}
                self.tracked_targets[target_id][radar_id] = {'azimuth': azimuth,'distance': distance }

    def draw_radar_sector(self, painter):
        current_time = time.time()
        for radar_id, radar_data in self.radars.items():
            radar_icon = radar_data['icon']
            radar_center = QPointF(
                radar_icon.x_pos + radar_icon.width() // 2,
                radar_icon.y_pos + radar_icon.height() // 2
            )
            if 'last_scan_update' not in radar_data:
                radar_data['last_scan_update'] = current_time
                radar_data['scan_angle'] = 0
            scan_speed = 45
            time_diff = current_time - radar_data['last_scan_update']
            radar_data['scan_angle'] = (radar_data['scan_angle'] + time_diff * scan_speed) % 360
            radar_data['last_scan_update'] = current_time
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
            painter.setPen(QPen(QColor(0, 180, 0), 2))
            scan_rect = QRectF(
                radar_center.x() - radar_data['radius'],
                radar_center.y() - radar_data['radius'],
                radar_data['radius'] * 2,
                radar_data['radius'] * 2
            )
            start_angle = -(radar_data['scan_angle'] - radar_data['view_angle'] / 2) * 16
            span_angle = -radar_data['view_angle'] * 16
            painter.drawPie(scan_rect, int(start_angle), int(span_angle))
            dash_pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
            dash_pen.setDashPattern([4, 4])
            for target_id, target_data in self.tracked_targets.items():
                if target_id not in self.trails or not self.trails[target_id]:
                    continue
                target_point = self.trails[target_id][-1]
                dx = target_point.x() - radar_center.x()
                dy = radar_center.y() - target_point.y()
                azimuth = np.degrees(np.arctan2(dy, dx)) % 360
                distance = np.sqrt(dx**2 + dy**2)
                if distance > radar_data['radius']:
                    continue
                painter.setPen(dash_pen)
                ray_length = distance * 0.95
                end_x = radar_center.x() + ray_length * np.cos(np.radians(azimuth))
                end_y = radar_center.y() - ray_length * np.sin(np.radians(azimuth))
                painter.drawLine(radar_center, QPointF(end_x, end_y))
                painter.setBrush(QBrush(Qt.red))
                painter.drawEllipse(QPointF(end_x, end_y), 3, 3)

    def update_radar_scan(self):
        for radar_data in self.radars.values():
            radar_data['scan_angle'] = (radar_data['scan_angle'] + self.scan_speed) % 360

    def update_step(self,step):
        self.current_step=step
        if step<=self.max_step:
            self.scan_angle = (self.scan_angle + self.scan_speed) % 360
            self.update_target_azimuths()
            self.process_rls_events(self.simulation_data[step])
            self.update()

    def process_rls_events(self, step_data):
        if 'radar_tracking' in step_data:
            for event in step_data['radar_tracking']:
                self.handle_target_detection(event['target_id'])

    def handle_target_detection(self, radar_id, target_id,size):
        if target_id not in self.tracked_targets:
            self.tracked_targets[target_id] = {'radar_id' : radar_id, 'size': size}
            self.update()

    def update_target_azimuths(self):
        updated = False
        for target_id, target_data in self.tracked_targets.items():
            if target_id in self.trails and self.trails[target_id]:
                radar_id = target_data['radar_id']
                if radar_id in self.radars:
                    radar_icon = self.radars[radar_id]['icon']
                    radar_center = QPoint(radar_icon.x_pos + radar_icon.width()//2,
                                                 radar_icon.y_pos + radar_icon.height()//2)
                    target_point = self.trails[target_id][-1]
                    dx = target_point.x() - radar_center.x()
                    dy = radar_center.y() - target_point.y()
                    self.tracked_targets[target_id]['azimuth'] = (np.degrees(np.arctan2(dy, dx))) % 360
                    updated = True
        if updated:
            self.update()

    def add_explosion(self, step, explosion_data):
        explosion_id = f"explosion_{step}"
        center = QPoint(int(explosion_data['x']), int(explosion_data['y']))
        radius = explosion_data.get('radius', 80)
        self.explosions[explosion_id] = {'center': center,'max_radius': radius, 'current_radius': radius // 4,   'alpha': 180, 'start_step': step,'duration': explosion_data.get('duration', 10)  }
        for damage in explosion_data.get('damages', []):
            self.add_damage_marker(step, damage)

    def add_damage_marker(self, step, damage_data):
        damage_id = f"damage_{step}_{damage_data['id']}"
        pos = QPoint(int(damage_data['x']), int(damage_data['y']))
        self.damage_markers[damage_id] = {'position': pos, 'alpha': 180,'start_step': step,'duration': damage_data.get('duration', 20)}

    def update_explosion_effects(self):
        to_remove = []
        for exp_id, cloud in self.explosion_clouds.items():
            cloud['step'] += 1
            cloud['current_radius'] = min(cloud['max_radius'], cloud['current_radius'] + 2)
            cloud['alpha'] = max(10, cloud['alpha'] - 2)
            if cloud['step'] >= cloud['max_steps']:
                to_remove.append(exp_id)
            for exp_id in to_remove:
                del self.explosion_clouds[exp_id]
            if to_remove:
                self.update()

    def calculate_blast_radius(self, center: QPoint, all_points: List[QPoint]) -> int:
        if not all_points:
            return 50
        max_distance = max(np.sqrt((point.x() - center.x())**2 + (point.y() - center.y())**2) for point in all_points)
        return min(150, max(50, int(max_distance * 1.2)))

    def add_blast_effect(self, rocket_id: int, rocket_coords: np.ndarray, plane_id: int, plane_coords: np.ndarray, collateral_damage: List[Tuple[int, np.ndarray]]):
        center = QPoint(int((rocket_coords[0] + plane_coords[0]) / 2), int((rocket_coords[1] + plane_coords[1]) / 2))
        all_points = [center]
        all_points.extend(QPoint(int(c[0]), int(c[1])) for _, c in collateral_damage)
        blast_radius = self.calculate_blast_radius(center, all_points)
        explosion_id = f"blast_{rocket_id}_{plane_id}"
        self.explosions[explosion_id] = {'center': center,'max_radius': blast_radius, 'current_radius': 10, 'alpha': 180, 'step': 0,'max_steps': 3}
        for obj_id, coords in collateral_damage:
            point = QPoint(int(coords[0]), int(coords[1]))
            self.damage_markers[f"damage_{obj_id}"] = {'position': point, 'alpha': 180, 'step': 0, 'max_steps': 40}

    def update_effects(self):
       to_remove = []
       for exp_id, exp in self.explosions.items():
            exp['step'] += 1
            exp['current_radius'] = min(exp['max_radius'], exp['current_radius'] + exp['max_radius'] // 10)
            if exp['step'] > exp['max_steps'] // 2:
                exp['alpha'] = max(0, exp['alpha'] - 15)
            if exp['step'] >= exp['max_steps']:
                to_remove.append(exp_id)
       for exp_id in to_remove:
            del self.explosions[exp_id]
       to_remove_dmg = []
       for dmg_id, dmg in self.damage_markers.items():
            dmg['step'] += 1
            dmg['alpha'] = max(0, dmg['alpha'] - 5)
            if dmg['step'] >= dmg['max_steps']:
                to_remove_dmg.append(dmg_id)
       for dmg_id in to_remove_dmg:
            del self.damage_markers[dmg_id]
       if to_remove or to_remove_dmg:
            self.update()

    def add_to_trail(self, obj_id, point):
       if obj_id not in self.trails:
            self.trails[obj_id] = []
       self.trails[obj_id].append(QPointF(point))
       self.update()

    def process_explosion_message(self, msg: dict):
        center = QPoint(int((msg['rocket_coords'][0] + msg['plane_coords'][0]) / 2),int((msg['rocket_coords'][1] + msg['plane_coords'][1]) / 2))
        all_points = [center]
        all_points.extend(QPoint(int(c[0]), int(c[1])) for _, c in msg['collateral_damage'])
        blast_radius = self.calculate_blast_radius(center, all_points)
        explosion_id = f"blast_{msg['rocket_id']}_{msg['plane_id']}_{msg['collision_step']}"
        self.explosions[explosion_id] = {'center': center, 'max_radius': blast_radius, 'current_radius': blast_radius // 4, 'alpha': 180, 'start_step': msg['collision_step'], 'duration': 15  }
        for obj_id, coords in msg['collateral_damage']:
            damage_id = f"damage_{obj_id}_{msg['collision_step']}"
            self.damage_markers[damage_id] = {'position': QPoint(int(coords[0]), int(coords[1])), 'alpha': 180, 'start_step': msg['collision_step'],'duration': 25  }

    def update_effects(self):
        to_remove = []
        for exp_id, exp in self.explosions.items():
            steps_passed = self.current_step - exp['start_step']
            if steps_passed < 0:
                continue
            if steps_passed >= exp['duration']:
                to_remove.append(exp_id)
                continue
            progress = steps_passed / exp['duration']
            exp['current_radius'] = int(exp['max_radius'] * min(1.0, progress * 1.5))
            exp['alpha'] = int(180 * (1 - progress))
        for exp_id in to_remove:
            del self.explosions[exp_id]
        to_remove_dmg = []
        for dmg_id, dmg in self.damage_markers.items():
            steps_passed = self.current_step - dmg['start_step']
            if steps_passed >= dmg['duration']:
                to_remove_dmg.append(dmg_id)
                continue
            dmg['alpha'] = int(180 * (1 - steps_passed / dmg['duration']))
        for dmg_id in to_remove_dmg:
            del self.damage_markers[dmg_id]

