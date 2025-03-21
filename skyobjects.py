class SkyObject:
    def __init__(self, dispatcher, obj_id, start, finish, speed):
        self.dispatcher = dispatcher
        self.id = obj_id
        self.status = "alive"
        self.currentPos = start
        self.start = start
        self.finish = finish
        self.trajectory = []
        self.time_left = 0
        self.current_time = 0
        self.speed = speed
    
    def send_message(self, message):
        self.dispatcher.send_message(message)
    
    def get_message(self):
        return self.dispatcher.get_message(self.id)
    
    def update(self):
        pass


class Plane(SkyObject):
    def __init__(self, dispatcher, obj_id, start, finish, speed, priority):
        super().__init__(dispatcher, obj_id, start, finish, speed)
        self.priority = priority
    
    def update(self):
        self.currentPos += self.speed


class Rocket(SkyObject):
    def __init__(self, dispatcher, obj_id, start, finish, radius):
        super().__init__(dispatcher, obj_id, start, finish)
    
    def boom(self):
        self.status = "dead"
        #здесь радиус разрушения
        self.dispatcher.send_message(SEtoRadarPlaneKilled)
    
    def update(self):
        self.currentPos += self.speed