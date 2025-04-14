from skyenv.skyenv import SkyEnv
from controlcenter.ControlCenter import ControlCenter
from dispatcher.dispatcher import Dispatcher
from vizualization.start_page import startPage
from database.databaseman import DatabaseManager
from PyQt5.QtWidgets import QApplication
import sys

class Simulation:
    def __init__(self):
        self.dispatcher = None
        self.gui = None
        self.skyEnv = None
        self.CC = None
        self.db = DatabaseManager()
        self.steps = 250
        self.app = QApplication(sys.argv)
        self.set_dispatcher()
        self.set_GUI()

    def set_dispatcher(self):
        self.dispatcher = Dispatcher()

    def set_GUI(self):
        self.gui = startPage(self.dispatcher,self.app, self)
        #self.steps = self.gui.set_session_params(self.db)
        #self.gui.set_session_params(self.db)
    
    def set_units(self):
        self.skyEnv = SkyEnv(self.dispatcher)
        self.CC = ControlCenter(self.dispatcher, self.db.load_cc())
        self.CC.start(self.db)#send_done()
        self.skyEnv.start(self.db)#send_done)

        #while dispatcher.get_done!=2:
        #wait
        #main window
        
    def modulate(self):
        print('Начало моделирования')
        for i in range(self.steps):
            print('Шаг моделирования', i)
            self.skyEnv.update()
            self.CC.update()
            self.gui.update()
            #self.app.exec_()#передовать и вызывать в update у тебя
            
    def run(self):
        self.app.exec_()
        