# This Python file uses the following encoding: utf-8
from dispatcher.enums import Modules
from dispatcher.enums import Priorities
from dispatcher.messages import SEKilled,SEAddRocket,SEStarting, SEKilledGUI,  TargetUnfollowedGUI, ToGuiRocketInactivated,RadarToGUICurrentTarget,RocketUpdate
from dispatcher.dispatcher import Dispatcher

class SimulationDataCollector:
    def __init__(self, dispatcher):
        self.dispatcher=dispatcher
        self.steps_data=[]
        self.current_step=0
        self.rockets_data = {} # {rocket_id: {step:coords}}
    def begin_step(self, step):
        self.current_step = step
        self.steps_data.append({'step': step,'messages': []})

    def collect_messages(self):
        if not self.steps_data or self.steps_data[-1]['step'] != self.current_step:
            self.begin_step(self.current_step)
        message_queue = self.dispatcher.get_message(Modules.GUI)
        while not message_queue.empty():
            priority, message = message_queue.get()
            #print(message)
            self._add_message(message, priority)

    def _add_message(self, message, priority):
        msg_type = self._get_message_type(message)
        self.steps_data[-1]['messages'].append({'type': msg_type,'data': message,'priority': priority,'step': self.current_step})
        #print( self.steps_data)

        if msg_type == 'rocket_add':
            self.handle_rocket_add(message)
        elif msg_type == 'rocket_update':
            self.handle_rocket_update(message)

    def _get_message_type(self, message):
        if isinstance(message, SEStarting):
            return 'plane_start'
        elif isinstance(message, SEKilledGUI):
            return 'explosion'
        elif isinstance(message, SEAddRocket):
            return 'rocket_add'
        elif isinstance(message, RadarToGUICurrentTarget):
            return 'radar_tracking'
        elif isinstance(message, ToGuiRocketInactivated):
            return 'rocket_inactivate'
        elif isinstance(message, RocketUpdate):
            return 'rocket_update'
        elif isinstance(message, TargetUnfollowedGUI):
            return 'radar_untracking'

    def handle_rocket_add(self, rocket_data):
               """Обработка добавления новой ракеты"""
               rocket_id = rocket_data.rocket_id
               if rocket_id not in self.rockets_data:
                   self.rockets_data[rocket_id] = {}
               # Записываем начальные координаты (если они есть)
               if hasattr(rocket_data, 'rocket_coords'):
                   self.rockets_data[rocket_id][self.current_step] = rocket_data.rocket_coords

    def handle_rocket_update(self, rocket_data):
               """Обработка обновления координат ракеты"""
               rocket_id = rocket_data.rocket_id
               if rocket_id in self.rockets_data:
                   # Записываем координаты для текущего шага
                   self.rockets_data[rocket_id][self.current_step] = rocket_data.rocket_coords
               else:
                   # Если ракета не была добавлена, создаем запись
                   self.rockets_data[rocket_id] = {self.current_step: rocket_data.rocket_coords}

