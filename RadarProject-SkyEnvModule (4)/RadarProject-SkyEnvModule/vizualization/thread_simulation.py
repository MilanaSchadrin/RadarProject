# This Python file uses the following encoding: utf-8
from PyQt5.QtCore import QThread, pyqtSignal
from dispatcher.enums import Modules

class SimulationThread(QThread):
    progress_updated = pyqtSignal(int)

    def __init__(self, simulation, steps, data_collector):
        super().__init__()
        self.simulation = simulation
        self.steps = steps
        self.data_collector = data_collector

    def run(self):
        """Выполняет моделирование и сбор данных"""
        self.simulation.dispatcher.register(Modules.GUI)
        self.simulation.set_units()

        simulation_data = []

        for step in range(self.steps):
            # Выполняем шаг моделирования
            self.simulation.skyEnv.update()
            self.simulation.CC.update()

            # Собираем данные
            step_data = self.data_collector.collect_step_data(step)
            simulation_data.append(step_data)

            # Обновляем прогресс
            self.progress_updated.emit(step + 1)

            # Даем возможность обработать события GUI
            QThread.msleep(50)

        # Возвращаем собранные данные
        self.finished.emit(simulation_data)
