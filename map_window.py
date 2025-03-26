from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QTextEdit, QLabel, QFrame
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen
from PyQt5.QtWidgets import QApplication

class MapView(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("background-color: white;")
        self.trail = []

        #в качестве примера
        self.radar_image = QPixmap('./i.webp')
        self.radar_label = QLabel(self)
        self.radar_label.setPixmap(self.radar_image)
        self.radar_label.setScaledContents(True)
        self.radar_label.setFixedSize(70, 70)
        self.radar_x = 250
        self.radar_y = 450
        self.radar_label.move(self.radar_x, self.radar_y)
        self.radius = 200

    def add_to_trail(self, point):
        self.trail.append(point)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(0, 0, 255))

        for i in range(1, len(self.trail)):
            painter.drawLine(self.trail[i - 1], self.trail[i])

        painter.setBrush(QBrush(QColor(173, 216, 230, 0)))
        painter.setPen(QPen(QColor(0, 255, 0), 2))
        circle_center = (self.radar_x + self.radar_label.width() / 2, self.radar_y + self.radar_label.height() / 2)
        painter.drawEllipse(self.radar_x + self.radar_label.width() / 2  - self.radius, self.radar_y + self.radar_label.height() / 2 - self.radius, self.radius * 2, self.radius * 2)


class PlaneIcon(QLabel):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setText("✈")
            self.setStyleSheet("font-size: 20px;")
            self.setAlignment(Qt.AlignCenter)
            self.setGeometry(0, 0, 50, 50)

            '''
            добавление картинки самолета, чтобы нос самолета был направлен по ходу движения
            self.plane_pixmap = QPixmap(50, 50)
            self.plane_pixmap.fill(Qt.transparent)
            painter = QPainter(self.plane_pixmap)
            painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.black)  # Цвет самолета
            painter.drawPolygon([QPoint(25, 0), QPoint(50, 25), QPoint(25, 50), QPoint(0, 25)])
            painter.end()

            self.plane_label = QLabel(self)
            self.plane_label.setPixmap(self.plane_pixmap)
            self.plane_label.setAlignment(Qt.AlignCenter)
            '''

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

        self.text_output = QTextEdit(self)
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output, 1)
        self.central_widget.setLayout(layout)

        self.plane_label = PlaneIcon(self)

        self.coordinates = []
        self.current_index = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.move_plane)

    ''' get_data: получение данных от управляющей программы или взятие данных из БД '''
    def get_data_plane(self, id, coord):
        self.visualize_plane_track (id, coord)
        #pass

    def get_data_radar(sector, position):
        pass

    def get_data_rocket(id, coord, zone_kill):
        pass

    def visualize_plane_track(self, plane_id, coords):
        self.coordinates = coords
        self.current_index = 0
        if coords:
           x, y = coords[0]
           self.plane_label.move(x, y)
           self.map_view.add_to_trail(QPoint(x, y))
           self.plane_label.setToolTip(f"ID самолета: {plane_id}")
           self.timer.start(1000)


    def visualize_rls_sector(self, rls_sector, dist):
        self.text_output.append(f"Старт работы радиолокатора")
        self.text_output.append(f"Угол обзора (азимут, °): {rls_sector}")
        self.text_output.append(f"Дальность действия, км : {dist}")

        #визуализация сектора обзора радиолокатора в виде круга
        '''
        self.radar_image = QPixmap('/home/astra/Desktop/i.webp')
        self.radar_label = QLabel(self)
        self.radar_label.setPixmap(self.radar_image)
        self.radar_label.setScaledContents(True)
        self.radar_label.setFixedSize(70, 70)
        self.radar_x = 150
        self.radar_y = 450
        self.radar_label.move(self.radar_x, self.radar_y)
        self.radius = 100
        '''

    def visualize_zur_track(self, zur_id, coord, detection_area):
        self.text_output.append(f"ЗУР: запуск зур {zur_id}")

    def move_plane(self):
            if self.current_index < len(self.coordinates):
                  x, y = self.coordinates[self.current_index]
                  self.map_view.add_to_trail(QPoint(x, y))
                  self.plane_label.move(x, y)
                  self.current_index += 1
                  self.map_view.update()
            else:
                  self.timer.stop()
