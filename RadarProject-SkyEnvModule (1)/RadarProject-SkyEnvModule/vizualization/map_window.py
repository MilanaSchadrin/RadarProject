import math
import numpy as np
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
        #положения задать корректно; считать значения из бд
        self.radar = RadarIcon('./vizualization/pictures/radar.png', 250, 450, parent=self)
        self.pu_image = PUIcon('./vizualization/pictures/pu.png', 650, 450, parent=self)

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

    def add_to_trail(self, obj_id, point):
                """Добавляет точку в трек объекта"""
                if obj_id not in self.trails:
                    self.trails[obj_id] = []
                self.trails[obj_id].append(QPoint(point))

                # Ограничиваем длину трека
                if len(self.trails[obj_id]) > 100:
                    self.trails[obj_id] = self.trails[obj_id][-100:]

                self.update()

    def visualize_rls(self, target_id, angle=None, dist=None):
                """Добавляет цель для отслеживания РЛС"""
                if angle is not None:
                    self.view_angle = angle
                if dist is not None:
                    self.rls_radius = dist

                if target_id not in self.tracked_targets:
                    self.tracked_targets[target_id] = 0
                    self.update()

    def update_scan(self):
                """Обновляет угол сканирования"""
                self.scan_angle = (self.scan_angle + 10) % 360
                self.update()

    def update_targets_azimuth(self):
                """Обновляет направления на все отслеживаемые цели"""
                radar_center = QPoint(
                    self.radar.x_pos + self.radar.width()//2,
                    self.radar.y_pos + self.radar.height()//2
                )

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
                for trail in self.trails.values():
                    for i in range(1, len(trail)):
                        painter.drawLine(trail[i-1], trail[i])

                radar_center = QPoint(
                    self.radar.x_pos + self.radar.width()//2,
                    self.radar.y_pos + self.radar.height()//2
                )
                painter.setBrush(QBrush(QColor(0, 255, 0, 30)))
                painter.setPen(QPen(QColor(0, 180, 0), 2))

                scan_rect = QRectF(
                    radar_center.x() - self.rls_radius,
                    radar_center.y() - self.rls_radius,
                    self.rls_radius * 2,
                    self.rls_radius * 2
                )
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
            flat_coords = np.nan_to_num(coords)
            flat_coords = [(int(x), int(y)) for x, y in flat_coords[:, :2]]

            if plane_id not in self.planes:
                icon = PlaneImageIcon("./vizualization/pictures/airplane.webp", self)
                icon.setToolTip(f"ID самолёта: {plane_id}")
                icon.show()
                initial_angle=0
                timer = QTimer(self)
                timer.timeout.connect(lambda pid=plane_id: self.move_plane(pid))
                self.planes[plane_id] = {
                    'icon': icon,
                    'coords': flat_coords,
                    'index': 0,
                    'timer': timer,
                    'current_angle':initial_angle
                }
            else:
                self.planes[plane_id]['coords'] = flat_coords
                self.planes[plane_id]['index'] = 0
                if 'current_angle' not in self.planes[plane_id]:
                    self.planes[plane_id]['current_angle'] = 0

            x, y = flat_coords[0]
            self.planes[plane_id]['icon'].move(x-20, y-20)
            self.map_view.add_to_trail(plane_id, QPoint(x, y))
            self.planes[plane_id]['timer'].start(1000)

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
                        if dx!=0 and dy!=0:
                            angle_rad = math.atan2(dy, dx)
                            angle_deg = math.degrees(angle_rad)
                            mov_angle=math.degrees(math.atan2(-dy,dx))
                            correct_angle=(-mov_angle+90)%360
                            if abs(correct_angle - plane_data['current_angle']) > 1:
                                        icon.rotate_to(correct_angle)
                                        plane_data['current_angle'] = correct_angle

                    self.map_view.add_to_trail(plane_id, QPoint(x, y))
                    plane_data['index'] += 1
                    self.map_view.update()
                else:
                    plane_data['timer'].stop()
    '''
    def visualize_zur_track(self, zur_id, rocket_coords, detection_area=None):
                        """Визуализирует траекторию ракеты с анимацией движения"""
                        if rocket_coords is None or len(rocket_coords) == 0:
                            return

                        # Преобразуем координаты в 2D массив (N,3)
                        rocket_coords = np.atleast_2d(rocket_coords)
                        if rocket_coords.shape[1] < 3:
                            return

                        # Конвертируем координаты в целые числа для отображения
                        flat_coords = [(int(x), int(y)) for x, y in rocket_coords[:, :2]]

                        if zur_id not in self.rockets:
                            # Создаем иконку ракеты
                            icon = RocketIcon("./vizualization/pictures/rocket.png", self)
                            icon.setToolTip(f"Ракета ID: {zur_id}")
                            icon.show()

                            # Создаем таймер для анимации движения
                            timer = QTimer(self)
                            timer.timeout.connect(lambda zid=zur_id: self.move_zur(zid))

                            # Сохраняем данные ракеты
                            self.rockets[zur_id] = {
                                'icon': icon,
                                'coords': rocket_coords,
                                'index': 0,
                                'timer': timer
                            }

                            # Устанавливаем начальную позицию
                            x, y = flat_coords[0]
                            icon.move(x, y)

                            # Добавляем первую точку в траекторию
                            self.map_view.add_to_trail(zur_id, QPoint(x, y))

                            # Запускаем таймер с интервалом 50 мс для плавной анимации
                            timer.start(50)
                        else:
                            # Обновляем координаты существующей ракеты
                            self.rockets[zur_id]['coords'] = rocket_coords
                            self.rockets[zur_id]['index'] = 0
    def move_zur(self, zur_id):
                                   zur_data = self.rockets.get(zur_id)
                                   if not zur_data:
                                    return
                                   coords = zur_data['coords']
                                   index = zur_data['index']
                                   if index < len(coords):
                                        x, y, z = coords[index]
                                        icon = zur_data['icon']
                                        x = int(x)
                                        y = int(y)
                                        icon.move(x, y)
                                        if index > 0:
                                            prev_x, prev_y, z = coords[index - 1]
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
                                        #функция для взрыва...
    '''
    def visualize_zur_track(self, zur_id, coords: np.ndarray, detection_area=None):
        self.text_output.append(f" Ракета  с ID {zur_id} появилася в воздушном пространстве")
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
                x, y, z = coords[index]
                icon = zur_data['icon']
                x = int(x)
                y = int(y)
                icon.move(x, y)
                if index > 0:
                    prev_x, prev_y, z = coords[index - 1]
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
        #self.rls_sector = rls_sector
        #self.rls_radius = dist
        #self.update()

'''
        class MapView(QFrame):
            def __init__(self):
                super().__init__()
                self.setStyleSheet("background-color: white;")
                #в качестве примера
                self.trails = {} #{id :(points)}
                self.background_image = QPixmap('./vizualization/pictures/background.png')
                #background.png 325328457001211.png

                #в качестве примера
                #тут значения должны передаваться из бд....
                self.radar = RadarIcon('./vizualization/pictures/radar.png', 250, 450, parent=self)
                self.pu_image = PUIcon('./vizualization/pictures/pu.png', 650, 450, parent=self)
                #self.radar_x = 250
                #self.radar_y = 450
                #self.radius = 200

                self.rls_radius = None
                self.follow_target_id = None
                self.rls_angle = None
                self.update_timer = QTimer()
                self.update_timer.timeout.connect(self.update)
                self.update_timer.start(100)
            def visualize_rls(self, target_id, angle,  dist):
                self.follow_target_id = target_id
                self.view_angle = angle
                self.rls_radius =dist
                #self.update()

            def add_to_trail(self, obj_id, point):
                if obj_id not in self.trails:
                    self.trails[obj_id] = []
                self.trails[obj_id].append(point)
                self.update()

            def paintEvent(self, event):
                 painter = QPainter(self)
                 if not self.background_image.isNull():
                    painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
                 #отрисовка траекторий всех самолетов
                 for trail in self.trails.values():
                     painter.setPen(QColor(0, 0, 255))
                     for i in range(1, len(trail)):
                        painter.drawLine(trail[i - 1], trail[i])
                     painter.setBrush(QBrush(QColor(173, 216, 230, 0)))
                     painter.setPen(QPen(QColor(81, 121, 94), 2))
                     #painter.drawEllipse(self.radar_x + self.radar.width() / 2 - self.radius, self.radar_y + self.radar.height() / 2 - self.radius, self.radius * 2, self.radius * 2)

                 if self.follow_target_id and self.rls_radius:
                         trail = self.trails.get(self.follow_target_id)
                         if trail and len(trail) > 0:
                             target_point = trail[-1]
                             radar_cx = self.radar.x_pos + self.radar.width() // 2
                             radar_cy = self.radar.y_pos + self.radar.height() // 2

                             dx = target_point.x() - radar_cx
                             dy = radar_cy - target_point.y()  # инверсия Y (в PyQt вниз — положительно)

                             azimuth = (np.degrees(np.arctan2(dy, dx)) + 360) % 360

                             start_angle = -(azimuth - self.view_angle / 2) * 16
                             span_angle = -self.view_angle * 16

                             painter.setBrush(QBrush(QColor(0, 255, 0, 60)))
                             painter.setPen(QPen(QColor(0, 128, 0), 2))

                             rect = QRectF(radar_cx - self.rls_radius,
                                           radar_cy - self.rls_radius,
                                           self.rls_radius * 2,
                                           self.rls_radius * 2)

                             painter.drawPie(rect, int(start_angle), int(span_angle))
'''
