from simulation import Simulation
from PyQt5.QtWidgets import QApplication
import sys

if __name__=="__main__":
    app = QApplication(sys.argv)
    sim = Simulation()
    sim.modulate()
    sys.exit(app.exec_())