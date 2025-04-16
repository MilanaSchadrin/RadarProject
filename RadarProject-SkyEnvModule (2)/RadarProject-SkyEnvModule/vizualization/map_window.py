import math
import numpy as np
from typing import List, Tuple
from typing import Dict
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QTransform


class Icon(QLabel):
    def __init__(self, image_path, size=(60, 60), parent=None):
        super().__init__(parent)
        self.original_pixmap = QPixmap(image_path)
        self.setScaledContents(True)
        self.setFixedSize(*size)
    def rotate_to(self, angle_degrees):
        transform = QTransform()
        transform.rotate(angle_degrees)
        rotated = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        self.setPixmap(rotated)


class RocketIcon(Icon):
    def __init__(self, image_path, parent=None):
        super().__init__(image_path, size=(60, 60), parent=parent)


class PlaneImageIcon(Icon):
    def __init__(self, image_path, parent=None):
        super().__init__(image_path, size=(40, 40), parent=parent)


class RadarIcon(QLabel):
    def __init__(self, image_path, x, y, radius=200, parent=None):
        super().__init__(parent)
        self.radar_image = QPixmap(image_path)
        self.setPixmap(self.radar_image)
        self.setScaledContents(True)
        self.setFixedSize(70, 70)
        self.move(x, y)
        self.x_pos = x
        self.y_pos = y
        self.radius = radius
        self.setAttribute(Qt.WA_TranslucentBackground)

class PUIcon(QLabel):
    def __init__(self, pu_path, x, y, radius=200, parent=None):
        super().__init__(parent)
        self.pu_image = QPixmap(pu_path)
        self.setPixmap(self.pu_image)
        self.setScaledContents(True)
        self.setFixedSize(70, 70)
        self.move(x, y)
        self.setAttribute(Qt.WA_TranslucentBackground)


class MapView(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white;")
        self.trails = {}  # {id: [points]}
        self.background_image = QPixmap('./vizualization/pictures/background.png')
        #!!!
        #положения задать корректно; считать значения из бд
        self.radar = RadarIcon('./vizualization/pictures/radar.png', 250, 450, parent=self)
        self.pu_image = PUIcon('./vizualization/pictures/pu.png', 650, 450, parent=self)
        #обработка коллизий
        self.explosions = {}
        self.damage_markers = {}
        self.effect_timer = QTimer()
        self.effect_timer.timeout.connect(self.update_effects)
        self.effect_timer.start(500)
        #РЛС
        self.rls_radius = 0
        self.view_angle = 0
        self.tracked_targets = {}
        self.scan_angle = 0
        self.scan_timer = QTimer()
        self.scan_timer.timeout.connect(self.update_scan)
        self.scan_timer.start(100)
        self.track_timer = QTimer()
        self.track_timer.timeout.connect(self.update_targets_azimuth)
        self.track_timer.start(200)
        self.explosion_clouds = {}

    def add_explosion_cloud(self, explosion_id, center, radius=80):
        self.explosion_clouds[explosion_id] = {'center': center,'max_radius': radius, 'current_radius': 20, 'alpha': 40,  'step': 0, 'max_steps': 40}


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

    def calculate_blast_radius(self, center: QPoint, all_points: List[QPoint]) -> float:
        if not all_points:
            return 50
        max_distance = max(np.sqrt((point.x() - center.x())**2 + (point.y() - center.y())**2) for point in all_points)
        return min(150, max(50, max_distance * 1.2))


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
       self.trails[obj_id].append(QPoint(point))
       if len(self.trails[obj_id]) > 100:
            self.trails[obj_id] = self.trails[obj_id][-100:]
       self.update()


    def visualize_rls(self, target_id, angle=None, dist=None):
       if angle is not None:
            self.view_angle = angle
       if dist is not None:
            self.rls_radius = dist
       if target_id not in self.tracked_targets:
            self.tracked_targets[target_id] = 0
            self.update()

    def update_scan(self):
       self.scan_angle = (self.scan_angle + 10) % 360
       self.update()

    def update_targets_azimuth(self):
       radar_center = QPoint(self.radar.x_pos + self.radar.width()//2,self.radar.y_pos + self.radar.height()//2)
       updated = False
       for target_id in list(self.tracked_targets.keys()):
            if target_id in self.trails and self.trails[target_id]:
                target_point = self.trails[target_id][-1]
                dx = target_point.x() - radar_center.x()
                dy = radar_center.y() - target_point.y()
                self.tracked_targets[target_id] = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
                updated = True
       if updated:
            self.update()


    def paintEvent(self, event):
       painter = QPainter(self)
       if not self.background_image.isNull():
            painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
       painter.setPen(QPen(QColor(0, 0, 255), 2))
       #for trail in self.trails.values():
                  #  for i in range(1, len(trail)):
                       # painter.drawLine(trail[i-1], trail[i])

       radar_center = QPoint(self.radar.x_pos + self.radar.width()//2, self.radar.y_pos + self.radar.height()//2 )
       painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
       painter.setPen(QPen(QColor(0, 180, 0), 2))
       scan_rect = QRectF(radar_center.x() - self.rls_radius, radar_center.y() - self.rls_radius, self.rls_radius * 2,self.rls_radius * 2)
       start_angle = -(self.scan_angle - self.view_angle/2) * 16
       span_angle = -self.view_angle * 16
       painter.drawPie(scan_rect, int(start_angle), int(span_angle))
       dash_pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
       dash_pen.setDashPattern([4, 4])
       for target_id, azimuth in self.tracked_targets.items():
            if target_id in self.trails and self.trails[target_id]:
                target_point = self.trails[target_id][-1]
                dx = target_point.x() - radar_center.x()
                dy = target_point.y() - radar_center.y()
                distance_to_target = np.sqrt(dx*dx + dy*dy)
                ray_length = min(self.rls_radius, distance_to_target * 0.9)
                end_x = radar_center.x() + ray_length * np.cos(np.radians(azimuth))
                end_y = radar_center.y() - ray_length * np.sin(np.radians(azimuth))
                painter.setPen(dash_pen)
                painter.drawLine(radar_center, QPointF(end_x, end_y))
       for exp in self.explosions.values():
            #взрыв
            core_color = QColor(255, 165, 0, exp['alpha'])
            painter.setPen(QPen(core_color, 4))
            painter.setBrush(QBrush(core_color, Qt.SolidPattern))
            painter.drawEllipse(exp['center'], exp['current_radius'], exp['current_radius'])
            #волна взрыва
            if exp['current_radius'] > exp['max_radius'] // 2:
                wave_alpha = int(exp['alpha'] * 0.7)
                wave_color = QColor(255, 100, 0, wave_alpha)
                painter.setPen(QPen(wave_color, 2))
                painter.setBrush(QBrush(Qt.NoBrush))
                wave_radius = int(exp['current_radius'] * 1.3)
                painter.drawEllipse(exp['center'], wave_radius, wave_radius)

       for dmg in self.damage_markers.values():
            dmg_color = QColor(255, 50, 0, dmg['alpha'])
            painter.setPen(QPen(dmg_color, 2))
            size = 8 + int(10 * (1 - dmg['step'] / dmg['max_steps']))
            painter.drawLine(dmg['position'].x() - size, dmg['position'].y() - size,dmg['position'].x() + size, dmg['position'].y() + size)
            painter.drawLine(dmg['position'].x() - size, dmg['position'].y() + size,dmg['position'].x() + size, dmg['position'].y() - size)





