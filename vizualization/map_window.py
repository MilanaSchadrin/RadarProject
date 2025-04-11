import math
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint
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
        #в качестве примера
        self.trails = {}
        self.background_image = QPixmap('C:/Users/milan/Documents/Uni/Python/RadarProject/vizualization/pictures/background.png')
        #background.png 325328457001211.png

        #в качестве примера

        self.radar = RadarIcon('radar.png', 250, 450, parent=self)
        self.pu_image = PUIcon('pu.png', 650, 450, parent=self)
        self.radar_x = 250
        self.radar_y = 450
        self.radius = 200

    def add_to_trail(self, plane_id, point):
        if plane_id not in self.trails:
            self.trails[plane_id] = []
        self.trails[plane_id].append(point)
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
             painter.drawEllipse(self.radar_x + self.radar.width() / 2 - self.radius, self.radar_y + self.radar.height() / 2 - self.radius, self.radius * 2, self.radius * 2)

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

            
            flat_coords = [(int(x), int(y)) for x, y in coords[:, :2]]

            if plane_id not in self.planes:
                icon = PlaneImageIcon("C:/Users/milan/Documents/Uni/Python/RadarProject/vizualization/pictures/airplane.webp", self)
                icon.setToolTip(f"ID самолёта: {plane_id}")
                icon.show()
                timer = QTimer(self)
                timer.timeout.connect(lambda pid=plane_id: self.move_plane(pid))
                self.planes[plane_id] = {
                    'icon': icon,
                    'coords': flat_coords,
                    'index': 0,
                    'timer': timer
                }
            else:
                self.planes[plane_id]['coords'] = flat_coords
                self.planes[plane_id]['index'] = 0

            x, y = flat_coords[0]
            self.planes[plane_id]['icon'].move(x, y)
            self.map_view.add_to_trail(plane_id, QPoint(x, y))
            self.planes[plane_id]['timer'].start(1000)

    def move_plane(self, plane_id):
                plane_data = self.planes.get(plane_id)
                if not plane_data:
                    return

                coords = plane_data['coords']
                index = plane_data['index']

                if index < len(coords):
                    x, y = coords[index]
                    icon = plane_data['icon']
                    icon.move(x, y)

                    if index > 0:
                        prev_x, prev_y = coords[index - 1]
                        dx = x - prev_x
                        dy = y - prev_y
                        angle_rad = math.atan2(dx, -dy)
                        angle_deg = math.degrees(angle_rad)
                        icon.rotate_to(angle_deg)

                    self.map_view.add_to_trail(plane_id, QPoint(x, y))
                    plane_data['index'] += 1
                    self.map_view.update()
                else:
                    plane_data['timer'].stop()

    def visualize_zur_track(self, zur_id, coords, detection_area=None):
        self.text_output.append(f"Запуск ЗУР с идентификатором: {zur_id}")
        if not coords:
           return
        if zur_id not in self.rockets:
           icon = RocketIcon("C:/Users/milan/Documents/Uni/Python/RadarProject/vizualization/pictures/rocket.png", self)
           icon.setToolTip(f"ID ракеты: {zur_id}")
           icon.show()
           timer = QTimer(self)
           timer.timeout.connect(lambda zid=zur_id: self.move_zur(zid))
           self.rockets[zur_id] = {'icon': icon, 'coords': coords, 'index': 0, 'timer': timer}
        else:
           self.rockets[zur_id]['coords'] = coords
           self.rockets[zur_id]['index'] = 0
        x, y = coords[0]
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
                x, y = coords[index]
                zur_data['icon'].move(x, y)
                if index > 0:
                    prev_x, prev_y = coords[index - 1]
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


    def visualize_rls_sector(self, rls_sector, dist):
        self.text_output.append(f"Старт работы радиолокатора")
        self.text_output.append(f"Угол обзора (азимут, °): {rls_sector}")
        self.text_output.append(f"Дальность действия, км : {dist}")

