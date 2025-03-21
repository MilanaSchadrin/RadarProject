class SkyEnv:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher
        self.planes = []
        self.rockets = []
        self.targets = {}  # {rocket: plane}
    
    def check_collision(self, rocket, plane):
        return rocket.currentPos == plane.currentPos
    
    def check_if_in_radius(self, rocket, plane, radius):
        return abs(rocket.currentPos - plane.currentPos) <= radius
    
    def remove_plane(self, plane):
        if plane in self.planes:
            self.planes.remove(plane)
    
    def remove_rocket(self, rocket):
        if rocket in self.rockets:
            self.rockets.remove(rocket)
    
    def delete_pair(self, rocket, plane):
        if (rocket, plane) in self.targets:
            del self.targets[(rocket, plane)]
    
    def send_message(self, message):
        self.dispatcher.send_message(message)
    
    def get_message(self, recipient_id):
        return self.dispatcher.get_message()
    
    def update(self):
        for obj in self.planes + self.rockets:
            obj.update()
            
        for rocket in self.rockets:
            for plane in self.planes:
                if self.check_collision(rocket, plane):
                    rocket.boom()
                    self.remove_rocket(rocket)
                    self.remove_plane(plane)
                    self.delete_pair(rocket, plane)
        
        self.dispatcher.send_message(SEtoGUIUpdateRocket)
