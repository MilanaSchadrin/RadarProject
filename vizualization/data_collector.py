# This Python file uses the following encoding: utf-8
from dispatcher.enums import Modules
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, ToGuiRocketInactivated,RadarToGUICurrentTarget
from dispatcher.dispatcher import Dispatcher

class VisualizationDataCollector:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.simulation_steps = []
        self.current_step = 0

    def collect_step_data(self, step):
        """Собирает данные для одного шага моделирования"""
        step_data = {
            'step': step,
            'events': []
        }

        # Обрабатываем все сообщения для текущего шага
        messages = []
        message_queue = self.dispatcher.get_message(Modules.GUI)
        while not message_queue.empty():
            messages.append(message_queue.get())

        for priority, message in messages:
            event = self._process_message(message, step)
            if event:
                if isinstance(event, list):
                    step_data['events'].extend(event)
                else:
                    step_data['events'].append(event)

        return step_data

    def _process_message(self, message, step):
        """Преобразует сообщения диспетчера в события визуализации"""
        if isinstance(message, SEStarting):

            return self._process_se_starting(message, step)
        elif isinstance(message, SEKilled):
            return self._process_se_killed(message, step)
        elif isinstance(message, SEAddRocket):
            return self._process_se_add_rocket(message, step)
        elif isinstance(message, RadarToGUICurrentTarget):
            return self._process_radar_message(message, step)
        return None
