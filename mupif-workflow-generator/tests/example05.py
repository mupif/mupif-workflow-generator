import sys
# custom for each user
sys.path.insert(0, "/home/user/Projects/mupif-workflow-generator/mupif-workflow-generator")
from Application import *


class FireDynamicSimulator(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "FireDynamicsSimulator")
        self.addDataSlot(DataLink.OutputDataSlot(self, "ASTField", "field"))


Block.ExecutionBlock.list_of_models.append(FireDynamicSimulator)


class HeatSolver(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "HeatSolver")
        self.addDataSlot(DataLink.InputDataSlot(self, "ASTField", "field"))
        self.addDataSlot(DataLink.OutputDataSlot(self, "TemperatureField", "field"))


Block.ExecutionBlock.list_of_models.append(HeatSolver)


class MechanicalSolver(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "MechanicalSolver")
        self.addDataSlot(DataLink.InputDataSlot(self, "TemperatureField", "field"))
        self.addDataSlot(DataLink.OutputDataSlot(self, "DisplacementField", "field"))


Block.ExecutionBlock.list_of_models.append(MechanicalSolver)

if __name__ == '__main__':
    application = Application()

    workflow = Block.WorkflowBlock(application.window.widget.scene)
    model1 = FireDynamicSimulator(workflow)
    model2 = HeatSolver(workflow)
    model3 = MechanicalSolver(workflow)

    timeloop = Block.TimeLoopBlock(workflow)

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.addExecutionBlock(model3)

    var1 = Block.VariableBlock(workflow)
    var1.setValue(0.5)
    workflow.addExecutionBlock(var1)

    var2 = Block.VariableBlock(workflow)
    var2.setValue(10.0)
    workflow.addExecutionBlock(var2)

    workflow.addExecutionBlock(timeloop)

    workflow.resizeForChildren()
    application.window.widget.addNode(workflow)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    var1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    var2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    application.run()

