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

             self.parameters_display = QLabel("")
             layout.addWidget(self.parameters_display)

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


    def save_parameters(self):
        params = {}
        if self.module_name == 'ВО':
            count = int(self.module_count.text()) if self.module_count.text() else 0
            params_dict = {'count': count,'elements': []}
            for i, fields in enumerate(self.vo_fields, 1):
                element = {'start_pos': fields['start'].text(),'end_pos': fields['end'].text(),}
                params_dict['elements'].append(element)
            params = params_dict
        elif self.module_name == 'Радиолокатор':
            params = {'position': tuple(map(float, self.pos_input.text().split(','))), 'max_targets': int(self.max_targets_input.text()), 'angle_of_view': float(self.angle_input.text()),'range': float(self.range_input.text())}
        elif self.module_name == 'ПУ':
            params = { 'position': tuple(map(float, self.pos_pu.text().split(','))), 'missile_count': int(self.cout_zur.text()), 'range': int(self.dist_zur.text()),'velocity': int(self.vel_zur.text())}
        elif self.module_name == 'ПБУ': params = {'position': tuple(map(float, self.pos_control.text().split(',')))}
        self.on_save(self.module_name, params)
        self.close()
