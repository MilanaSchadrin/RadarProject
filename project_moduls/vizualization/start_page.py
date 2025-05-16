import sys
import time
import numpy as np
from queue import PriorityQueue
from dispatcher.enums import Modules
from dispatcher.enums import Priorities
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, ToGuiRocketInactivated,RadarToGUICurrentTarget
from dispatcher.dispatcher import Dispatcher
from vizualization.data_collector_for_visual import  SimulationDataCollector
from vizualization.parametr_window import ParametersWindow
from PyQt5.QtWidgets import QApplication,QProgressBar,QMessageBox, QDialog,QSpinBox, QWidget, QGroupBox, QLabel, QTextEdit, QLineEdit, QVBoxLayout, QPushButton, QComboBox,QHBoxLayout
from PyQt5.QtCore import QTimer, Qt, QSize
from PyQt5.QtGui import QIntValidator,QMovie
from vizualization.map_class import MapWindow

class StartPage(QWidget):
    def __init__(self, dispatcher, app, simulation):
        super().__init__()
        self.steps=None
        self.step=1
        self.dispatcher=dispatcher
        self.map_window=None
        self.simulation = simulation
        self.module_params = {}
        self.on_params_save_callback = None
        self.expect_modules=set()
        self.data_colector = SimulationDataCollector(self.dispatcher)
        self.init_ui()

    def load_db_parameters(self):
            db_name = self.db_name_input.text()
            if not db_name:
                QMessageBox.warning(self, "Ошибка", "Введите название базы данных")
                return

                #self.simulation.db
            planes = self.simulation.db.load_planes()
            radars = self.simulation.db.load_radars()
            launchers = self.simulation.db.load_launchers()
            cc = self.simulation.db.load_cc()

            db_data = {'planes': planes,'radars': radars,'launchers': launchers,'cc': cc}
            for module_name, params in db_data.items():
                self.module_params[module_name] = params

            self.update_params_display()
            QMessageBox.information(self, "Успеx", "Параметры успешно загружены из базы данных")




    def init_ui(self):
        self.setWindowTitle("Параметры моделирования")
        self.setGeometry(300, 300, 400, 400)
        layout = QVBoxLayout()
        text_labels = ['Моделирование работы ЗРС', 'Задать параметры моделирования:']
        for label in text_labels:
            text = QLabel(label)
            layout.addWidget(text)
        self.steps_label = QLabel ('Введите количество шагов моделирования:')
        layout.addWidget(self.steps_label)
        self.steps_input=QLineEdit()
        layout.addWidget(self.steps_input)
        

        self.step_label = QLabel ('Введите шаг моделирования:')
        layout.addWidget(self.step_label)
        self.step_input=QLineEdit()
        layout.addWidget(self.step_input)

        #Загрузка БД по названию
        self.db_name = QLabel ('Введите название базы данных для загрузки:')
        layout.addWidget(self.db_name)
        self.db_name_input=QLineEdit()
        layout.addWidget(self.db_name_input)

        self.load_db_button = QPushButton('Загрузить параметры из БД')
        self.load_db_button.clicked.connect(self.load_db_parameters)
        layout.addWidget(self.load_db_button)

        self.button_radar = QPushButton('Модуль радиолокатора', self)
        self.button_pbu = QPushButton('Модуль ПБУ', self)
        self.button_pu = QPushButton('Модуль ПУ', self)
        self.button_vo = QPushButton('Модуль ВО', self)
        layout.addWidget(self.button_radar)
        layout.addWidget(self.button_pbu)
        layout.addWidget(self.button_pu)
        layout.addWidget(self.button_vo)

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

    def get_step(self):
        try:
            self.steps = int(self.steps_input.text())
            #print("STEPS", self.steps)
        except ValueError:
            print("Некорректное количество шагов")
        return self.steps
    
    def get_step_size(self):
        try:
             self.dispatcher.time_step = float(self.step_input.text())
             print("STEPS", self.dispatcher.time_step)
        except ValueError:
             print("Некорректный шаг")

    def get_db_name(self):
        self.name_db = (self.db_name_input.text())
        self.simulation.db.add_name(self.name_db)
        #print("DB", self.name_db )

    def open_map_window(self):
        self.data_colector.dispatcher.register(Modules.GUI)
        
        loading_window = QDialog(self)
        loading_window.setWindowTitle("Моделирование работы ЗРС")
        loading_window.setFixedSize(600, 400)
        loading_window.setWindowFlags(Qt.Window | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        """main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)"""

        loading_layout = QVBoxLayout()
        loading_layout.setContentsMargins(30, 30, 30, 30)
        loading_layout.setSpacing(20)

        title_label = QLabel("Пожалуйста, подождите")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
        loading_layout.addWidget(title_label)
        
        status_label = QLabel("Загрузка результатов моделирования...")
        status_label.setAlignment(Qt.AlignCenter)
        status_label.setStyleSheet("font-size: 14px; color: #666;")
        loading_layout.addWidget(status_label)
        
        progress = QProgressBar()
        progress.setMaximum(self.steps)
        progress.setTextVisible(False)
        progress.setFixedHeight(10)
        progress.setStyleSheet("""QProgressBar {border: 1px solid #ccc; border-radius: 5px;background: #f0f0f0;}
                                QProgressBar::chunk {background: qlineargradient( spread:pad, x1:0, y1:0.5, x2:1, y2:0.5, stop:0 #4facfe, stop:1 #00f2fe);
                            border-radius: 4px;}""")
        loading_layout.addWidget(progress)
        percent_label = QLabel("0%")
        percent_label.setAlignment(Qt.AlignCenter)
        percent_label.setStyleSheet("font-size: 14px; color: #4facfe; font-weight: bold;")
        loading_layout.addWidget(percent_label)
        #gif_label = QLabel()
        #gif_label.setAlignment(Qt.AlignCenter)
        #movie = QMovie("vizualization/pictures/loading.gif")  # путь к твоему GIF
        #movie.setScaledSize(QSize(500, 200))
        #gif_label.setFixedSize(600, 370)
        #gif_label.setMovie(movie)
        #movie.start()
        #gif_label.setStyleSheet("background: transparent;")
        #gif_container = QHBoxLayout()

        #gif_container.setContentsMargins(0, 0, 0, 0)  # Убираем margins у контейнера
        #gif_container.addWidget(gif_label)

        #loading_layout.addLayout(gif_container)

        loading_window.setLayout(loading_layout)
        self.dot_animation = QTimer(loading_window)
        self.dot_count = 0

        def animate_dots():
            dots = "." * (self.dot_count % 4)
            title_label.setText(f"Процесс моделирования...{dots}")
            self.dot_count += 1
        self.dot_animation.timeout.connect(animate_dots)
        self.dot_animation.start(500)
        loading_window.show()

        def update_progress(step):
            progress.setValue(step)
            percent = int(step / self.steps * 100)
            percent_label.setText(f"{percent}%")
            status_label.setText(f"Выполнено {step} из {self.steps} шагов...")
            QApplication.processEvents()
        self.simulation.set_units()
        self.simulation.modulate(progress_callback=update_progress)
        loading_window.close()
        self.show_results()

    def show_results(self):

        self.map_window = MapWindow(self.simulation.db)
        self.map_window.set_simulation_data(self.data_colector.steps_data)
        self.map_window.rockets_data = self.data_colector.rockets_data

        self.map_window.show()
        for i, step in enumerate(self.data_colector.steps_data):
            msg_count = len(step['messages'])
            if msg_count > 0:
                #print(f"Шаг {i}: {msg_count} сообщений")
                for msg in step['messages']:
                    pass
                    #print(f"  - {msg['type']} (приоритет: {msg['priority']})")
        #self.hide()

    def open_parameters_window(self, module_name):
        self.params_window = ParametersWindow(module_name, self.store_parameters, self.simulation.db)
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
                       for i, radar_data in enumerate(params['radars'], 1):
                               position = radar_data['position']
                               if isinstance(position, str):
                                   position = tuple(map(float, position.split(',')))
                               db.add_radar(i, position, int(radar_data['max_targets']), float(radar_data['range']))
            elif module_name == 'ПУ':
                                       for i, launcher_data in enumerate(params['launchers'], 1):
                                           position = launcher_data['position']
                                           if isinstance(position, str):
                                               position = tuple(map(float, position.split(',')))
                                           db.add_launcher(
                                               i,
                                               position,
                                               int(launcher_data['missile_count'])
                                           )

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
