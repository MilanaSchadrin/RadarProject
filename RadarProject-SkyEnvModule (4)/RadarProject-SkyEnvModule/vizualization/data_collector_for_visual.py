# This Python file uses the following encoding: utf-8
from dispatcher.enums import Modules
from dispatcher.enums import Priorities
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, ToGuiRocketInactivated,RadarToGUICurrentTarget
from dispatcher.dispatcher import Dispatcher

class SimulationDataCollector:
    def __init__(self, dispatcher):
        self.dispatcher=dispatcher
        self.steps_data=[]
        self.current_step=0

    def begin_step(self, step):
                self.current_step = step
                self.steps_data.append({
                    'step': step,
                    'messages': []
                })

    def collect_messages(self):
                if not self.steps_data or self.steps_data[-1]['step'] != self.current_step:
                    self.begin_step(self.current_step)
                message_queue = self.dispatcher.get_message(Modules.GUI)
                while not message_queue.empty():
                    priority, message = message_queue.get()
                    self._add_message(message, priority)

    def _add_message(self, message, priority):
                msg_type = self._get_message_type(message)
                self.steps_data[-1]['messages'].append({
                    'type': msg_type,
                    'data': message,
                    'priority': priority,
                    'step': self.current_step
                })
    def _get_message_type(self, message):
                        if isinstance(message, SEStarting):
                            return 'plane_start'
                        elif isinstance(message, SEKilled):
                            return 'explosion'
                        elif isinstance(message, SEAddRocket):
                            return 'rocket_add'
                        elif isinstance(message, RadarToGUICurrentTarget):
                            return 'radar_tracking'
                        return 'other'
