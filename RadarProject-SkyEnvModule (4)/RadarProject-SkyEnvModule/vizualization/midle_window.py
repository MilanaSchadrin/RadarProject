# This Python file uses the following encoding: utf-8
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton, QApplication


class LoadingWindow(QDialog):
    def __init__(self, total_steps, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Загрузка результатов моделирования")
        self.setFixedSize(400, 150)

        layout = QVBoxLayout()

        self.label = QLabel("Идет обработка результатов моделирования...")
        layout.addWidget(self.label)

        self.progress = QProgressBar()
        self.progress.setMaximum(total_steps)
        layout.addWidget(self.progress)

        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)

    def update_progress(self, current_step):
        self.progress.setValue(current_step)
        QApplication.processEvents()
