
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
from start_page import start_page
from map_window import MapWindow

app = QApplication(sys.argv)
ex=start_page()
ex.show()
sys.exit(app.exec_())
