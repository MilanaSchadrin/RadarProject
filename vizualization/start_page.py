from dispatcher.enums import Modules
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, ToGuiRocketInactivated,RadarToGUICurrentTarget
from dispatcher.dispatcher import Dispatcher
from queue import PriorityQueue
from vizualization.map_window import MapWindow
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIntValidator
import random
import time

class startPage(QWidget):
    def __init__(self, dispatcher, app, simulation):
    #def __init__(self):
        super().__init__()
        self.current_time=0
        self.steps=300
        self.dispatcher=dispatcher
        self.map_window=None
        self.simulation = simulation
        self.module_params = {}
        self.on_params_save_callback = None
        self.expect_modules=set()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Start")
        self.setGeometry(300, 300, 400, 300)
        layout = QVBoxLayout()
        text_labels = ['Моделирование работы ЗРС', 'Задать параметры моделирования:']
        for label in text_labels:
            text = QLabel(label)
            layout.addWidget(text)

        self.button_radar = QPushButton('Модуль радиолокатора', self)
        self.button_pbu = QPushButton('Модуль ПБУ', self)
        self.button_pu = QPushButton('Модуль ПУ', self)
        #self.button_zur = QPushButton('Модуль ЗУР', self)
        self.button_vo = QPushButton('Модуль ВО', self)

        layout.addWidget(self.button_radar)
        layout.addWidget(self.button_pbu)
        layout.addWidget(self.button_pu)
        #layout.addWidget(self.button_zur)
        layout.addWidget(self.button_vo)
        steps_label = QLabel ('Введите количество шагов моделирования:')
        layout.addWidget(steps_label)

        self.steps_input=QLineEdit(str(self.steps))
        self.steps_input.setValidator(QIntValidator(1,1000))
        layout.addWidget(self.steps_input)

        self.button_radar.clicked.connect(lambda: self.open_parameters_window('Радиолокатор'))
        self.button_pbu.clicked.connect(lambda: self.open_parameters_window('ПБУ'))
        self.button_pu.clicked.connect(lambda: self.open_parameters_window('ПУ'))
        #self.button_zur.clicked.connect(lambda: self.open_parameters_window('ЗУР'))
        self.button_vo.clicked.connect(lambda: self.open_parameters_window('ВО'))
        self.button_start_model = QPushButton('Начать моделирование')
        layout.addWidget(self.button_start_model)
        self.button_start_model.clicked.connect(self.open_map_window)
        layout.addStretch(1)
        self.setLayout(layout)
        self.show()

    def set_params_callback(self, callback, expect_modules):
        self.on_params_save_callback = callback
        if expect_modules:
            self.expect_modules=set(expect_modules)

    def update(self):
        ''' Обработка сообщений от диспетчера'''
        print('update')
        messages = []
        message_queue = self.dispatcher.get_message(Modules.GUI)
        while not message_queue.empty():
                messages.append(message_queue.get())
        for priority, message in messages:
                    if isinstance(message, SEStarting):
                        self.handle_se_starting(message)
                        print('SE send units')
                    elif isinstance(message, SEKilled):
                        self.handle_se_killed(message)
                        print('Plane was killed')
                    elif isinstance(message, SEAddRocket):
                        self.handle_se_add_rocket(message)
                        print('Rocket was added')
                    elif isinstance(message, RadarToGUICurrentTarget):
                        self.handle_radar_to_gui_current_target(message)
                        print('Radar controlls')

        self.current_time += 1

    def open_map_window(self):
        self.map_window = MapWindow()
        self.map_window.show()
        self.dispatcher.register(Modules.GUI)
        self.simulation.set_units()
        self.simulation.modulate()

    def handle_se_starting(self, message: SEStarting):
                for plane_id, plane_data in message.planes.items():
                      self.map_window.text_output.append(f"Запуск самолета с ID: {plane_id}")
                      self.map_window.visualize_plane_track(plane_id, plane_data)
                      self.map_window.text_output.append(f"РЛС отслеживает самолет с ID: {plane_id}")
                      self.map_window.visualize_rls(plane_id, 60, 350)

    def handle_se_killed(self, message: SEKilled):
                self.map_window.text_output.append(f"Уничтоженние самолета с ID: {message.plane_id}")
                pass
    def handle_se_add_rocket(self, message: SEAddRocket):
                self.map_window.text_output.append(f"Добавлена ракета с ID: {message.rocket_id}")
                self.map_window.visualize_zur_track(message.rocket_id, message.rocket_coords, detection_area=None)
    def handle_radar_to_gui_current_target(self, message: RadarToGUICurrentTarget):
                self.map_window.text_output.append(f"Радар с ID: {message.radar_id} отслеживает цель с ID: {message.target_id}")
                #раскомментировать для тестирования; пока значения 60,350 для примера, я добавлю их считывание с бл
                #self.map_window.visualize_rls(plane_id, 60, 350)

    def open_parameters_window(self, module_name):
        self.params_window = ParametersWindow(module_name, self.store_parameters, self)
        self.params_window.show()

    def store_parameters(self, module_name, params_dict):
        #if self.on_params_save_callback:
         self.module_params[module_name] = params_dict
         if self.expect_modules and self.on_params_save_callback:
             if self.expect_modules.issubset(self.module_params.keys()):
                self.on_params_save_callback(self.module_params)
                print(f'Параметры модуля {module_name} сохранены: {params_dict}')

    def set_session_params(self, db):
                print('set')
                for module_name, params in self.module_params.items():
                    if module_name == 'Радиолокатор':
                        radar_id = len(db.load_radars()) + 1
                        db.add_radar(radar_id, params['position'], params['max_targets'], params['angle_of_view'], params['range'])

                    elif module_name == 'ПУ':
                        launcher_id = len(db.load_launchers()) + 1
                        db.add_launcher(launcher_id, params['position'], params['missile_count'], params['range'], params['velocity'])

                    elif module_name == 'ПБУ':
                         сс_id = len(db.load_cc()) + 1
                         db.add_cc(сс_id, params['position'])

                    elif module_name == 'ВО':
                        plane_id = len(db.load_planes()) + 1
                        db.add_plane(plane_id, params['start'], params['end'])



class ParametersWindow(QWidget):
    def __init__(self, module_name, on_save_callback, main_wind):
        super().__init__()
        self.module_name = module_name
        self.on_save = on_save_callback
        self.main_wind = main_wind
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle(f"Параметры для {self.module_name}")
        layout = QVBoxLayout()

        if self.module_name == 'Радиолокатор':
            layout.addWidget(QLabel("Координаты (x, y, z):"))
            self.pos_input = QLineEdit()
            layout.addWidget(self.pos_input)

            layout.addWidget(QLabel("Максимальное количество сопровождаемых целей:"))
            self.max_targets_input = QLineEdit()
            layout.addWidget(self.max_targets_input)

            layout.addWidget(QLabel("Угол обзора (°):"))
            self.angle_input = QLineEdit()
            layout.addWidget(self.angle_input)

            layout.addWidget(QLabel("Дальность действия (км):"))
            self.range_input = QLineEdit()
            layout.addWidget(self.range_input)

        elif self.module_name == 'ПУ':
             layout.addWidget(QLabel("Координаты (x, y, z):"))
             self.pos_pu = QLineEdit()
             layout.addWidget(self.pos_pu)

             layout.addWidget(QLabel("Количество ракет:"))
             self.cout_zur = QLineEdit()
             layout.addWidget(self.cout_zur)

             layout.addWidget(QLabel("Дальность действия (км):"))
             self.dist_zur = QLineEdit()
             layout.addWidget(self.dist_zur)

             layout.addWidget(QLabel("Скорость (м/с):"))
             self.vel_zur = QLineEdit()
             layout.addWidget(self.vel_zur)
            
        elif self.module_name == 'ПБУ':
            layout.addWidget(QLabel("Положение (x, y, z):"))
            self.pos_control = QLineEdit(self)
            layout.addWidget(self.pos_control)
            
        elif self.module_name == 'ВО':
             layout.addWidget(QLabel("Количество целей:"))
             self.count_goal = QLineEdit()
             layout.addWidget(self.count_goal)

             layout.addWidget(QLabel("Стартовая позиция (x, y, z):"))
             self.coord_goal = QLineEdit()
             layout.addWidget(self.coord_goal)

             layout.addWidget(QLabel("Конечная позиция (x, y, z):"))
             self.coord_goal_end = QLineEdit()
             layout.addWidget(self.coord_goal_end)


        self.submit_button = QPushButton('Сохранить параметры')
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.save_parameters)
        self.setLayout(layout)

    def save_parameters(self):
           params = {}

           if self.module_name == 'Радиолокатор':
                params['position'] = tuple(map(float, self.pos_input.text().split(',')))
                params['max_targets'] = int(self.max_targets_input.text())
                params['angle_of_view'] = float(self.angle_input.text())
                params['range'] = float(self.range_input.text())

           elif self.module_name == 'ПУ':
                params['position'] = tuple(map(float, self.pos_pu.text().split(',')))
                params['missile_count'] = int(self.cout_zur.text())
                params['range'] = int(self.dist_zur.text())
                params['velocity'] = int(self.vel_zur.text())

           elif self.module_name == 'ПБУ':
                     params['position'] = tuple(map(float, self.pos_control.text().split(',')))

           elif self.module_name == 'ВО':
                params['count'] = int(self.count_goal.text())
                params['start'] = tuple(map(float, self.coord_goal.text().split(',')))
                params['end'] = tuple(map(float, self.coord_goal_end.text().split(',')))
           self.on_save(self.module_name, params)
           self.close()

