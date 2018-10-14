"""Window class."""
import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import DataLink
import Block
import Window
import GraphWidget


class Application():

    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.window = Window.Window()

    def run(self):
        sys.exit(self.app.exec_())

    def exit(self):
        sys.exit()
