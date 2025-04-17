# This Python file uses the following encoding: utf-8
from vizualization.map_window import  MapView
from vizualization.map_window import PUIcon
from vizualization.map_window import RadarIcon
from vizualization.map_window import PlaneImageIcon
from vizualization.map_window import RocketIcon
from vizualization.map_window import Icon
from typing import List, Tuple
from typing import Dict
import math
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen


class MapWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моделирование ЗРС")
        self.setGeometry(100, 100, 800, 600)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QHBoxLayout(self.central_widget)
        self.map_view = MapView()
        layout.addWidget(self.map_view, 3)
        self.showFullScreen()
        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output, 1)
        self.central_widget.setLayout(layout)
        self.text_output.append(f"Моделирование работы ЗРС")
        self.rockets = {}
        self.planes = {}

    ''' get_data: получение данных от управляющей программы или взятие данных из БД '''
    def get_data_plane(self, plane_id, coord_list):
            self.visualize_plane_track(plane_id, coord_list)
        #pass

    def get_data_radar(sector, position):
        pass

    def get_data_rocket(id, coord, zone_kill):
        pass
        #self.visualize_plane_track (id, coord)

    def visualize_plane_track(self, plane_id, coords: np.ndarray):
            self.text_output.append(f"✈️ Самолет с ID {plane_id} появился в воздушном пространстве")
            if coords is None or len(coords) == 0:
                return
            coords = np.atleast_2d(coords)
            if coords.shape[1] < 2:
                return
            #flat_coords = np.nan_to_num(coords)
            flat_coords=[]
            flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
            if plane_id not in self.planes:
                icon = PlaneImageIcon("./vizualization/pictures/airplane.webp", self)
                icon.setToolTip(f"ID самолёта: {plane_id}")
                icon.show()
                initial_angle=0
                timer = QTimer(self)
                timer.timeout.connect(lambda pid=plane_id: self.move_plane(pid))
                self.planes[plane_id] = {'icon': icon,'coords': flat_coords,'index': 0,'timer': timer, 'current_angle':initial_angle}
            else:
                self.planes[plane_id]['coords'] = flat_coords
                self.planes[plane_id]['index'] = 0
                if 'current_angle' not in self.planes[plane_id]:
                    self.planes[plane_id]['current_angle'] = 0
            x, y = flat_coords[0]
            self.planes[plane_id]['icon'].move(x-20, y-20)
            self.map_view.add_to_trail(plane_id, QPoint(x, y))
            self.planes[plane_id]['timer'].start(500)

    def move_plane(self, plane_id):
                plane_data = self.planes.get(plane_id)
                if not plane_data:
                    return
                coords = plane_data['coords']
                index = plane_data['index']
                correct_angle=plane_data['current_angle']

                if index < len(coords):
                    x, y = coords[index]
                    icon = plane_data['icon']
                    icon.move(x-20, y-20)
                    correct_angle=plane_data.get('current_angle', 0)
                    if index > 0:
                        prev_x, prev_y = coords[index - 1]
                        dx = x - prev_x
                        dy = y - prev_y
                        if dx!=0 or dy!=0:
                            angle_rad = math.atan2(dy, dx)
                            angle_deg = math.degrees(angle_rad)
                            #mov_angle=math.degrees(math.atan2(dx,-dy))
                            correct_angle=(angle_deg +90) % 360
                            if abs(correct_angle - plane_data['current_angle']) > 1:
                                        icon.rotate_to(correct_angle)
                                        plane_data['current_angle'] = correct_angle

                    self.map_view.add_to_trail(plane_id, QPoint(x, y))
                    plane_data['index'] += 1
                    self.map_view.update()
                else:
                    plane_data['timer'].stop()

    def visualize_zur_track(self, zur_id, coords: np.ndarray, detection_area=None):
        self.text_output.append(f'<span style="color: blue;">• Ракета с ID {zur_id} появилася в воздушном пространстве</span>')
        #self.text_output.append(f" Ракета  с ID {zur_id} появилася в воздушном пространстве")
        if coords is None or len(coords) == 0:
           return
        coords = np.atleast_2d(coords)
        if coords.shape[1] < 2:
               return
        flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]
        if zur_id not in self.rockets:
           icon = RocketIcon("./vizualization/pictures/rocket.png", self)
           icon.setToolTip(f"ID ракеты: {zur_id}")
           icon.show()
           timer = QTimer(self)
           timer.timeout.connect(lambda zid=zur_id: self.move_zur(zid))
           self.rockets[zur_id] = {'icon': icon, 'coords': coords, 'index': 0, 'timer': timer}
        else:
           self.rockets[zur_id]['coords'] = flat_coords
           self.rockets[zur_id]['index'] = 0
        x, y = flat_coords[0]
        self.rockets[zur_id]['icon'].move(x, y)
        self.map_view.add_to_trail(zur_id, QPoint(x, y))
        self.rockets[zur_id]['timer'].start(1500)



    def move_zur(self, zur_id):
           zur_data = self.rockets.get(zur_id)
           if not zur_data:
            return
           coords = zur_data['coords']
           index = zur_data['index']
           if index < len(coords):
                x, y,z = coords[index]
                icon = zur_data['icon']
                x = int(x)
                y = int(y)
                icon.move(x, y)
                if index > 0:
                    prev_x, prev_y,z = coords[index - 1]
                    dx = x - prev_x
                    dy = y - prev_y
                    angle_rad = math.atan2(dx, -dy)
                    angle_deg = math.degrees(angle_rad)
                    zur_data['icon'].rotate_to(angle_deg)
                self.map_view.add_to_trail(zur_id, QPoint(x, y))
                zur_data['index'] += 1
                self.map_view.update()
           else:
                zur_data['timer'].stop()

    def visualize_rls(self, target_id, angle,  dist):
        self.text_output.append(f"Старт работы радиолокатора")
        self.text_output.append(f"Угол обзора (азимут, °): {angle}")
        self.text_output.append(f"Дальность действия, км : {dist}")
        self.map_view.visualize_rls(target_id, angle,  dist)


    def handle_explosion_event(self, rocket_id: int, rocket_coords: np.ndarray, plane_id: int, plane_coords: np.ndarray,collateral_damage: List[Tuple[int, np.ndarray]]):
        self.remove_object(rocket_id)
        self.remove_object(plane_id)
        self.map_view.add_blast_effect(rocket_id, rocket_coords, plane_id, plane_coords, collateral_damage)
        self.log_explosion(rocket_id, plane_id, collateral_damage)


    def remove_object(self, obj_id: int):
        if obj_id in self.rockets:
            self.rockets[obj_id]['icon'].hide()
            self.rockets[obj_id]['timer'].stop()
            del self.rockets[obj_id]
        elif obj_id in self.planes:
            self.planes[obj_id]['icon'].hide()
            self.planes[obj_id]['timer'].stop()
            del self.planes[obj_id]

    def log_explosion(self, rocket_id: int, plane_id: int, collateral_damage: List[Tuple[int, np.ndarray]]):
        self.text_output.append(f'<span style="color: red; font-weight: bold;"> ВЗРЫВ! Ракета {rocket_id} сбила самолет {plane_id}</span>')
        if collateral_damage:
            damaged_objects = ", ".join([f"#{obj_id}" for obj_id, _ in collateral_damage])
            self.text_output.append(f'<span style="color: orange;">⚠️ Вторичные повреждения: {damaged_objects}</span>')
