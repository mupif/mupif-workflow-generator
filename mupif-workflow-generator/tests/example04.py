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


def printCode(code, level=-1):
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
    graph.setGeometry(100, 100, 800, 800)

    workflow = WorkflowBlock(graph.scene)
    model1 = FireDynamicSimulator(workflow)
    model2 = HeatSolver(workflow)
    model3 = MechanicalSolver(workflow)

    timeloop = TimeLoopBlock(workflow)

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.addExecutionBlock(model3)

    var1 = VariableBlock(workflow)
    var1.setValue(0.5)
    workflow.addExecutionBlock(var1)

    var2 = VariableBlock(workflow)
    var2.setValue(10.0)
    workflow.addExecutionBlock(var2)

    workflow.addExecutionBlock(timeloop)

    workflow.resizeForChildren()
    graph.addNode(workflow)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    var1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    var2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    code = workflow.generateCode()

    graph.show()
    # workflow.updateChildrenPosition()

    # print code
    printCode(code)

    # graph.registerNodeClass(Integer)
    # nodeInt1 = Integer()
    print(graph.scene.items())
    for i in list(graph.scene.items()):
        print(i.scene())
    # graph.addNode(nodeInt1)

    app.exec()


if __name__ == '__main__':
    test()
