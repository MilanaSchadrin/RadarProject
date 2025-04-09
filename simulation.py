from skyenv import SkyEnv
from databaseman import DatabaseManager

class Simulation:
    def __init__(self):
        self.dispatcher = None
        self.gui = None
        self.skyEnv = None
        self.CC = None
        self.CC_loc = (0,0,0)
        self.db = DatabaseManager()
        self.steps = 250
        self.set_dispatcher()
        self.set_GUI()
        self.set_units()

    def set_dispatcher(self):
        self.dispatcher = Dispatcher()

    def set_GUI(self):
        #start_page to StartPage
        self.gui = start_page(self.dispatcher)
        self.steps, self.CC_loc = self.gui.set_session_params(self.db)
    
    def set_units(self):
        self.skyEnv = SkyEnv(self.dispatcher)
        self.CC = ControlCenter(self.dispatcher, self.CC_loc)
        self.CC.start(self.db)
        self.skyEnv.start(self.db)
        
    def modulate(self):
        for i in range(self.steps):
            self.skyEnv.update()
            self.CC.update()
            self.gui.show()