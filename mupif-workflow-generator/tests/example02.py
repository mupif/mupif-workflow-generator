# import PyQt5
# from PyQt5 import QtGui
# from PyQt5 import QtCore
from PyQt5 import QtWidgets

import sys

# custom for each user
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
import Block
import GraphWidget


class ModelA(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "HeatSolver")


class ModelB(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "MechanicalSolver")


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
    graph.setGeometry(100, 100, 800, 600)
    graph.show()


    print(graph.scene.items())
    for i in list(graph.scene.items()):
        print(i.scene())
    # graph.addNode(nodeInt1)

    app.exec_()


if __name__ == '__main__':
    test()
