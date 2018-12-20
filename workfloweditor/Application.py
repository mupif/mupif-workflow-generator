"""Application class."""
from .Window import *
from .GraphWidget import *


class Application:

    def __init__(self):
        self.app = QtWidgets.QApplication([])
        self.window = Window(self)

    def run(self):
        sys.exit(self.app.exec())

    def exit(self):
        sys.exit()

    def addWorkflow(self):
        return self.window.widget.addWorkflowBlock()

    def getWorkflowBlock(self):
        return self.window.widget.getWorkflowBlock()
