import math
import time
import numpy as np
from typing import List, Tuple
from typing import Dict
from PyQt5.QtWidgets import QMainWindow,QGraphicsObject, QWidget, QHBoxLayout, QTextEdit, QLabel,QGraphicsPixmapItem, QFrame, QGraphicsView, QGraphicsScene, QGraphicsEllipseItem, QGraphicsLineItem
from PyQt5.QtCore import Qt, QTimer, QPoint, QRectF, QPointF
from PyQt5.QtGui import QPainter, QColor, QPixmap, QBrush, QColor, QPen, QConicalGradient
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QTransform, QFont
class GraphicsIcon(QGraphicsPixmapItem, QGraphicsObject):
    def __init__(self, image_path, size=(20, 20), parent=None):
        QGraphicsPixmapItem.__init__(self, parent)
        QGraphicsObject.__init__(self)
        self.original_pixmap = QPixmap(image_path)
        self._size=size
        self._angle = 0
        scaled_pixmap = self.original_pixmap.scaled(*self._size,
                                                   Qt.KeepAspectRatio,
                                                   Qt.SmoothTransformation)
        super().__init__(scaled_pixmap)
        self.setTransformationMode(Qt.SmoothTransformation)


    def pos(self) -> QPointF:
        return super().pos()

    def setPos(self, pos: QPointF):
        super().setPos(pos)
    def update_pixmap(self):
            scaled = self.original_pixmap.scaled(*self._size,
                                               Qt.KeepAspectRatio,
                                               Qt.SmoothTransformation)
            transform = QTransform()
            transform.rotate(self._angle)
            rotated = scaled.transformed(transform, Qt.SmoothTransformation)
            self.setPixmap(rotated)
            self.setOffset(-rotated.width()/2, -rotated.height()/2)  # Центрирование

    def rotate_to(self, angle_degrees):
            self._angle = angle_degrees
            self.update_pixmap()
    def boundingRect(self) -> QRectF:
                    return QGraphicsPixmapItem.boundingRect(self)

    def paint(self, painter, option, widget=None):
                    QGraphicsPixmapItem.paint(self, painter, option, widget)

class RocketIcon(GraphicsIcon):
    def __init__(self, image_path, parent=None):
        pixmap = QPixmap(image_path)
        super().__init__(pixmap, size=(30,30), parent=parent)

        #self.setScale(30,30)

class PlaneImageIcon(GraphicsIcon):
    def __init__(self, image_path,  parent=None):
        pixmap = QPixmap(image_path)
        super().__init__(pixmap, size=(20,20), parent=parent)
        #self.setScale(20, 20)



class MapView(QGraphicsView):
    def __init__(self, db_manager):
        super().__init__()
        #сцена
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setStyleSheet("background-color: white;")

        self.trails = {}  # {id: [points]}
        self.background_image = QPixmap('./vizualization/pictures/background.png')
        self.pu_image = []
        self.cc_icon = None
        #положения рлс, пу -  считать значения из бд;
        #self.radar = RadarIcon('./vizualization/pictures/radar.png', 250, 450, parent=self)
        #self.pu_image = PUIcon('./vizualization/pictures/pu.png', 650, 450, parent=self)
        #обработка коллизий
        self.explosions = {}
        self.damage_markers = {}
        self.explosion_clouds = {}
        self.visible_objects={}
        #РЛС
        self.tracked_targets = {}
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
        self.radar = {} #{radar_id:{'icon': RadarIcon, 'radius': int, 'view_angle':int}}
        self.db_manager = db_manager
        self.load_radars_from_db()
        self.load_and_draw_launchers()
        self.load_and_draw_cc()

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        old_pos = self.mapToScene(event.pos())
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
             zoom_factor = zoom_out_factor
        current_scale = self.transform().m11()

        new_scale = current_scale * zoom_factor
        if new_scale < 0.1 or new_scale > 10:
             return

        old_pos = self.mapToScene(event.pos())

        self.scale(zoom_factor, zoom_factor)

        new_pos = self.mapToScene(event.pos())

        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())

    def load_radars_from_db(self):
            if self.db_manager:
                radars_data = self.db_manager.load_radars()
                for radar_id, radar in radars_data.items():
                    self.add_radar(radar_id, x=radar['position'][0], y=radar['position'][1], radius=radar['range_input'],view_angle=radar['angle_input'])

    def add_radar(self, radar_id, x, y, radius, view_angle):
        radar_pixmap = QPixmap('./vizualization/pictures/radar.png').scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        radar_item = QGraphicsPixmapItem(radar_pixmap)
        radar_item.setOffset(-radar_pixmap.width()/2, -radar_pixmap.height()/2)
        radar_item.setPos(x,y)
        radar_item.setTransformationMode(Qt.SmoothTransformation)
        radar_item.setZValue(10)
        radar_item.setToolTip(f"ID: {radar_id}\n"
                               f"Дальность: {radius} км \n")
        self.scene.addItem(radar_item)
        self.radar[radar_id] = {
                        'item': radar_item,
                        'icon': radar_item,
                        'radius': radius,
                        'view_angle': view_angle,
                        'scan_angle': 0,
                        'x': x,
                        'y': y
                    }


    def load_and_draw_launchers(self):
            launchers = self.db_manager.load_launchers()
            for launcher_id, launcher_data in launchers.items():
                x, y = launcher_data['position'][0], launcher_data['position'][1]
                pu_pixmap = QPixmap('./vizualization/pictures/pu.png').scaled(70, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                pu_item = QGraphicsPixmapItem(pu_pixmap)
                pu_item.setPos(x - pu_pixmap.width()/2, y - pu_pixmap.height()/2)
                pu_item.setZValue(10)
                self.scene.addItem(pu_item)
                self.pu_image.append(pu_item)

    def load_and_draw_cc(self):
            cc_data = self.db_manager.load_cc()
            if cc_data:
                first_cc = next(iter(cc_data.values()))
                x, y = first_cc['position'][0],  first_cc['position'][1]
                cc_pixmap = QPixmap('./vizualization/pictures/pbu.png').scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.cc_icon = QGraphicsPixmapItem(cc_pixmap)
                self.cc_icon.setPos(x - cc_pixmap.width()/2, y - cc_pixmap.height()/2)
                self.cc_icon.setZValue(10)
                self.scene.addItem(self.cc_icon)
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
        super().paintEvent(event)
        painter = QPainter(self.viewport())
        if not painter.isActive():
            return
        painter.setRenderHint(QPainter.Antialiasing)
        self.draw_scale(painter)
        #if not self.background_image.isNull():
            # painter.drawPixmap(0, 0, self.width(), self.height(), self.background_image)
        self.draw_radar_sector(painter)

        for exp_id, explosion in self.explosions.items():
                steps_passed = self.current_step - explosion['start_step']
                if 0 <= steps_passed < explosion['duration']:
                    progress = steps_passed / explosion['duration']
                    current_radius = int(explosion['current_radius'] +(explosion['max_radius'] - explosion['current_radius']) * progress)
                    alpha = int(explosion['alpha'] * (1 - progress * 0.7))
                    core_color = QColor(255, 140, 0, alpha)
                    painter.setPen(QPen(core_color, 2))
                    painter.setBrush(QBrush(core_color))
                    painter.drawEllipse(explosion['center'], current_radius, current_radius)
                    if progress < 0.7:
                        wave_alpha = int(alpha * 0.6)
                        wave_color = QColor(255, 80, 0, wave_alpha)
                        painter.setPen(QPen(wave_color, 1))
                        painter.setBrush(Qt.NoBrush)
                        wave_radius = int(current_radius * 1.3)
                        painter.drawEllipse(explosion['center'], wave_radius, wave_radius)
        for dmg_id, marker in self.damage_markers.items():
                steps_passed = self.current_step - marker['start_step']
                if 0 <= steps_passed < marker['duration']:
                    progress = steps_passed / marker['duration']
                    alpha = int(marker['alpha'] * (1 - progress))
                    size = 8 + int(10 * (1 - progress))
                    dmg_color = QColor(255, 50, 0, alpha)
                    painter.setPen(QPen(dmg_color, 2))
                    pos = marker['position']
                    painter.drawLine(pos.x()-size, pos.y()-size, pos.x()+size, pos.y()+size)
                    painter.drawLine(pos.x()+size, pos.y()-size, pos.x()-size, pos.y()+size)

    def draw_scale(self, painter):
                           painter.save()
                           rect = self.mapToScene(self.viewport().rect()).boundingRect()
                           left = int(rect.left())
                           right = int(rect.right())
                           top = int(rect.top())
                           bottom = int(rect.bottom())
                           painter.setPen(QPen(self.grid_color, 1, Qt.DashLine))
                           start_x = (left // self.grid_step) * self.grid_step
                           start_y = (top // self.grid_step) * self.grid_step
                           for x in range(start_x, right, self.grid_step):
                               point = self.mapFromScene(QPointF(x, 0))
                               sx = point.x()
                               painter.drawLine(sx, 0, sx, self.height())
                           for y in range(start_y, bottom, self.grid_step):
                               point = self.mapFromScene(QPointF(0, y))
                               sy = point.y()
                               painter.drawLine(0, sy, self.width(), sy)
                           painter.setPen(QPen(self.axis_color, self.axis_width))
                           origin_screen = self.mapFromScene(QPointF(0, 0))
                           ox, oy = origin_screen.x(), origin_screen.y()

                           painter.drawLine(0, oy, self.width(), oy)  # X-axis
                           painter.drawLine(ox, 0, ox, self.height())  # Y-axis

                           arrow_size = 10
                           painter.drawLine(self.width() - arrow_size, oy - arrow_size//2, self.width(), oy)
                           painter.drawLine(self.width() - arrow_size, oy + arrow_size//2, self.width(), oy)

                           painter.drawLine(ox - arrow_size//2, arrow_size, ox, 0)
                           painter.drawLine(ox + arrow_size//2, arrow_size, ox, 0)

                           painter.setFont(self.font)
                           for x in range(start_x, right, self.grid_step):
                               point = self.mapFromScene(QPointF(x, 0))
                               sx = point.x()
                               if 0 <= sx <= self.width():
                                   painter.drawText(sx + 2, oy - 5, f"{x}")

                           for y in range(start_y, bottom, self.grid_step):
                               point = self.mapFromScene(QPointF(0, y))
                               sy = point.y()
                               if 0 <= sy <= self.height():
                                   painter.drawText(ox + 5, sy - 2, f"{y}")
                           painter.restore()
    '''
    def update_radar_targets(self, targets):
                               for radar_id, radar_data in self.radar.items():
                                   radar_icon = radar_data['icon']
                                   radar_center = radar_icon.scenePos()

                                   if radar_id not in self.tracked_targets:
                                       self.tracked_targets[radar_id] = {}

                                   for target_id, (x, y) in targets.items():
                                       if target_id not in self.planes:
                                           continue

                                       self.trails[target_id].append(QPoint(x, y))
                                       if len(self.trails[target_id]) > 50:
                                           self.trails[target_id] = self.trails[target_id][-50:]

                                       dx = x - radar_center.x()
                                       dy = radar_center.y() - y
                                       azimuth = math.degrees(math.atan2(dy, dx)) % 360
                                       distance = math.sqrt(dx*dx + dy*dy)

                                       if isinstance(self.tracked_targets[radar_id][target_id], (int, float)):
                                           self.tracked_targets[radar_id][target_id] = {
                                               'azimuth': self.tracked_targets[radar_id][target_id],
                                               'distance': distance
                                           }
                                       else:
                                           self.tracked_targets[radar_id][target_id]['azimuth'] = azimuth
                                           self.tracked_targets[radar_id][target_id]['distance'] = distance
                               self.update()
    '''
    def update_radar_targets(self, targets):
        for radar_id, radar_data in self.radar.items():
            radar_icon = radar_data['icon']
            radar_center = radar_icon.scenePos()

            # Не создаем пустой словарь, если радара нет в tracked_targets
            if radar_id not in self.tracked_targets:
                continue

            for target_id, (x, y) in targets.items():
                # Пропускаем, если цель не в planes или не отслеживается этим радаром
                if target_id not in self.planes or target_id not in self.tracked_targets[radar_id]:
                    continue

                self.trails[target_id].append(QPoint(x, y))
                dx = x - radar_center.x()
                dy = radar_center.y() - y
                azimuth = math.degrees(math.atan2(dy, dx)) % 360
                distance = math.sqrt(dx*dx + dy*dy)

                if isinstance(self.tracked_targets[radar_id][target_id], (int, float)):
                    self.tracked_targets[radar_id][target_id] = {
                        'azimuth': self.tracked_targets[radar_id][target_id],
                        'distance': distance
                    }
                else:
                    self.tracked_targets[radar_id][target_id]['azimuth'] = azimuth
                    self.tracked_targets[radar_id][target_id]['distance'] = distance

        #self.update()

    def draw_radar_sector(self, painter):
        scan_angle = (self.current_step * 10) % 360
        for radar_id, radar_data in self.radar.items():
            transform = self.transform()
            scale = transform.m11()
            viewport_radius = radar_data['radius'] * scale
            radar_icon = radar_data['icon']
            center = radar_icon.scenePos()
            viewport_center = self.mapFromScene(center)
            painter.setPen(QPen(QColor(0, 255, 0, 100), 1))
            painter.setBrush(QBrush(QColor(0, 255, 0, 20)))
            painter.drawEllipse(viewport_center, viewport_radius, viewport_radius)


            #self.map_view.scene.addItem(self.radar[radar_id]['icon']

            scene_radius = radar_data['radius']

            top_left = self.mapFromScene(center + QPointF(-scene_radius, -scene_radius))
            bottom_right = self.mapFromScene(center + QPointF(scene_radius, scene_radius))

            scan_rect = QRectF(top_left, bottom_right)
            start_angle = -(scan_angle - radar_data['view_angle'] / 2) * 16
            span_angle = -radar_data['view_angle'] * 16

            #painter.setPen(QPen(QColor(0, 255, 0, 100), 1))
            #painter.setBrush(QBrush(QColor(0, 255, 0, 20)))
            #painter.drawEllipse(viewport_center, scene_radius, scene_radius)

            #green =QColor(144,238, 144, 150)
            #painter.setBrush(QBrush(green))
            #painter.setPen(Qt.NoPen)
            #painter.drawPie(scan_rect, int(start_angle), int(span_angle))
            #painter.drawPie(scan_rect, int(start_angle), int(span_angle))
            #painter.drawPie(scan_rect, int(start_angle), int(span_angle))
            #dash_pen = QPen(QColor(255, 0, 0), 2, Qt.DashLine)
            #dash_pen.setDashPattern([4, 4])
            #print("SELF>TRACKED", self.tracked_targets)
            if radar_id in self.tracked_targets:
                for target_id in list(self.tracked_targets[radar_id].keys()):
                    target_id= int(target_id)
                    if target_id in self.trails and self.trails[target_id]:
                        #print("TARGET", target_id)
                        target_point = self.trails[target_id][-1]
                        target_viewport_point = self.mapFromScene(target_point)
                        radar_center_scene = radar_data['icon'].scenePos()
                        radar_center_viewport = self.mapFromScene(radar_center_scene)
                        dx = target_viewport_point.x() - radar_center_viewport.x()
                        dy = radar_center_viewport.y() - target_viewport_point.y()
                        azimuth = np.degrees(np.arctan2(dy, dx)) % 360
                        distance = np.sqrt(dx*dx + dy*dy)
                        self.tracked_targets[radar_id][target_id] = {'azimuth': azimuth, 'distance': distance}
                        if distance > radar_data['radius']:
                            continue
                        ray_length = distance * 0.9
                        end_x = radar_center_viewport.x() + ray_length * np.cos(np.radians(azimuth))
                        end_y = radar_center_viewport.y() - ray_length * np.sin(np.radians(azimuth))
                        dash_pen = QPen(QColor(255, 0,0), 2,Qt.DashLine)
                        dash_pen.setDashPattern([4,4])
                        painter.setPen(dash_pen)
                        painter.drawLine(radar_center_viewport, QPointF(end_x, end_y))
                        painter.setBrush(QBrush(Qt.red))
                        painter.drawEllipse(QPointF(end_x, end_y), 4, 4)
        self.update()


    def visualize_rls(self, target_id, sector_size):
        self.detection_effects.append({'angle': 45, 'distance': 1500, 'target_id':target_id, 'alpha':255, 'steps_left': 30})
        if target_id not in self.tracked_targets:
            self.tracked_targets[target_id]=45 #angle
            self.target_smoothing[target_id]={'current':sector_size, 'target': sector_size, 'step':0}
            self.update()

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

    def handle_target_detection(self, radar_id, target_id, size):
        if radar_id not in self.tracked_targets:
            self.tracked_targets[radar_id] = {}
        if target_id not in self.tracked_targets[radar_id]:
            self.tracked_targets[radar_id][target_id] = size
        self.update()

    def handle_target_untracking(self, radar_id, target_id):
        for r_id in [radar_id, str(radar_id), int(radar_id) if str(radar_id).isdigit() else None]:
               if r_id is None:
                   continue
               if r_id in self.tracked_targets:
                   # Аналогично проверяем target_id
                   for t_id in [target_id, str(target_id), int(target_id) if str(target_id).isdigit() else None]:
                       if t_id is None:
                           continue
                       if t_id in self.tracked_targets[r_id]:
                           del self.tracked_targets[r_id][t_id]
                           # Удаляем радар, если у него не осталось целей
                           if not self.tracked_targets[r_id]:
                               del self.tracked_targets[r_id]
                           print(f"Удалена цель {target_id} из радара {radar_id}")
                           return
        #print(f"Цель {target_id} не найдена в радаре {radar_id}")
        '''
        print("HANDLE",self.tracked_targets)

        print("Содержимое tracked_targets с типами:")
        for radar_id, targets_dict in self.tracked_targets.items():
               print(f"• Радар ID: {radar_id} (тип: {type(radar_id)})")
               for target_id, target_data in targets_dict.items():
                   print(f"  ∟ Цель ID: {target_id} (тип: {type(target_id)})")
                   print(f"    Данные: {target_data} (тип данных: {type(target_data)})")
                   if isinstance(target_data, dict):
                       for k, v in target_data.items():
                           print(f"      {k}: {v} (тип: {type(v)})")

        if str(radar_id) or radar_id  in self.tracked_targets:
               if target_id or str(target_id) in self.tracked_targets[radar_id]:
                   print("IF")

                   del self.tracked_targets[radar_id][target_id]
                   if not self.tracked_targets[radar_id]:
                       del self.tracked_targets[radar_id]

               #self.update()
         '''
        #print("END HANDLER",self.tracked_targets)


    def handle_target_destruction(self, explosion_data):
            for radar_id, targets in list(self.tracked_targets.items()):
                if explosion_data.plane_id in targets:
                    del targets[explosion_data.plane_id]
                    if not targets:
                        del self.tracked_targets[radar_id]
            self.update()
    '''
    def update_target_azimuths(self):
        for radar_id, radar_data in self.radar.items():
            radar_icon = radar_data['icon']
            #radar_center = QPoint(radar_icon.x_pos + radar_icon.width() // 2, radar_icon.y_pos + radar_icon.height() // 2)
            radar_center =radar_icon.scenePos()
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
    '''
    def update_target_azimuths(self):
            for radar_id, radar_data in self.radar.items():
                radar_icon = radar_data['icon']
                center = radar_icon.scenePos()
                updated = False
                for target_id in list(self.tracked_targets.keys()):
                    if target_id in self.trails and self.trails[target_id]:
                        target_point = self.trails[target_id][-1]
                        dx = target_point.x() - center.x()
                        dy = center.y() - target_point.y()
                        self.tracked_targets[target_id] = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
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
        return max(100, max(50, int(max_distance * 1.2)))

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

    def add_to_trail(self, obj_id, point):
       if obj_id not in self.trails:
            self.trails[obj_id] = []
       self.trails[obj_id].append(QPointF(point))
       self.update()

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

