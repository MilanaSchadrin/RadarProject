from skyenv import SkyEnv

class Simulation:
    def __init__(self):
        self.dispatcher = None
        self.gui = None
        self.skyEnv = None
        self.launchers = []
        self.CC = None
        self.plane_data = None
        self.radar_data = None
        self.launcher_data = None
        self.steps = 250
        #self.set_dispatcher()
        #self.set_GUI()
        self.set_units()

    """def set_dispatcher(self):
        self.dispatcher = Dispatcher()

    def set_GUI(self):
        self.gui = GUI(self.dispatcher)
        self.steps, self. plane_data, self.radar_data, self.launcher_data = self.gui.set_session_params()
        #call save here to save data from user into db"""

    def save(self):
        pass
    
    def set_units(self):
        self.skyEnv = SkyEnv(self.dispatcher)
        #self.CC = ControlCenter(self.dispatcher)
        #self.CC.set_units(self.radar_data,self.launcher_data)
        
    def modulate(self, time_step=0):
        for _ in range(self.steps):
            self.skyEnv.update()
            self.CC.update()