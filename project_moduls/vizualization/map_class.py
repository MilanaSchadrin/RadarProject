# This Python file uses the following encoding: utf-8
import math
import time
import numpy as np
from typing import Optional
from PyQt5.QtWidgets import QApplication,QGraphicsEllipseItem, QMainWindow, QPushButton,QWidget,QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF,QPropertyAnimation, QRect, QSequentialAnimationGroup,QPauseAnimation, QAbstractAnimation, QParallelAnimationGroup
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen
from vizualization.map_window import  MapView
#from vizualization.map_window import PIcon
#from vizualization.map_window import RadarIcon
from vizualization.map_window import PlaneImageIcon
from vizualization.map_window import RocketIcon
#from vizualization.map_window import Icon
from typing import List, Tuple
from typing import Dict
import traceback

from types import SimpleNamespace
import numpy as np
import math

class MapWindow(QMainWindow):
    def __init__(self, db_manager):
        super().__init__()
        self.setWindowTitle("Моделирование ЗРС")
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint | Qt.WindowMaximizeButtonHint)
        screen_geometry = QApplication.desktop().screenGeometry()
        self.resize(int(screen_geometry.width()*0.7), int(screen_geometry.height()*0.7))
        self.move(int(screen_geometry.width()*0.1), int(screen_geometry.height()*0.1))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        self.map_view = MapView(db_manager)
        layout.addWidget(self.map_view, 3)
        self.setup_control_panel(layout)

        self.simulation_steps = []
        self.current_step = -1
        self.max_step = 0

        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_step)
        self.playback_speed = 50
        self.text_output.append(f"Моделирование работы ЗРС")

        self.rockets = {}
        self.planes = {}
        self.tracked_targets = {}

        self.simulation_events = []
        self.playback_timer = QTimer(self)
        self.playback_timer.timeout.connect(self.next_step)

        self.step_interv = 1000
        self.animation_duration = 600
        self.is_playing = False

        self.plane_animation_duration = 800
        self.rocket_animation_duration = 1000
        self.animation_steps = 20
        self.inactive_rockets = {}
        self.cross_visible_time = 500
        self.preserve_rotation_on_backward = True
        #self.rockets_data ... заполняем чhep data_collector
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
          self.preserve_rotation_on_backward=True
          if self.current_step >= self.max_step:
            self.current_step = -1
          self.is_playing = True
          self.playback_timer.start(self.playback_speed)


    def stop_playback(self):
          self.playback_timer.stop()
          #self.is_playing = False

    def next_step(self):
          self.preserve_rotation_on_backward=True
          if not self.is_playing:
            return
          if self.current_step < self.max_step:
            self.current_step += 1
            self.update_visualization()
            self.map_view.update_step(self.current_step)
          if self.current_step == self.max_step:
            self.stop_playback()
    def prev_step(self):
           self.preserve_rotation_on_backward = False
           if not self.is_playing:
                return
           if self.current_step   < self.max_step:
            self.current_step -= 1
            self.update_visualization()
            self.map_view.update_step(self.current_step)
            self.restore_objects_state()

    def restore_objects_state(self):
                for plane_id, plane_data in self.planes.items():
                    if 'pre_explosion_state' in plane_data:
                        if (plane_data['pre_explosion_state']['visible'] and
                                       ('explosion_step' not in plane_data or self.current_step < plane_data['explosion_step'])):
                                       plane_data['icon'].show()
                                       plane_data['icon'].setPos(plane_data['pre_explosion_state']['pos'])

                            #plane_data['icon'].show()
                            #plane_data['icon'].setPos(plane_data['pre_explosion_state']['pos'])
                    coords = plane_data['coords']
                    if self.current_step < len(coords):
                        if 'explosion_step' in plane_data and self.current_step >= plane_data['explosion_step']:
                                   plane_data['icon'].hide()
                                   continue
                        x, y = coords[self.current_step]
                        plane_data['icon'].setPos(QPointF(x, y))
                        plane_data['last_pos'] = (x, y)
                        plane_data['icon'].show()

                for rocket_id, rocket_data in self.rockets.items():
                    if 'pre_explosion_state' in rocket_data:
                        if rocket_data['pre_explosion_state']['visible']:
                            rocket_data['icon'].show()
                            rocket_data['icon'].setPos(rocket_data['pre_explosion_state']['pos'])

                    if 'first_appearance_step' in rocket_data and self.current_step >= rocket_data['first_appearance_step']:
                        if 'explosion_step' in rocket_data and self.current_step >= rocket_data['explosion_step']:
                                        rocket_data['icon'].hide()
                                        continue
                        current_coords = self.get_rocket_coords_at_step(rocket_id, self.current_step)
                        if current_coords is not None:
                            x, y = current_coords[0], current_coords[1]
                            rocket_data['icon'].setPos(QPointF(x, y))
                            rocket_data['last_pos'] = (x, y)
                            rocket_data['icon'].show()
                            # Убрано автоматическое обновление поворота при восстановлении состояния
                    else:
                        rocket_data['icon'].hide()

                for rocket_id, cross_label in list(self.inactive_rockets.items()):
                    cross_label.hide()
                    cross_label.deleteLater()
                    del self.inactive_rockets[rocket_id]


    def update_visualization(self, instant_update=False):
          step_data = self.simulation_steps[self.current_step]
          self.process_step(step_data)
          self.text_output.append(f"\nШаг {self.current_step + 1}/{self.max_step + 1}")
          self.update_planes(instant_update)
          self.update_zur_positions(instant_update)
          self.update_radar_targets(self.tracked_targets)
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
                if 'explosion_step' in plane_data and self.current_step >= plane_data['explosion_step']:
                  plane_data['icon'].hide()
                  continue
                coords = plane_data['coords']
                target_idx = min(self.current_step, len(coords) - 1)
                target_x, target_y = coords[target_idx]
                if instant_update or plane_data.get('last_pos') is None:
                    plane_data['icon'].setPos(QPointF(target_x , target_y ))
                    plane_data['last_pos'] = (target_x, target_y)
                else:
                    self.animate_plane_movement(plane_data, target_x, target_y,plane_id)
                self.update_plane_rotation(plane_data, target_idx, coords)
                plane_data['last_pos'] = (target_x, target_y)
    '''
    раньше работало
    def update_zur_positions(self, instant_update=False):
          for zur_id, zur_data in self.rockets.items():
                if 'first_appearance_step' not in zur_data:
                    continue
                if self.current_step >= zur_data['first_appearance_step']:
                    #zur_data['icon'].show()
                    coords = zur_data['coords']
                    coord_idx = self.current_step - zur_data['first_appearance_step']
                    coord_idx = min(coord_idx, len(coords) - 1)
                    target_x, target_y = coords[coord_idx]
                    if instant_update or zur_data.get('last_pos') is None:
                        zur_data['icon'].setPos(QPointF(target_x - 10, target_y - 10))
                        zur_data['last_pos'] = (target_x, target_y)
                        if self.current_step > zur_data.get('last_processed_step', -1):
                            self.map_view.add_to_trail(zur_id, QPointF(target_x, target_y))
                    else:
                        if self.is_playing:
                                self.animate_plane_movement(zur_data, target_x, target_y,zur_id)
                                #self.animate_movement(zur_data, target_x, target_y,zur_id)
                        else:
                                zur_data['icon'].setPos(QPointF(target_x -10, target_y -10))
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
    '''
    '''
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
    '''
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
                icon.setPos(QPointF(x, y))
                self.map_view.add_to_trail(id, QPointF(x, y))

    def visualize_plane_track(self, plane_id, coords: np.ndarray):
           self.text_output.append(f'<span style="color: blue;">✈️ Самолет с ID {plane_id} появился в воздушном пространстве')
           if coords is None or len(coords) == 0:
                return
           coords = np.atleast_2d(coords)
           if coords.shape[1] < 2:
                return
           flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
           if plane_id not in self.planes:
                icon = PlaneImageIcon("./vizualization/pictures/airplane.webp")
                icon.setToolTip(f"ID самолёта: {plane_id}")
                self.map_view.scene.addItem(icon)
                self.planes[plane_id] = {'icon': icon, 'coords': flat_coords,  'index': 0, 'last_pos': flat_coords[0], 'current_angle': 0}
                x, y = flat_coords[0]
                icon.setPos(QPointF(x, y))
                self.map_view.add_to_trail(plane_id, QPoint(x, y))
           else:
                self.planes[plane_id]['coords'] = flat_coords
    '''
    def visualize_zur_track(self, zur_id, coords: np.ndarray):
           if coords is None or len(coords) == 0:
                return
           coords = np.atleast_2d(coords)
           if coords.shape[1] < 2:
                return
           flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
           if zur_id not in self.rockets:
                icon = RocketIcon("./vizualization/pictures/rocket.png")
                icon.setToolTip(f"ID ракеты: {zur_id}")
                self.rockets[zur_id] = {'icon': icon, 'coords': flat_coords, 'index': 0, 'last_pos': flat_coords[0], 'current_angle': 0, 'first_appearance_step': self.current_step, 'last_processed_step': -1}
                #icon.show()
                self.map_view.scene.addItem(icon)
                x, y = flat_coords[0]
                icon.setPos(QPointF(x , y ))
                self.map_view.add_to_trail(zur_id, QPoint(x, y))
                self.rockets[zur_id]['last_pos']= (x,y)
                self.rockets[zur_id]['last_processed_step'] =self.current_step
           else:
                self.rockets[zur_id]['coords'] = flat_coords
                if self.current_step >= self.rockets[zur_id]['first_appearance_step']:
                    self.rockets[zur_id]['icon'].show()
                    coord_idx = self.current_step - self.rockets[zur_id]['first_appearance_step']
                    coord_idx = min(coord_idx, len(flat_coords) - 1)
                    x, y = flat_coords[coord_idx]
                    self.rockets[zur_id]['icon'].setPos(QPointF(x, y ))
                    self.map_view.add_to_trail(zur_id, QPoint(x, y))
                    self.rockets[zur_id]['last_pos'] = (x, y)
                    self.rockets[zur_id]['last_processed_step'] = self.current_step
    '''
    def visualize_zur_track(self, zur_id, initial_coords=None):
           if zur_id not in self.rockets:
               icon = RocketIcon("./vizualization/pictures/rocket.png")
               icon.setToolTip(f"ID ракеты: {zur_id}")
               self.rockets[zur_id] = {
                   'icon': icon,
                   'last_pos': None,
                   'current_angle': 0,
                   'first_appearance_step': next(iter(self.rockets_data[zur_id].keys())) if zur_id in self.rockets_data else self.current_step,
                   'last_processed_step': -1
               }
               self.map_view.scene.addItem(icon)
               #icon.hide()

    def update_zur_positions(self, instant_update=False):
                   #print("UPDATE", self.rockets, self.current_step)
                   """Обновляет позиции ракет на текущем шаге"""
                   for zur_id, zur_data in self.rockets.items():
                       if 'first_appearance_step' not in zur_data:
                           continue
                       if 'explosion_step' in zur_data and self.current_step >= zur_data['explosion_step']:
                           zur_data['icon'].hide()
                           continue
                       current_coords = self.get_rocket_coords_at_step(zur_id, self.current_step)
                       if current_coords is not None:
                           target_x, target_y = current_coords[0], current_coords[1]
                           zur_data['icon'].show()
                           if instant_update or zur_data.get('last_pos') is None:
                               zur_data['icon'].setPos(QPointF(target_x - 10, target_y - 10))
                               zur_data['last_pos'] = (target_x, target_y)
                               self.map_view.add_to_trail(zur_id, QPointF(target_x, target_y))
                           else:
                               if self.is_playing:
                                   self.animate_plane_movement(zur_data, target_x, target_y, zur_id)
                               else:
                                   zur_data['icon'].setPos(QPointF(target_x - 10, target_y - 10))
                                   self.map_view.add_to_trail(zur_id, QPointF(target_x, target_y))
                           self.update_rocket_rotation(zur_id, zur_data, target_x, target_y)

                           zur_data['last_processed_step'] = self.current_step
                       else:
                           zur_data['icon'].hide()

    def get_rocket_coords_at_step(self, rocket_id, step):
                               if rocket_id in self.rockets_data:
                                   for s in sorted(self.rockets_data[rocket_id].keys(), reverse=True):
                                       if s <= step:
                                           return self.rockets_data[rocket_id][s]
                               return None
    def update_rocket_rotation(self, rocket_id, rocket_data, target_x, target_y):
         #print("ROTATION", self.preserve_rotation_on_backward)
         if  self.preserve_rotation_on_backward==True:
                                if rocket_data.get('last_pos'):
                                    last_x, last_y = rocket_data['last_pos']
                                    dx = target_x - last_x
                                    dy = target_y - last_y
                                    if dx != 0 or dy != 0:
                                        angle_rad = math.atan2(dy, dx)
                                        angle_deg = math.degrees(angle_rad)
                                        rocket_data['icon'].rotate_to(((angle_deg + 90) % 360))
                                rocket_data['last_pos'] = (target_x, target_y)
         else:
             if rocket_data.get('last_pos'):
                 last_x, last_y = rocket_data['last_pos']
                 dx = target_x - last_x
                 dy = target_y - last_y
                 if dx != 0 or dy != 0:
                     angle_rad = math.atan2(dy, dx)
                     angle_deg = math.degrees(angle_rad)
                     rocket_data['icon'].rotate_to(((angle_deg - 90) % 360))
             rocket_data['last_pos'] = (target_x, target_y)

    def process_step(self, step_data):
           for msg in step_data['messages']:
                self.process_message(msg)

    def remove_radar_target(self, radar_id, plane_id):
                    """
                    Удаляет цель из списка отслеживаемых целей радара
                    :param radar_id: ID радара (как строка или число)
                    :param plane_id: ID самолета (как число)
                    """
                    # Преобразуем radar_id в строку, если ключи хранятся как строки
                    radar_key = str(radar_id)

                    if radar_key in self.tracked_targets:
                        if plane_id in self.tracked_targets[radar_key]:
                            del self.tracked_targets[radar_key][plane_id]
                            print(f"Удалена цель {plane_id} у радара {radar_id}")

                            # Если у радара больше нет целей, можно удалить и сам радар из словаря
                            if not self.tracked_targets[radar_key]:
                                del self.tracked_targets[radar_key]
                                print(f"Радар {radar_id} больше не отслеживает цели и удален из списка")

                            # Обновляем отрисовку
                            self.map_view.update()
                        else:
                            print(f"Цель {plane_id} не найдена у радара {radar_id}")
                    else:
                        print(f"Радар {radar_id} не найден в tracked_targets")

                    print("Обновленный tracked_targets:", self.tracked_targets)
    def process_message(self, msg):
           try:
                if msg['type'] == 'plane_start':
                    for plane_id, coords in msg['data'].planes.items():
                        #print(coords)
                        self.visualize_plane_track(plane_id, coords/1000)

                elif msg['type'] == 'rocket_add':
                    #print('rocket_add')
                    rocket_data = msg['data']
                    self.visualize_zur_track(rocket_data.rocket_id)
                    self.update_zur_positions()

                    #self.visualize_zur_track(rocket_data.rocket_id, rocket_data.rocket_coords)
                    #self.handle_rocket_add(msg['data'])

                elif msg['type'] == 'rocket_update':
                        self.update_zur_positions()

                        #print(msg['data'])
                        '''
                        start_x, start_y = 200, 200
                        end_x, end_y = 500, 500

                        #для теста
                        total_steps = 30
                        if self.curr < total_steps:
                                progress = self.current_step / total_steps
                                current_x = start_x + (end_x - start_x) * progress
                                current_y = start_y + (end_y - start_y) * progress
                        else:
                                current_x, current_y = end_x, end_y

                        updated_rocket_data = SimpleNamespace(
                                rocket_id=701,
                                rocket_coords=np.array([current_x, current_y])
                            )
                        updated_rocket_data_2 = SimpleNamespace(
                                    rocket_id=702,
                                    rocket_coords=np.array([current_x, current_y])
                                )
                        self.curr+=1
                        self.handle_rocket_update(updated_rocket_data)
                        self.handle_rocket_update(updated_rocket_data_2)

                        #self.handle_rocket_update( rocket_data)
                        #self.visualize_zur_track(rocket_data.rocket_id, rocket_data.rocket_coords)
                        '''

                elif msg['type'] == 'radar_tracking':
                    #print('radar_tracking')
                    radar_id = msg['data'].radar_id
                    target_id = msg['data'].target_id
                    #print('self.current_step', self.current_step)
                    #print('radar_id', radar_id)
                    #print('target_id', target_id)
                    #if radar_id not in self.tracked_targets:
                    #    self.tracked_targets[radar_id] = {}
                    self.map_view.handle_target_detection(int(radar_id), target_id, msg['data'].sector_size)
                    self.text_output.append(f"Радар {radar_id} отслеживает цель {target_id}")
                    if target_id not in self.tracked_targets[radar_id]:
                        self.tracked_targets[radar_id][target_id] = {'sector_size': msg['data'].sector_size,'last_detection': self.current_step}

                elif msg['type'] == 'radar_untracking':
                    #print("MAP", self.tracked_targets)
                    radar_id = msg['data'].radarId
                    target_id = msg['data'].targetId
                    print("UNTRACK radar_id", radar_id)
                    print("UNTRACK  target_id ", target_id)
                    #self.remove_radar_target(radar_id, target_id)
                    #self.update_radar_targets()
                    self.map_view.handle_target_untracking(radar_id, target_id)

                    #print("FROM UPTRACK", self.tracked_targets)
                    self.text_output.append(f"Радар {radar_id} прекратил отслеживание цели {target_id}")
                    #self.map_view.update()

                elif msg['type'] == 'explosion':
                            explosion_data = msg['data']
                            self.map_view.handle_target_destruction(explosion_data)
                            explosion_circle = QGraphicsEllipseItem()
                            radius = explosion_data.death_range
                            explosion_circle.setRect(explosion_data.rocket_coords[0] - radius, explosion_data.rocket_coords[1] - radius,  radius * 2,radius * 2)
                            pen = QPen(Qt.red)
                            pen.setWidth(2)
                            explosion_circle.setPen(pen)
                            brush = QBrush(QColor(255, 0, 0, 50))
                            explosion_circle.setBrush(brush)
                            self.map_view.scene.addItem(explosion_circle)

                            if explosion_data.plane_id in self.planes:
                                plane_data = self.planes[explosion_data.plane_id]
                                plane_data['pre_explosion_state'] = {
                                    'visible': plane_data['icon'].isVisible(),
                                    'pos': plane_data['icon'].pos()
                                }
                                plane_data['explosion_step'] = self.current_step
                                plane_data['icon'].hide()
                                #del self.planes[explosion_data.plane_id]  # радикально ...
                                for radar_id in self.tracked_targets:
                                     if explosion_data.plane_id in self.tracked_targets[radar_id]:
                                         del self.tracked_targets[radar_id][explosion_data.plane_id]

                            if explosion_data.rocket_id in self.rockets:
                                rocket_data = self.rockets[explosion_data.rocket_id]
                                rocket_data['pre_explosion_state'] = {
                                    'visible': rocket_data['icon'].isVisible(),
                                    'pos': rocket_data['icon'].pos()
                                }
                                #rocket_data['destroyed'] = True
                                rocket_data['explosion_step'] = self.current_step
                                rocket_data['icon'].hide()
                                #self.text_output.append(f'<span style="color: olive;">🚀 Ракета с ID {explosion_data.rocket_id} деактивирована🧨</span>')

                                #self.map_view.scene.removeItem(rocket_data['icon'])
                            #if explosion_data.rocket_id in self.rockets:
                            #            rocket_data = self.rockets[explosion_data.rocket_id]
                            #            rocket_data['icon'].hide()

                            self.text_output.append(
                                f" Взрыв ракеты {explosion_data.rocket_id}, самолета {explosion_data.plane_id}, "
                                f"координаты взрыва ({explosion_data.rocket_coords[0]:.1f}, "
                                f"{explosion_data.rocket_coords[1]:.1f}). Радиус поражения: {explosion_data.death_range}"
                            )
                            QTimer.singleShot(1000, lambda: self.map_view.scene.removeItem(explosion_circle))
                elif msg['type'] == 'rocket_inactivate':
                    rocket_id = msg['data'].rocketId
                    self.text_output.append(f'<span style="color: olive;">🚀 Ракета с ID {rocket_id} деактивирована🧨</span>')
                    if rocket_id in self.rockets:
                        rocket_data = self.rockets[rocket_id]
                        cross_label = QLabel(self)
                        cross_pixmap = QPixmap(20, 20)
                        cross_pixmap.fill(Qt.transparent)
                        painter = QPainter(cross_pixmap)
                        painter.setRenderHint(QPainter.Antialiasing)
                        pen = QPen(Qt.red, 2)
                        painter.setPen(pen)
                        painter.drawLine(0, 0, 20, 20)
                        painter.drawLine(20, 0, 0, 20)
                        painter.end()
                        cross_label.setPixmap(cross_pixmap)
                        last_pos = rocket_data.get('last_pos', (0, 0))
                        cross_label.move(last_pos[0] - 10, last_pos[1] - 10)
                        cross_label.show()
                        rocket_data['icon'].hide()
                        del self.rockets[rocket_id]
                        self.inactive_rockets[rocket_id] = cross_label
                        QTimer.singleShot(self.cross_visible_time, lambda rid=rocket_id: self.remove_cross(rid))

           except Exception as e:
                print(f"Ошибка при обработке сообщения: {e}")


    def visualize_explosion(self, rocket_id: int, rocket_coords: np.ndarray, plane_id: int, plane_coords: np.ndarray, collateral_damage: List[Tuple[int, np.ndarray]], collision_step: int):
           center_x = (rocket_coords[0] + plane_coords[0]) / 2
           center_y = (rocket_coords[1] + plane_coords[1]) / 2
           center = QPoint(int(center_x), int(center_y))
           all_points = [center]
           for _, coords in collateral_damage:
                all_points.append(QPoint(int(coords[0]), int(coords[1])))
           blast_radius = self.map_view.calculate_blast_radius(center, all_points)
           explosion_id = f"explosion_{rocket_id}_{plane_id}_{collision_step}"
           self.map_view.explosions[explosion_id] = {'center': center, 'max_radius': blast_radius, 'current_radius': 10, 'alpha': 220, 'start_step': collision_step, 'duration': 5,
                               'damage_points': [(damage_id, QPoint(int(coords[0]), int(coords[1])))for damage_id, coords in collateral_damage]}
           for damage_id, point in self.map_view.explosions[explosion_id]['damage_points']:
                   damage_marker_id = f"damage_{damage_id}_{collision_step}"
                   self.map_view.damage_markers[damage_marker_id] = {'position': point, 'alpha': 200, 'start_step': collision_step, 'duration': 5}

    '''
    def calculate_blast_radius(self, center: QPoint, all_points: List[QPoint]) -> int:
           if not all_points:
                return 50
           max_distance = 0
           for point in all_points:
                dx = point.x() - center.x()
                dy = point.y() - center.y()
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > max_distance:
                    max_distance = distance
           base_radius = 100
           scale_factor = 1.5
           radius = int(max(base_radius, max_distance * scale_factor))
           return radius
    '''
    def remove_cross(self, rocket_id):
           if rocket_id in self.inactive_rockets:
                   cross_label = self.inactive_rockets[rocket_id]
                   cross_label.hide()
                   cross_label.deleteLater()
                   del self.inactive_rockets[rocket_id]

    def handle_explosion_event(self, explosion_msg: dict):

                        plane_id = explosion_msg['plane_id']
                        if plane_id in self.planes:
                           plane_data = self.planes[plane_id]
                           if 'animation' in plane_data:
                               plane_data['animation'].stop()
                               del plane_data['animation']
                           current_pos = plane_data['icon'].pos()
                           plane_data['last_pos'] = (current_pos.x(), current_pos.y())
                           cross_label = QLabel(self.map_view)
                           cross_label.setAttribute(Qt.WA_TranslucentBackground)
                           icon_size = plane_data['icon'].original_pixmap.size()
                           #icon_size = (20,20)
                           cross_pixmap = QPixmap(icon_size)
                           cross_pixmap.fill(Qt.transparent)
                           painter = QPainter(cross_pixmap)
                           painter.setRenderHint(QPainter.Antialiasing)
                           pen = QPen(QColor(255, 0, 0), 3)
                           painter.setPen(pen)
                           margin = 5
                           painter.drawLine(margin, margin,icon_size.width()-margin, icon_size.height()-margin)
                           painter.drawLine(icon_size.width()-margin, margin, margin, icon_size.height()-margin)
                           painter.end()

                           #cross_label.setPixmap(cross_pixmap)
                           #scale_factor = 0.5
                           #point = QPoint(int(current_pos.x())*scale_factor, int(current_pos.y())*scale_factor)
                           #rect = QRect(point, icon_size)
                           #cross_label.setGeometry(rect)
                           #cross_label.setGeometry(rect)


                           scale_factor = 0.4
                           small_cross = cross_pixmap.scaled(
                               int(cross_pixmap.width() * scale_factor),
                               int(cross_pixmap.height() * scale_factor),
                               Qt.KeepAspectRatio,
                               Qt.SmoothTransformation
                           )

                           cross_label.setPixmap(small_cross)

                           icon_center_x = int(current_pos.x() + icon_size.width()/2 - small_cross.width()/2)
                           icon_center_y = int(current_pos.y() + icon_size.height()/2 - small_cross.height()/2)

                           cross_label.setGeometry(
                               icon_center_x,
                               icon_center_y,
                               small_cross.width(),
                               small_cross.height()
                           )
                           #cross_label.setGeometry(QRect(current_pos, icon_size))
                           #cross_label.show()
                           QTimer.singleShot(1000, lambda: self.process_plane_destruction(plane_id,explosion_msg['collision_step'], explosion_msg['rocket_id']))
                        self.visualize_explosion(rocket_id=explosion_msg['rocket_id'], rocket_coords=explosion_msg['rocket_coords'],
                                   plane_id=explosion_msg['plane_id'], plane_coords=explosion_msg['plane_coords'],
                                   collateral_damage=explosion_msg['collateral_damage'],collision_step=explosion_msg['collision_step'])
                        self.map_view.set_current_step(explosion_msg['collision_step'])
                        self.update()

    '''
    def handle_explosion_event(self, explosion_msg: dict):
        plane_id = explosion_msg['plane_id']
        rocket_id = explosion_msg['rocket_id']
        if plane_id in self.planes:
            self.planes[plane_id]['pre_explosion_state'] = {
                'visible': True,
                'pos': self.planes[plane_id]['icon'].pos()
            }
        if rocket_id in self.rockets:
            self.rockets[rocket_id]['pre_explosion_state'] = {
                'visible': True,
                'pos': self.rockets[rocket_id]['icon'].pos()
            }
        if plane_id in self.planes:
            plane_data = self.planes[plane_id]
            if 'animation' in plane_data:
                plane_data['animation'].stop()
                del plane_data['animation']
            current_pos = plane_data['icon'].pos()
            plane_data['last_pos'] = (current_pos.x(), current_pos.y())
            #cross_label = self.create_destruction_cross(current_pos, plane_data['icon'].original_pixmap.size())
            #cross_label.show()
            plane_data['icon'].hide()
            QTimer.singleShot(2000, lambda: self.process_plane_destruction(
                plane_id,  explosion_msg['collision_step'], rocket_id
            ))
        self.visualize_explosion(
            rocket_id=rocket_id,
            rocket_coords=explosion_msg['rocket_coords'],
            plane_id=plane_id,
            plane_coords=explosion_msg['plane_coords'],
            collateral_damage=explosion_msg['collateral_damage'],
            collision_step=explosion_msg['collision_step']
        )
        self.map_view.set_current_step(explosion_msg['collision_step'])
        self.update()
    '''
    def create_destruction_cross(self, position, icon_size):
        cross_label = QLabel(self.map_view)
        cross_label.setAttribute(Qt.WA_TranslucentBackground)

        cross_pixmap = QPixmap(icon_size)
        cross_pixmap.fill(Qt.transparent)

        painter = QPainter(cross_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        pen = QPen(QColor(255, 0, 0), 3)
        painter.setPen(pen)

        margin = 5
        painter.drawLine(margin, margin, icon_size.width()-margin, icon_size.height()-margin)
        painter.drawLine(icon_size.width()-margin, margin, margin, icon_size.height()-margin)
        painter.end()
        '''
        scale_factor = 0.4
        small_cross = cross_pixmap.scaled(
            int(cross_pixmap.width() * scale_factor),
            int(cross_pixmap.height() * scale_factor),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        cross_label.setPixmap(small_cross)
        icon_center_x = int(position.x() + icon_size.width()/2 - small_cross.width()/2)
        icon_center_y = int(position.y() + icon_size.height()/2 - small_cross.height()/2)

        cross_label.setGeometry(
            icon_center_x,
            icon_center_y,
            small_cross.width(),
            small_cross.height()
        )

        return cross_label
        '''
    def process_plane_destruction(self, plane_id: int, collision_step: int, rocket_id):
           if plane_id in self.planes:
                   self.planes[plane_id]['icon'].hide()
                   #del self.planes[plane_id]
           damage_id = f"plane_{plane_id}"
           #pos = cross_label.pos()
           #self.map_view.damage_markers[damage_id] = {'position': QPoint(pos.x() + cross_label.width()//2, pos.y() + cross_label.height()//2),'alpha': 200,'start_step': collision_step,'duration': 30}
           #QTimer.singleShot(2000, lambda: self.remove_cross_marker(cross_label, damage_id))
           target_id = plane_id
           for radar_id in list(self.tracked_targets.keys()):
                   if target_id in self.tracked_targets[radar_id]:
                       del self.tracked_targets[radar_id][target_id]
           for radar_id in list(self.map_view.tracked_targets.keys()):
                       if target_id in self.map_view.tracked_targets[radar_id]:
                           del self.map_view.tracked_targets[radar_id][target_id]

           if rocket_id in self.rockets:
                       rocket_data = self.rockets[rocket_id]
                       if 'icon' in rocket_data:
                           rocket_data['icon'].hide()
                           del self.rockets[rocket_id]
                       if 'animation' in rocket_data:
                           rocket_data['animation'].stop()

    def remove_cross_marker(self, cross_label: QLabel, damage_id: str):
           cross_label.hide()
           cross_label.deleteLater()
           if damage_id in self.map_view.damage_markers:
                   del self.map_view.damage_markers[damage_id]

#here
    def log_explosion(self, rocket_id: int, plane_id: int, collateral_damage: List[Tuple[int, np.ndarray]]):
        self.text_output.append(f'<span style="color: red; font-weight: bold;"> ВЗРЫВ! Ракета {rocket_id} сбила самолет {plane_id}</span>')
        secondary_damage = [(obj_id, pos) for obj_id, pos in collateral_damage if obj_id != plane_id]

        if secondary_damage:
             damaged_objects = ", ".join([f"#{obj_id}" for obj_id, _ in secondary_damage])
             self.text_output.append(f'<span style="color: orange;">⚠️ Вторичные повреждения: {damaged_objects}</span>')
'''
             elif msg['type'] == 'radar_untracking':
                 #self.map_view.update()
                 radar_id = msg['data'].radarId
                 target_id = msg['data'].targetId
                 self.map_view.handle_target_untracking(radar_id, target_id)
                 self.text_output.append(f"Радар {radar_id} прекратил отслеживание цели {target_id}")
'''
