# import PyQt5
# from PyQt5 import QtGui
# from PyQt5 import QtCore
from PyQt5 import QtWidgets

import sys

# custom for each user
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
from Block import *
import GraphWidget


class FireDynamicSimulator(ModelBlock):
    def __init__(self, workflow):
        ModelBlock.__init__(self, workflow, None, "FireDynamicsSimulator")
        self.addDataSlot(OutputDataSlot(self, "ASTField", "field"))


ExecutionBlock.list_of_models.append(FireDynamicSimulator)


class HeatSolver(ModelBlock):
    def __init__(self, workflow):
        ModelBlock.__init__(self, workflow, None, "HeatSolver")
        self.addDataSlot(InputDataSlot(self, "ASTField", "field"))
        self.addDataSlot(OutputDataSlot(self, "TemperatureField", "field"))


ExecutionBlock.list_of_models.append(HeatSolver)


class MechanicalSolver(ModelBlock):
    def __init__(self, workflow):
        ModelBlock.__init__(self, workflow, None, "MechanicalSolver")
        self.addDataSlot(InputDataSlot(self, "TemperatureField", "field"))
        self.addDataSlot(OutputDataSlot(self, "DisplacementField", "field"))


ExecutionBlock.list_of_models.append(MechanicalSolver)


def printCode (code, level=-1):
    if isinstance(code, str):
        print("%s%s" % ('\t'*level, code))
    else:
        for line in code:
            printCode(line, level+1)


#
# here we set up the workflow model directly
# the other possibility is to create workflow model from file (json)
# (not yet available)
#
def test():
    app = QtWidgets.QApplication([])
    graph = GraphWidget.GraphWidget()
    graph.setGeometry(100, 100, 1000, 600)
    graph.show()




    app.exec_()


if __name__ == '__main__':
    test()
