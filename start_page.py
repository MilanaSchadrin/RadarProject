#from enums import Modules
#from messages import SEKilled,SEAddRocket,SEAddRocketToRadar,SEStarting,CCToSkyEnv,ToGuiRocketInactivated,LauncherControllerMissileLaunched
#from queue import PriorityQueue
from map_window import MapWindow
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QHBoxLayout
import random
import time

class start_page(QWidget):
    def __init__(self, dispatcher):
    #def __init__(self):
        super().__init__()
        self.init_ui()
        self.dispatcher=dispatcher
        self.current_time=0
        self.steps=300

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
'
        #print('update')

    def handle_se_starting(self, message: SEStarting):
                for plane_id, plane_data in message.planes.items():                        
                    self.map_window.text_output.append(f"Добавлена воздушная цель с ID: {plane_id}")
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

        for i in range(self.steps):
                self.update()
                time.sleep(3)

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
               self.params_window = ParametersWindow(module_name)
               self.params_window.show()

class ParametersWindow(QWidget):
    def __init__(self, module_name):
        super().__init__()
        self.module_name = module_name
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle(f"Параметры для {self.module_name}")
        self.setGeometry(400, 400, 300, 200)
        layout = QVBoxLayout()

        if self.module_name == 'Радиолокатор':
            layout.addWidget(QLabel("Угол обзора (азимут, °) : "))
            self.angle_input = QLineEdit(self)
            layout.addWidget(self.angle_input)
            layout.addWidget(QLabel("Дальность действия, км : "))
            self.range_input = QLineEdit(self)
            layout.addWidget(self.range_input)
            self.submit_button = QPushButton('Сохранить параметры', self)
            layout.addWidget(self.submit_button)
            self.submit_button.clicked.connect(self.save_parameters)
            self.setLayout(layout)

        if self.module_name == 'ПБУ':
            layout.addWidget(QLabel("Количество одновременно контролируемых ЗУР, шт :"))
            self.cout_zur_control = QLineEdit(self)
            layout.addWidget(self.cout_zur_control)
            self.submit_button = QPushButton('Сохранить параметры', self)
            layout.addWidget(self.submit_button)
            self.submit_button.clicked.connect(self.save_parameters)
            self.setLayout(layout)

        if self.module_name == 'ПУ':
            layout.addWidget(QLabel("Количество ракет, которые могут быть размещены на установке, шт :"))
            self.cout_zur = QLineEdit(self)
            layout.addWidget(self.cout_zur)
            self.submit_button = QPushButton('Сохранить параметры', self)
            layout.addWidget(self.submit_button)
            self.submit_button.clicked.connect(self.save_parameters)
            self.setLayout(layout)

        if self.module_name == 'ЗУР':
            layout.addWidget(QLabel("Дальность стрельбы, м : "))
            self.dist = QLineEdit(self)
            layout.addWidget(self.dist)
            layout.addWidget(QLabel("Скорость полета, м/с :"))
            self.velocity_zur = QLineEdit(self)
            layout.addWidget(self.velocity_zur)
            self.submit_button = QPushButton('Сохранить параметры', self)
            layout.addWidget(self.submit_button)
            self.submit_button.clicked.connect(self.save_parameters)
            self.setLayout(layout)

        if self.module_name == 'ВО':
            layout.addWidget(QLabel("Количество воздушных целей, шт : "))
            self.count_goal = QLineEdit(self)
            layout.addWidget(self.count_goal)

            #добавить поля для стартовых позиций
            layout.addWidget(QLabel("Стартовые позиции воздушной цели (x, y , z) : "))
            self.coord_goal = QLineEdit(self)
            layout.addWidget(self.coord_goal)


            self.submit_button = QPushButton('Сохранить параметры', self)
            layout.addWidget(self.submit_button)
            self.submit_button.clicked.connect(self.save_parameters)
            self.setLayout(layout)

    #тут параметры записываются в файл txt; их нужно сохранять в БД;

    def save_parameters(self):
        parameters = {}
        if self.module_name == 'Радиолокатор':
            parameters['angle_of_view'] = self.angle_input.text()
            parameters['range'] = self.range_input.text()
            self.close()
        elif self.module_name == 'ПБУ':
            parameters['controlled_zur_count'] = self.cout_zur_control.text()
            self.close()
        elif self.module_name == 'ПУ':
            parameters['missile_count'] = self.cout_zur.text()
            self.close()
        elif self.module_name == 'ЗУР':
            parameters['shooting_range'] = self.dist.text()
            parameters['flight_speed'] = self.velocity_zur.text()
            self.close()
        elif self.module_name == 'ВО':
            parameters['air_target_count'] = self.count_goal.text()
            self.close()
        file_path = "parameters.txt"
        with open(file_path, 'a') as file:
            file.write(f"Параметры модуля {self.module_name}:\n")
            for key, value in parameters.items():
                file.write(f"{key}: {value}\n")
            file.write("\n")


