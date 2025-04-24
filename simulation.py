from skyenv.skyenv import SkyEnv
from controlcenter.ControlCenter import ControlCenter
from dispatcher.dispatcher import Dispatcher
from vizualization.start_page import StartPage
from database.databaseman import DatabaseManager
from PyQt5.QtWidgets import QApplication
import sys

class Simulation:
    def __init__(self):
        self.dispatcher = None
        self.gui = None
        self.skyEnv = None
        self.CC = None
        self.data_colector=None
        self.db = DatabaseManager()
        self.steps = 250
        self.app = QApplication(sys.argv)
        self.set_dispatcher()
        self.set_GUI()

    def set_dispatcher(self):
        self.dispatcher = Dispatcher()

    def set_GUI(self):
        self.gui = StartPage(self.dispatcher,self.app, self)
        expect_modules=['Радиолокатор', 'ПУ', 'ПБУ', 'ВО']
        self.gui.set_params_callback(self.on_params_ready, expect_modules)
        self.gui.set_session_params(self.db)
        self.gui.steps_input.editingFinished.connect(self.on_step)
        self.gui.db_name_input.editingFinished.connect(self.on_name)

    def on_step(self):
        self.steps = self.gui.get_step()

    def on_name(self):
        self.name = self.gui.get_db_name()
        
    def on_params_ready(self, params):
        self.gui.set_session_params(self.db)
    
    def set_units(self):
        self.skyEnv = SkyEnv(self.dispatcher,self.steps)
        self.CC = ControlCenter(self.dispatcher, self.db.load_cc(), self.steps)
        self.CC.start(self.db)#send_done()
        self.skyEnv.start(self.db)#send_done)

        #while dispatcher.get_done!=2:
        #wait
        #main window
        
    def modulate(self,progress_callback):
        print('Начало моделирования')
        for i in range(self.steps):
            #print('Шаг моделирования', i)
            self.data_colector.begin_step(i)
            self.skyEnv.update()
            self.CC.update()
            self.data_colector.collect_messages()
            self.gui.update()
            if progress_callback:
                progress_callback(i+1)
                QApplication.processEvents()
            #self.app.exec_()#передовать и вызывать в update у тебя
            
    def run(self):
        self.app.exec_()
        