from dispatcher.enums import Modules
from dispatcher.enums import Priorities
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, ToGuiRocketInactivated,RadarToGUICurrentTarget
from dispatcher.dispatcher import Dispatcher
from queue import PriorityQueue
from vizualization.parametr_window import ParametersWindow
import random
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QWidget, QGroupBox, QLabel, QTextEdit, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIntValidator
from vizualization.map_class import MapWindow

class startPage(QWidget):
    def __init__(self, dispatcher, app, simulation):
        super().__init__()
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
        self.setGeometry(300, 300, 400, 400)
        layout = QVBoxLayout()
        text_labels = ['Моделирование работы ЗРС', 'Задать параметры моделирования:']
        for label in text_labels:
            text = QLabel(label)
            layout.addWidget(text)
        self.button_radar = QPushButton('Модуль радиолокатора', self)
        self.button_pbu = QPushButton('Модуль ПБУ', self)
        self.button_pu = QPushButton('Модуль ПУ', self)
        self.button_vo = QPushButton('Модуль ВО', self)
        layout.addWidget(self.button_radar)
        layout.addWidget(self.button_pbu)
        layout.addWidget(self.button_pu)
        layout.addWidget(self.button_vo)
        steps_label = QLabel ('Введите количество шагов моделирования:')
        layout.addWidget(steps_label)
        self.steps_input=QLineEdit(str(self.steps))
        self.steps_input.setValidator(QIntValidator(1,1000))
        layout.addWidget(self.steps_input)
        self.saved_params_label = QLabel("Введенные параметры:")
        layout.addWidget(self.saved_params_label)
        self.params_display = QTextEdit()
        self.params_display.setReadOnly(True)
        self.params_display.setMaximumHeight(100)
        layout.addWidget(self.params_display)
        self.button_radar.clicked.connect(lambda: self.open_parameters_window('Радиолокатор'))
        self.button_pbu.clicked.connect(lambda: self.open_parameters_window('ПБУ'))
        self.button_pu.clicked.connect(lambda: self.open_parameters_window('ПУ'))
        self.button_vo.clicked.connect(lambda: self.open_parameters_window('ВО'))
        self.button_start_model = QPushButton('Начать моделирование')
        layout.addWidget(self.button_start_model)
        self.button_start_model.clicked.connect(self.open_map_window)
        layout.addStretch(1)
        self.setLayout(layout)
        self.show()


    def update_params_display(self):
        if not self.module_params:
            self.params_display.setPlainText("Параметры не заданы")
            return
        display_text = []
        for module, params in self.module_params.items():
            display_text.append(f"====== {module} ======")
            for param, value in params.items():
                display_text.append(f"{param}: {value}")
            display_text.append("")
        self.params_display.setPlainText("\n".join(display_text))


    def set_params_callback(self, callback, expect_modules):
        self.on_params_save_callback = callback
        if expect_modules:
            self.expect_modules=set(expect_modules)

    def update(self):
        messages = []
        message_queue = self.dispatcher.get_message(Modules.GUI)
        while not message_queue.empty():
                messages.append(message_queue.get())
        for priority, message in messages:
                    if isinstance(message, SEStarting):
                        self.handle_se_starting(message)
                    elif isinstance(message, SEKilled):
                        self.handle_se_killed(message)
                    elif isinstance(message, SEAddRocket):
                        self.handle_se_add_rocket(message)
                    elif isinstance(message, RadarToGUICurrentTarget):
                        self.handle_radar_to_gui_current_target(message)


    def open_map_window(self):
        self.map_window = MapWindow()
        self.map_window.show()
        self.dispatcher.register(Modules.GUI)
        self.simulation.set_units()
        self.simulation.modulate()

    def handle_se_starting(self, message: SEStarting):
        for plane_id, plane_data in message.planes.items():
            self.map_window.text_output.append(f"✈️ Запуск самолета с ID: {plane_id}")
            self.map_window.visualize_plane_track(plane_id, plane_data)
            self.map_window.text_output.append(f"РЛС отслеживает самолет с ID: {plane_id}")
            self.map_window.visualize_rls(plane_id, 60, 350)
            self.test_id=plane_id
        self.map_window.text_output.append(f"Уничтоженние самолета с ID: {self.test_id}")
        #pass
            #self.map_window.handle_explosion_event()
            # rocket = Rocket(701, [300.0,300.0,0.0],[50.0, 30.0, 100.0], 0.0)
            # plane (400,400,
        test_message = SEKilled(Modules.GUI, Priorities.STANDARD,
                collision_step=42,
                rocket_id=701,
                rocket_coords=np.array([450.0, 400.0, 50.0]),  # x, y, z
                plane_id=self.test_id,
                plane_coords=np.array([600.0, 600.0, 55.0]),
                collateral_damage=[
                    #(301, np.array([170.0, 220.0, 60.0])),  # Поврежденный объект 1
                   # (302, np.array([140.0, 190.0, 45.0]))   # Поврежденный объект 2
                ]
        )
        #self.map_window.handle_explosion_event(   rocket_id=test_message.rocket_id,
        #rocket_coords=test_message.rocket_coords,
        #plane_id=test_message.plane_id,
        #plane_coords=test_message.plane_coords,
        #collateral_damage=test_message.collateral_damage)

    def handle_se_killed(self, message: SEKilled):
        self.map_window.text_output.append(f"Уничтоженние самолета с ID: {message.plane_id}")
        pass
        #self.map_window.handle_explosion_event()
        # rocket = Rocket(701, [300.0,300.0,0.0],[50.0, 30.0, 100.0], 0.0)
        # plane (400,400,
        test_message = SEKilled(
            collision_step=42,
            rocket_id=701,
            rocket_coords=np.array([450.0, 400.0, 50.0]),  # x, y, z
            plane_id=601,
            plane_coords=np.array([400.0, 400.0, 55.0]),
            collateral_damage=[
                #(301, np.array([170.0, 220.0, 60.0])),  # Поврежденный объект 1
               # (302, np.array([140.0, 190.0, 45.0]))   # Поврежденный объект 2
            ]
        )
        self.map_window.handle_explosion_event( test_message )

    def handle_se_add_rocket(self, message: SEAddRocket):
        #self.text_output.append(f'<span style="color: blue;">• Ракета с ID {zur_id} появилася в воздушном пространстве</span>')
        self.map_window.text_output.append(f'<span style="color: blue;">• Добавлена ракета с ID: {message.rocket_id}</span>')
        self.map_window.visualize_zur_track(message.rocket_id, message.rocket_coords, detection_area=None)

    def handle_radar_to_gui_current_target(self, message: RadarToGUICurrentTarget):
        self.map_window.text_output.append(f"<span style='color: red;'>•</span> Радар с ID: {message.radar_id} отслеживает цель с ID: {message.target_id}")
        #раскомментировать для тестирования; пока значения 60,350 для примера, я добавлю их считывание с бл
        #self.map_window.visualize_rls(plane_id, 60, 350)


    def open_parameters_window(self, module_name):
        self.params_window = ParametersWindow(module_name, self.store_parameters, self)
        self.params_window.show()

    def store_parameters(self, module_name, params_dict):
       self.module_params[module_name] = params_dict
       self.update_params_display()
       if self.expect_modules and self.on_params_save_callback:
           if self.expect_modules.issubset(self.module_params.keys()):
               self.on_params_save_callback(self.module_params)
               print(f'Параметры модуля {module_name} сохранены: {params_dict}')


    def set_session_params(self, db):
       for module_name, params in self.module_params.items():
            if module_name == 'Радиолокатор':
                radar_id = len(db.load_radars()) + 1
                db.add_radar(radar_id, params['position'], params['max_targets'], params['angle_of_view'], params['range'])
            elif module_name == 'ПУ':
                launcher_id = len(db.load_launchers()) + 1
                db.add_launcher(launcher_id, params['position'], params['missile_count'], params['range'], params['velocity'])
            elif module_name == 'ПБУ':
                cc_id = len(db.load_cc()) + 1
                db.add_cc(cc_id, params['position'])
            elif module_name == 'ВО':
                for i, element in enumerate(params['elements'], 1):
                    plane_id = len(db.load_planes()) + 1
                    start_pos = element['start_pos']
                    end_pos = element['end_pos']
                    if isinstance(start_pos, str):
                        start_pos = tuple(map(float, start_pos.split(',')))
                    if isinstance(end_pos, str):
                        end_pos = tuple(map(float, end_pos.split(',')))
                    if len(start_pos) != 3 or len(end_pos) != 3:
                        raise ValueError("Координаты должны содержать 3 значения (x,y,z)")
                    db.add_plane(plane_id, start_pos, end_pos)

