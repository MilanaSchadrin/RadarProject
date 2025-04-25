# This Python file uses the following encoding: utf-8
import math
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton,QWidget,QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF,QPropertyAnimation, QAbstractAnimation
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen
from vizualization.map_window import  MapView
from vizualization.map_window import PUIcon
from vizualization.map_window import RadarIcon
from vizualization.map_window import PlaneImageIcon
from vizualization.map_window import RocketIcon
from vizualization.map_window import Icon
from typing import List, Tuple
from typing import Dict


class MapWindow(QMainWindow):
    def __init__(self, ):
        super().__init__()
        self.setWindowTitle("Моделирование ЗРС")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        screen_geometry = QApplication.desktop().screenGeometry()
        self.resize(int(screen_geometry.width()*0.7), int(screen_geometry.height()*0.7))
        self.move(int(screen_geometry.width()*0.1), int(screen_geometry.height()*0.1))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        self.map_view = MapView()
        layout.addWidget(self.map_view, 3)
        self.setup_control_panel(layout)

        self.simulation_steps = []
        self.current_step = -1
        self.max_step = 0

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_step)
        self.playback_speed = 100
        self.text_output.append(f"Моделирование работы ЗРС")

        self.rockets = {}
        self.planes = {}
        self.tracked_targets = set()

        self.simulation_events = []  # List of events to be visualized
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_step)

        self.step_interv = 1000
        #self.playback_timer = QTimer(self)
        #self.playback_timer.timeout.connect(self.playback_speed)
        self.animation_duration = 600
        self.is_playing = False

        self.plane_animation_duration = 800
        self.rocket_animation_duration = 1000
        self.animation_steps = 20

    def setup_control_panel(self, main_layout):
         right_panel = QVBoxLayout()
         self.text_output = QTextEdit()
         self.text_output.setReadOnly(True)
         right_panel.addWidget(self.text_output, 3)
         self.setup_step_controls(right_panel)
         main_layout.addLayout(right_panel, 1)

    def setup_step_controls(self, panel_layout):
         step_controls = QHBoxLayout()
         self.prev_step_btn = QPushButton("Предыдущий шаг")
         self.next_step_btn = QPushButton("Следующий шаг")
         self.play_btn = QPushButton("Старт")
         self.stop_btn = QPushButton("Стоп")
         self.prev_step_btn.clicked.connect(self.prev_step)
         self.next_step_btn.clicked.connect(self.next_step)
         self.play_btn.clicked.connect(self.play_steps)
         self.stop_btn.clicked.connect(self.stop_playback)
         step_controls.addWidget(self.prev_step_btn)
         step_controls.addWidget(self.next_step_btn)
         step_controls.addWidget(self.play_btn)
         step_controls.addWidget(self.stop_btn)
         panel_layout.addLayout(step_controls)

    def set_simulation_data(self, steps_data):
         self.simulation_steps = steps_data
         self.map_view.set_simulation_data(steps_data)
         self.max_step = len(steps_data) - 1
         self.current_step = -1
         self.text_output.clear()
         self.text_output.append("Нажмите 'Старт' для начала")

    def reset_planes_state(self):
         for plane_id, plane_data in self.planes.items():
            plane_data['index'] = 0
            plane_data['last_pos'] = None
            plane_data['current_step'] = 0

    def play_steps(self):
          if self.current_step >= self.max_step:
            self.current_step = -1
          self.is_playing = True
          self.playback_timer.start(self.playback_speed)


    def stop_playback(self):
          self.playback_timer.stop()
          #self.is_playing = False

    def next_step(self):
          if not self.is_playing:
            return
          if self.current_step < self.max_step:
            self.current_step += 1
            self.update_visualization()
            self.map_view.update_step(self.current_step)
          if self.current_step == self.max_step:
            self.stop_playback()
    def prev_step(self):
          if self.current_step > 0 and self.is_playing:
            self.current_step -= 1
            self.update_visualization(instant_update=True)

    def update_visualization(self, instant_update=False):
          step_data = self.simulation_steps[self.current_step]
          self.process_step(step_data)
          self.text_output.append(f"\nШаг {self.current_step + 1}/{self.max_step + 1}")
          self.update_planes(instant_update)
          self.update_zur_positions(instant_update)
          self.update_radar_targets(self.tracked_targets)
           #self.map_view.update_radar_targets(self.tracked_targets)
          self.map_view.update()

    def update_radar_targets(self, target_ids = None):
          targets = {}
          if target_ids is not None:
                for target_id in target_ids:
                    if target_id in self.planes:
                        plane_data = self.planes[target_id]
                        coords = plane_data['coords']
                        idx = min(self.current_step, len(coords) - 1)
                        x, y = coords[idx]
                        targets[target_id] = (x, y)
          self.map_view.update_radar_targets(targets)

    def update_planes(self, instant_update=False):
          for plane_id, plane_data in self.planes.items():
                coords = plane_data['coords']
                target_idx = min(self.current_step, len(coords) - 1)
                target_x, target_y = coords[target_idx]
                if instant_update or plane_data.get('last_pos') is None:
                    plane_data['icon'].move(target_x - 10, target_y - 10)
                    plane_data['last_pos'] = (target_x, target_y)
                else:
                    self.animate_plane_movement(plane_data, target_x, target_y,plane_id)
                self.update_plane_rotation(plane_data, target_idx, coords)
                plane_data['last_pos'] = (target_x, target_y)

    def update_zur_positions(self, instant_update=False):
          for zur_id, zur_data in self.rockets.items():
                if 'first_appearance_step' not in zur_data:
                    continue
                if self.current_step >= zur_data['first_appearance_step']:
                    zur_data['icon'].show()
                    coords = zur_data['coords']
                    coord_idx = self.current_step - zur_data['first_appearance_step']
                    coord_idx = min(coord_idx, len(coords) - 1)
                    target_x, target_y = coords[coord_idx]
                    if instant_update or zur_data.get('last_pos') is None:
                        zur_data['icon'].move(target_x - 10, target_y - 10)
                        zur_data['last_pos'] = (target_x, target_y)
                        if self.current_step >zur_data.get('last_processed_step', -1):
                            self.map_view.add_to_trail(zur_id, QPointF(target_x, target_y))
                    else:
                        if self.is_playing:
                            self.animate_movement(zur_data, target_x, target_y,zur_id)
                        else:
                            zur_data['icon'].move(target_x -10, target_y -10)
                            self.map_view.add_to_trail(zur_id, QPointF(target_x, target_y))
                    self.update_rocket_rotation(zur_data, coord_idx, coords)
                    zur_data['last_pos'] = (target_x, target_y )
                    zur_data['last_processed_step'] = self.current_step
                else:
                    zur_data['icon'].hide()

    def update_rocket_rotation(self, rocket_data, target_idx, coords):
           if len(coords) <= 1:
                return
           if target_idx == 0:
                prev_x, prev_y = coords[0]
                next_x, next_y = coords[1]
           elif target_idx == len(coords) - 1:
                prev_x, prev_y = coords[target_idx - 1]
                next_x, next_y = coords[target_idx]
           else:
                prev_x, prev_y = coords[target_idx - 1]
                next_x, next_y = coords[target_idx + 1]
           dx = next_x - prev_x
           dy = next_y - prev_y
           angle_rad = math.atan2(dy, dx)
           angle_deg = math.degrees(angle_rad)
           rocket_data['icon'].rotate_to(((angle_deg + 90) % 360))

    def animate_movement(self, obj_data, target_x, target_y, obj_id, is_rocket=False):
           self.animation_in_progress = True
           icon = obj_data['icon']
           start_x, start_y = obj_data['last_pos']
           steps = self.animation_steps * (3 if is_rocket else 1)
           duration = self.rocket_animation_duration if is_rocket else self.plane_animation_duration
           anim = QPropertyAnimation(icon, b"pos")
           anim.setDuration(duration)
           anim.setStartValue(QPoint(start_x - 10, start_y - 10))
           anim.setEndValue(QPoint(target_x - 10, target_y - 10))
           def animation_finished():
                self.animation_in_progress = False
                if self.is_playing:
                    self.playback_timer.start(self.playback_speed)
           anim.finished.connect(animation_finished)
           anim.start(QAbstractAnimation.DeleteWhenStopped)

    def update_plane_rotation(self, plane_data, target_idx, coords):
           if len(coords) <= 1:
                return
           window_size = 3
           start_idx = max(0, target_idx - window_size)
           prev_x, prev_y = coords[start_idx]
           current_x, current_y = coords[target_idx]
           dx = current_x - prev_x
           dy = current_y - prev_y
           if abs(dx) < 0.1 and abs(dy) < 0.1:
                return
           angle_rad = math.atan2(dy, dx)
           angle_deg = math.degrees(angle_rad)
           correct_angle = (angle_deg + 90) % 360
           current_angle = plane_data.get('current_angle', correct_angle)
           angle_diff = (correct_angle - current_angle + 180) % 360 - 180
           max_angle_step = 30
           if abs(angle_diff) > max_angle_step:
                correct_angle = current_angle + max_angle_step * (1 if angle_diff > 0 else -1)
           plane_data['icon'].rotate_to(correct_angle)
           plane_data['current_angle'] = correct_angle

    def animate_plane_movement(self, plane_data, target_x, target_y, id):
           if not self.is_playing:
                return
           icon = plane_data['icon']
           start_x, start_y = plane_data['last_pos']
           steps = 6
           for i in range(1, steps + 1):
                if not self.is_playing:
                    break
                x = start_x + (target_x - start_x) * i / steps
                y = start_y + (target_y - start_y) * i / steps
                icon.move(int(x)-10, int(y)-10)
                self.map_view.add_to_trail(id, QPointF(x, y))

    def visualize_plane_track(self, plane_id, coords: np.ndarray):
           self.text_output.append(f"✈️ Самолет с ID {plane_id} появился в воздушном пространстве")
           if coords is None or len(coords) == 0:
                return
           coords = np.atleast_2d(coords)
           if coords.shape[1] < 2:
                return
           flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
           if plane_id not in self.planes:
                icon = PlaneImageIcon("./vizualization/pictures/airplane.webp", self)
                icon.setToolTip(f"ID самолёта: {plane_id}")
                icon.show()
                self.planes[plane_id] = {'icon': icon, 'coords': flat_coords,  'index': 0, 'last_pos': flat_coords[0], 'current_angle': 0}
                x, y = flat_coords[0]
                icon.move(x - 50, y - 50)
                self.map_view.add_to_trail(plane_id, QPoint(x, y))
           else:
                self.planes[plane_id]['coords'] = flat_coords

    def visualize_zur_track(self, zur_id, coords: np.ndarray):
           self.text_output.append(f'<span style="color: blue;">• Ракета с ID {zur_id} появилася в воздушном пространстве</span>')
           if coords is None or len(coords) == 0:
                return
           coords = np.atleast_2d(coords)
           if coords.shape[1] < 2:
                return
           flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
           if zur_id not in self.rockets:
                print("ZUR START", self.current_step)
                icon = RocketIcon("./vizualization/pictures/rocket.png", self)
                icon.setToolTip(f"ID ракеты: {zur_id}")
                self.rockets[zur_id] = {'icon': icon, 'coords': flat_coords, 'index': 0, 'last_pos': flat_coords[0], 'current_angle': 0, 'first_appearance_step': self.current_step, 'last_processed_step': -1}
                icon.show()
                #icon.hide()
                x, y = flat_coords[0]
                icon.move(x - 20, y - 20)
                self.map_view.add_to_trail(zur_id, QPoint(x, y))
                self.rockets[zur_id]['last_pos']= (x,y)
                self.rockets[zur_id]['last_processed_step'] =self.current_step
           else:
                        # Обновляем координаты существующей ракеты
                        self.rockets[zur_id]['coords'] = flat_coords
                        # Если ракета уже должна быть видна
                        if self.current_step >= self.rockets[zur_id]['first_appearance_step']:
                            self.rockets[zur_id]['icon'].show()
                            coord_idx = self.current_step - self.rockets[zur_id]['first_appearance_step']
                            coord_idx = min(coord_idx, len(flat_coords) - 1)
                            x, y = flat_coords[coord_idx]
                            self.rockets[zur_id]['icon'].move(x - 20, y - 20)
                            self.map_view.add_to_trail(zur_id, QPoint(x, y))
                            self.rockets[zur_id]['last_pos'] = (x, y)
                            self.rockets[zur_id]['last_processed_step'] = self.current_step

    def process_step(self, step_data):
           for msg in step_data['messages']:
                self.process_message(msg)

    def process_message(self, msg):
           try:
                if msg['type'] == 'plane_start':
                    for plane_id, coords in msg['data'].planes.items():
                        self.visualize_plane_track(plane_id, coords)
                elif msg['type'] == 'rocket_add':
                    rocket_data=msg['data']
                    self.visualize_zur_track(rocket_data.rocket_id, rocket_data.rocket_coords)
                elif msg['type'] == 'radar_tracking':
                    #print("RADAR", msg['data'].target_id)
                    self.map_view.handle_target_detection(msg['data'].target_id, msg['data'].sector_size)
                    self.text_output.append(f"Обнаружена цель{msg['data'].target_id}")
                    self.tracked_targets.add(msg['data'].target_id)
                elif msg['type'] == 'explosion':
                    print('Коллизия', msg['data'].collision_step, 'РАКЕТА',msg['data'].plane_id  )
                    print(msg['data'])
                    explosion_data = {'collision_step': msg['data'].collision_step, 'rocket_id': msg['data'].rocket_id, 'rocket_coords': msg['data'].rocket_coords,
                                                                    'plane_id': msg['data'].plane_id, 'plane_coords': msg['data'].plane_coords,
                                                                    'collateral_damage': [(damage[0], damage[1]) for damage in msg['data'].collateral_damage] if hasattr(msg['data'], 'collateral_damage') else []}
                    self.tracked_targets.remove(msg['data'].plane_id)
                    del self.map_view .trails[msg['data'].plane_id]
                    #self.log_explosion(self, rocket_id: int, plane_id: int, collateral_damage: List[Tuple[int, np.ndarray]])
                    self.handle_explosion_event(explosion_data)
                elif msg['type'] == 'rocket_inactivate':
                    rocket_id = msg['data'].rocketId
                    self.remove_object(rocket_id)
                    self.text_output.append(f'<span style="color: gray;">• Ракета с ID {rocket_id} деактивирована</span>')
           except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")


    def update_rls_visualization(self, step_data):
           if 'radar_tracking' in step_data:
                self.map_view.view_angle=60
                self.map_view.rls_radius=100
                self.map_view.scan_angle=60

    def handle_explosion_event(self, explosion_msg: dict):
           try:
                if hasattr(self, 'remove_object'):
                    self.remove_object(explosion_msg['rocket_id'])
                    self.remove_object(explosion_msg['plane_id'])
                if hasattr(self, 'map_view') and hasattr(self.map_view, 'process_explosion_message'):
                    self.map_view.process_explosion_message(explosion_msg)
                self.map_view.set_current_step(explosion_msg['collision_step'])
                self.update()
           except Exception as e:
                print(f"Ошибка обработки взрыва: {str(e)}")

    def remove_object(self, obj_id: int):
           if obj_id in self.rockets:
                self.rockets[obj_id]['icon'].hide()
                del self.rockets[obj_id]
           elif obj_id in self.planes:
                self.planes[obj_id]['icon'].hide()
                del self.planes[obj_id]
    '''
    def log_explosion(self, rocket_id: int, plane_id: int, collateral_damage: List[Tuple[int, np.ndarray]]):
        self.text_output.append(f'<span style="color: red; font-weight: bold;"> ВЗРЫВ! Ракета {rocket_id} сбила самолет {plane_id}</span>')
        if collateral_damage:
            damaged_objects = ", ".join([f"#{obj_id}" for obj_id, _ in collateral_damage])
            self.text_output.append(f'<span style="color: orange;">⚠️ Вторичные повреждения: {damaged_objects}</span>')
    '''
