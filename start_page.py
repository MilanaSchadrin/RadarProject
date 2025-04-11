from enums import Modules
from messages import SEKilled,SEAddRocket,SEAddRocketToRadar,SEStarting,CCToSkyEnv,ToGuiRocketInactivated,LauncherControllerMissileLaunched
from queue import PriorityQueue
from map_window import MapWindow
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QHBoxLayout
import random
import time
from databaseman import DatabaseManager

class start_page(QWidget):
    def __init__(self, dispatcher):
    #def __init__(self):
        super().__init__()
        self.current_time=0
        self.steps=300
        self.dispatcher=dispatcher

        self.module_params = {}
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
        self.button_zur = QPushButton('Модуль ЗУР', self)
        self.button_vo = QPushButton('Модуль ВО', self)
        layout.addWidget(self.button_radar)
        layout.addWidget(self.button_pbu)
        layout.addWidget(self.button_pu)
        layout.addWidget(self.button_zur)
        layout.addWidget(self.button_vo)

        self.button_radar.clicked.connect(lambda: self.open_parameters_window('Радиолокатор'))
        self.button_pbu.clicked.connect(lambda: self.open_parameters_window('ПБУ'))
        self.button_pu.clicked.connect(lambda: self.open_parameters_window('ПУ'))
        self.button_zur.clicked.connect(lambda: self.open_parameters_window('ЗУР'))
        self.button_vo.clicked.connect(lambda: self.open_parameters_window('ВО'))

        self.button_start_model = QPushButton('Начать моделирование')
        layout.addWidget(self.button_start_model)
        self.button_start_model.clicked.connect(self.open_map_window)
        layout.addStretch(1)
        self.setLayout(layout)
        self.show()
        for i in range(self.steps):
                self.update()

    def update(self):
        ''' Обработка сообщений от диспетчера'''

        mess = self.dispatcher.get_message(Modules.GUI)
        for message in mess:
                    if isinstance(message, SEStarting):
                        self.handle_se_starting(message)
                    elif isinstance(message, SeKilled):
                        self.handle_se_killed(message)
                    elif isinstance(message, SEAddRocket):
                        self.handle_se_add_rocket(message)
                    elif isinstance(message, RadarToGUICurrentTarget):
                        self.handle_radar_to_gui_current_target(message)

        self.current_time += 1

        print('update')

    def handle_se_starting(self, message: SEStarting):
                self.map_window.text_output.append(f"Запуск самолета с ID: {message.plane_id}")
                pass

    def handle_se_killed(self, message: SeKilled):
                self.map_window.text_output.append(f"Уничтоженние самолета с ID: {message.plane_id}")
                pass
    def handle_se_add_rocket(self, message: SEAddRocket):
                self.map_window.text_output.append(f"Добавлена ракета с ID: {message.rocket_id}")
                pass
    def handle_radar_to_gui_current_target(self, message: RadarToGUICurrentTarget):
                self.map_window.text_output.append(f"Радар с ID: {message.radar_id} отслеживает цель с ID: {message.target_id}")
                pass

    def open_map_window(self):

        self.map_window=MapWindow()
        self.map_window.show()
        self.dispatcher.register(Modules.GUI)



        '''
        plane_data = {
            1: np.array(
            [[100.0, 200.0, 1000.0]] ),

            2: np.array([[150.5, 250.2], [400.0, 500.0]]),
            3: np.array([[110.0, 210.0], [500.0, 500.0]])
        }

        mes = self.dispatcher.get_message(Modules.GUI)
        if isinstance(mes, SEStarting):
                print("Получено сообщение SEStarting")
                for plane_id, plane_data in mes.planes.items():
                    #print(plane_id)
                    #print(plane_data)
                    self.map_window.visualize_plane_track(plane_id, plane_data)
         '''


    def open_parameters_window(self, module_name):
        self.params_window = ParametersWindow(module_name, self.store_parameters)
        self.params_window.show()
    def store_parameters(self, module_name, params_dict):
                self.module_params[module_name] = params_dict
                print(f'Параметры модуля {module_name} сохранены: {params_dict}')

    def set_session_params(self, db):
                for module_name, params in self.module_params.items():
                    if module_name == 'Радиолокатор':
                        radar_id = len(db.load_radars()) + 1
                        db.add_radar(radar_id, params['position'], params['max_targets'], params['angle_of_view'], params['range'])

                    elif module_name == 'ПУ':
                        launcher_id = len(db.load_launchers()) + 1
                        db.add_launcher(launcher_id, params['position'], params['missile_count'], params['range'], params['velocity'])

                    elif module_name == 'ВО':
                        plane_id = len(db.load_planes()) + 1
                        db.add_plane(plane_id, params['start'], params['end'])

class ParametersWindow(QWidget):
    def __init__(self, module_name, on_save_callback):
        super().__init__()
        self.module_name = module_name
        self.on_save = on_save_callback
        self.init_ui()
    def init_ui(self):
        self.setWindowTitle(f"Параметры для {self.module_name}")
        layout = QVBoxLayout()

        if self.module_name == 'Радиолокатор':
            layout.addWidget(QLabel("Координаты (x, y, z):"))
            self.pos_input = QLineEdit()
            layout.addWidget(self.pos_input)

            layout.addWidget(QLabel("Макс. количество целей:"))
            self.max_targets_input = QLineEdit()
            layout.addWidget(self.max_targets_input)

            layout.addWidget(QLabel("Угол обзора (°):"))
            self.angle_input = QLineEdit()
            layout.addWidget(self.angle_input)

            layout.addWidget(QLabel("Дальность действия (км):"))
            self.range_input = QLineEdit()
            layout.addWidget(self.range_input)

        elif self.module_name == 'ПУ':
             layout.addWidget(QLabel("Положение (x, y, z):"))
             self.pos_pu = QLineEdit()
             layout.addWidget(self.pos_pu)

             layout.addWidget(QLabel("Кол-во ракет:"))
             self.cout_zur = QLineEdit()
             layout.addWidget(self.cout_zur)

             layout.addWidget(QLabel("Дальность действия (км):"))
             self.dist_zur = QLineEdit()
             layout.addWidget(self.dist_zur)

             layout.addWidget(QLabel("Скорость (м/с):"))
             self.vel_zur = QLineEdit()
             layout.addWidget(self.vel_zur)

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

           elif self.module_name == 'ВО':
                params['count'] = int(self.count_goal.text())
                params['start'] = tuple(map(float, self.coord_goal.text().split(',')))
                params['end'] = tuple(map(float, self.coord_goal_end.text().split(',')))


           self.on_save(self.module_name, params)
           self.close()
