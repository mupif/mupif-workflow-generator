import sys
# custom for each user
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
from Application import *

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

if __name__ == '__main__':
    application = Application()

    workflow = WorkflowBlock(application.window.widget.scene)
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

    application.window.widget.addNode(workflow)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    var1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    var2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    application.run()

