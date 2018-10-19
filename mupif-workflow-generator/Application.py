"""Window class."""
import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from DataLink import *
from Block import *
from Window import *
from GraphWidget import *


class Application:

    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.window = Window(self)

    def run(self):
        sys.exit(self.app.exec_())

    def exit(self):
        sys.exit()

    def addWorkflow(self):
        return self.window.widget.addWorkflowBlock()

    def getWorkflowBlock(self):
        return self.window.widget.getWorkflowBlock()
