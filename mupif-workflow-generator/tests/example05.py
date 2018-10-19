import sys
# custom for each user
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
from Application import *


class FireDynamicSimulator(ModelBlock):
    def __init__(self, parent, workflow):
        ModelBlock.__init__(self, parent, workflow, None, "FireDynamicsSimulator")
        self.addDataSlot(OutputDataSlot(self, "ASTField", "field"))


ExecutionBlock.list_of_models.append(FireDynamicSimulator)


class HeatSolver(ModelBlock):
    def __init__(self, parent, workflow):
        ModelBlock.__init__(self, parent, workflow, None, "HeatSolver")
        self.addDataSlot(InputDataSlot(self, "ASTField", "field"))
        self.addDataSlot(OutputDataSlot(self, "TemperatureField", "field"))


ExecutionBlock.list_of_models.append(HeatSolver)


class MechanicalSolver(ModelBlock):
    def __init__(self, parent, workflow):
        ModelBlock.__init__(self, parent, workflow, None, "MechanicalSolver")
        self.addDataSlot(InputDataSlot(self, "TemperatureField", "field"))
        self.addDataSlot(OutputDataSlot(self, "DisplacementField", "field"))


ExecutionBlock.list_of_models.append(MechanicalSolver)

if __name__ == '__main__':

    application = Application()

    # workflow = WorkflowBlock(None, application.window.widget.scene)
    # workflow = application.window.widget.addWorkflowBlock()
    workflow = application.getWorkflowBlock()

    var1 = VariableBlock(workflow, workflow)
    var1.setValue(0.5)
    workflow.addExecutionBlock(var1)

    var2 = VariableBlock(workflow, workflow)
    var2.setValue(10.0)
    workflow.addExecutionBlock(var2)

    timeloop = TimeLoopBlock(workflow, workflow)

    model1 = FireDynamicSimulator(timeloop, workflow)
    model2 = HeatSolver(timeloop, workflow)
    model3 = MechanicalSolver(timeloop, workflow)

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.addExecutionBlock(model3)

    workflow.addExecutionBlock(timeloop)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    # var1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    # var2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    application.run()

