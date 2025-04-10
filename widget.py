from dispatcher import Dispatcher
#from messages import SEStarting
#from messages import Message
#import enums
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from start_page import start_page
from map_window import MapWindow

disp=Dispatcher()
app = QApplication(sys.argv)

ex=start_page(disp)
#ex.show()
sys.exit(app.exec_())
