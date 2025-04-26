# This Python file uses the following encoding: utf-8
from PyQt5.QtWidgets import QApplication, QWidget, QGroupBox, QLabel, QTextEdit, QLineEdit, QVBoxLayout, QPushButton, QComboBox, QHBoxLayout
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QIntValidator

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
                layout.addWidget(QLabel("Количество радиолокаторов:"))
                self.module_count = QLineEdit("")
                self.module_count.setValidator(QIntValidator(1, 100))
                layout.addWidget(self.module_count)
                self.apply_button = QPushButton("Применить")
                self.apply_button.clicked.connect(self.create_radar_data)
                layout.addWidget(self.apply_button)
                self.radar_container = QVBoxLayout()
                layout.addLayout(self.radar_container)

        elif self.module_name == 'ПУ':
                            layout.addWidget(QLabel("Количество пусковых установок:"))
                            self.module_count = QLineEdit("1")
                            self.module_count.setValidator(QIntValidator(1, 100))
                            layout.addWidget(self.module_count)

                            self.apply_button = QPushButton("Настроить ПУ")
                            self.apply_button.clicked.connect(self.create_launcher_data)
                            layout.addWidget(self.apply_button)

                            self.launcher_container = QVBoxLayout()
                            layout.addLayout(self.launcher_container)

        elif self.module_name == 'ПБУ':
            layout.addWidget(QLabel("Положение (x, y, z):"))
            self.pos_control = QLineEdit(self)
            layout.addWidget(self.pos_control)

        elif self.module_name == 'ВО':
             layout.addWidget(QLabel("Количество самолетов:"))
             self.module_count = QLineEdit("")
             self.module_count.setValidator(QIntValidator(1,100))
             layout.addWidget(self.module_count)
             self.apply_button = QPushButton("Применить")
             self.apply_button.clicked.connect(self.create_vo_data)
             layout.addWidget(self.apply_button)

             self.vo_container = QVBoxLayout()
             layout.addLayout(self.vo_container)
             self.create_vo_data

        self.submit_button = QPushButton('Сохранить параметры')
        layout.addWidget(self.submit_button)
        self.submit_button.clicked.connect(self.save_parameters)
        self.setLayout(layout)

    def create_radar_data(self):
        for i in reversed(range(self.radar_container.count())):
            self.radar_container.itemAt(i).widget().setParent(None)
        count = int(self.module_count.text()) if self.module_count.text() else 1
        self.radar_fields = []
        for i in range(1, count + 1):
            group_box = QGroupBox(f"Радиолокатор {i}")
            group_layout = QVBoxLayout()
            pos_label = QLabel("Координаты (x,y,z):")
            pos_input = QLineEdit("")
            group_layout.addWidget(pos_label)
            group_layout.addWidget(pos_input)
            targets_label = QLabel("Макс. количество целей:")
            targets_input = QLineEdit("")
            targets_input.setValidator(QIntValidator(1, 100))
            group_layout.addWidget(targets_label)
            group_layout.addWidget(targets_input)
            angle_label = QLabel("Угол обзора (°):")
            angle_input = QLineEdit("")
            angle_input.setValidator(QIntValidator(1, 360))
            group_layout.addWidget(angle_label)
            group_layout.addWidget(angle_input)
            range_label = QLabel("Дальность (км):")
            range_input = QLineEdit("")
            range_input.setValidator(QIntValidator(1, 1000))
            group_layout.addWidget(range_label)
            group_layout.addWidget(range_input)
            group_box.setLayout(group_layout)
            self.radar_container.addWidget(group_box)
            self.radar_fields.append({ 'position': pos_input, 'max_targets': targets_input, 'angle': angle_input,'range': range_input})
    def create_vo_data(self):
        for i in reversed(range(self.vo_container.count())):
            self.vo_container.itemAt(i).widget().setParent(None)
        count = int(self.module_count.text()) if self.module_count.text() else 0
        self.vo_fields = []
        for i in range(1, count + 1):
            group_box = QGroupBox(f"Самолет {i}")
            group_layout = QVBoxLayout()
            start_label = QLabel(f"Стартовая позиция (x,y,z):")
            start_input = QLineEdit()
            group_layout.addWidget(start_label)
            group_layout.addWidget(start_input)
            end_label = QLabel(f"Конечная позиция (x,y,z):")
            end_input = QLineEdit()
            group_layout.addWidget(end_label)
            group_layout.addWidget(end_input)
            group_box.setLayout(group_layout)
            self.vo_container.addWidget(group_box)
            self.vo_fields.append({ 'start': start_input, 'end': end_input,})
    def create_launcher_data(self):
                    for i in reversed(range(self.launcher_container.count())):
                        widget = self.launcher_container.itemAt(i).widget()
                        if widget is not None:
                            widget.setParent(None)

                    count = int(self.module_count.text()) if self.module_count.text() else 1
                    self.launcher_fields = []

                    for i in range(1, count + 1):
                        group_box = QGroupBox(f"Пусковая установка {i}")
                        group_layout = QVBoxLayout()

                        group_layout.addWidget(QLabel("Координаты (x,y,z):"))
                        pos_input = QLineEdit("")
                        group_layout.addWidget(pos_input)

                        group_layout.addWidget(QLabel("Количество ракет:"))
                        count_input = QLineEdit("")
                        count_input.setValidator(QIntValidator(1, 100))
                        group_layout.addWidget(count_input)

                        group_layout.addWidget(QLabel("Дальность действия (км):"))
                        range_input = QLineEdit("")
                        range_input.setValidator(QIntValidator(1, 1000))
                        group_layout.addWidget(range_input)

                        group_layout.addWidget(QLabel("Скорость (м/с):"))
                        velocity_input = QLineEdit("1000")
                        velocity_input.setValidator(QIntValidator(100, 5000))
                        group_layout.addWidget(velocity_input)

                        group_box.setLayout(group_layout)
                        self.launcher_container.addWidget(group_box)
                        self.launcher_fields.append({
                            'position': pos_input,
                            'missile_count': count_input,
                            'range': range_input,
                            'velocity': velocity_input
                        })
    def save_parameters(self):
        params = {}
        if self.module_name == 'ВО':
            count = int(self.module_count.text()) if self.module_count.text() else 0
            params_dict = {'count': count,'elements': []}
            for i, fields in enumerate(self.vo_fields, 1):
                element = {'start_pos': fields['start'].text(),'end_pos': fields['end'].text(),}
                params_dict['elements'].append(element)
            params = params_dict
        if self.module_name == 'Радиолокатор':
                    count = int(self.module_count.text()) if self.module_count.text() else 1
                    params_dict = {'count': count, 'radars': []}

                    for fields in self.radar_fields:
                        radar_params = {
                            'position': tuple(map(float, fields['position'].text().split(','))),
                            'max_targets': int(fields['max_targets'].text()),
                            'angle': float(fields['angle'].text()),
                            'range': float(fields['range'].text())
                        }
                        params_dict['radars'].append(radar_params)

                    params = params_dict
        elif self.module_name == 'ПУ':

                                count = int(self.module_count.text()) if self.module_count.text() else 1
                                params_dict = {'count': count, 'launchers': []}

                                for fields in self.launcher_fields:
                                    launcher_params = {
                                        'position': tuple(map(float, fields['position'].text().split(','))),
                                        'missile_count': int(fields['missile_count'].text()),
                                        'range': int(fields['range'].text()),
                                        'velocity': int(fields['velocity'].text())
                                    }
                                    params_dict['launchers'].append(launcher_params)

                                params = params_dict

        elif self.module_name == 'ПБУ':
            params = {'position': tuple(map(float, self.pos_control.text().split(',')))}
        self.on_save(self.module_name, params)
        self.close()
        '''
        elif self.module_name == 'ПУ':
            params = { 'position': tuple(map(float, self.pos_pu.text().split(','))), 'missile_count': int(self.cout_zur.text()), 'range': int(self.dist_zur.text()),'velocity': int(self.vel_zur.text())}
        '''
