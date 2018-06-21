# import PyQt5
# from PyQt5 import QtGui
# from PyQt5 import QtCore
from PyQt5 import QtWidgets

import sys

#
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
import Block
import GraphWidget


class ModelA(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "HeatSolver")
        self.addDataSlot(Block.OutputDataSlot(self, "temperatureField", "field"))


class ModelB(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "MechanicalSolver")
        self.addDataSlot(Block.InputDataSlot(self, "temperatureField", "field"))
        self.addDataSlot(Block.OutputDataSlot(self, "DisplacementField", "field"))


def printCode (code, level=-1):
    if isinstance(code, str):
        print ("%s%s" % ('\t'*level, code))
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
    graph.setGeometry(100, 100, 800, 600)
    graph.show()

    workflow = Block.WorkflowBlock()
    model1 = ModelA(workflow)
    model2 = ModelB(workflow)

    timeloop = Block.TimeLoopBlock(workflow)

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.setVariable("start_time", 0.0)
    timeloop.setVariable("target_time", 1.0)
    # workflow.dataLinks.append(Block.DataLink(model1.dataSlots[0], model2.dataSlots[0]))

    workflow.addExecutionBlock(timeloop)
    graph.addNode(workflow)
    # model1.getDataSlotWithName("temperatureField").connectTo(model2.getDataSlotWithName("temperatureField"))

    code = workflow.generateCode()

    # print code
    printCode(code)

    # graph.registerNodeClass(Integer)
    # nodeInt1 = Integer()
    print(graph.scene.items())
    for i in list(graph.scene.items()):
        print(i.scene())
    # graph.addNode(nodeInt1)

    app.exec_()


if __name__ == '__main__':
    test()
