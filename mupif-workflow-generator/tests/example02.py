from example01_models import *
from Application import *

if __name__ == '__main__':

    application = Application()
    workflow = application.getWorkflowBlock()

    var1 = VariableBlock(workflow, workflow)
    var1.setValue(0.5)
    workflow.addExecutionBlock(var1)

    var2 = VariableBlock(workflow, workflow)
    var2.setValue(10.0)
    workflow.addExecutionBlock(var2)

    timeloop = TimeLoopBlock(workflow, workflow)

    model_c_1 = FireDynamicsSimulator()
    model_c_2 = HeatSolver()
    model_c_3 = MechanicalSolver()

    model1 = ModelBlock(timeloop, workflow)
    model1.constructFromMetaData(model_c_1.getMetaData())
    model2 = ModelBlock(timeloop, workflow)
    model2.constructFromMetaData(model_c_2.getMetaData())
    model3 = ModelBlock(timeloop, workflow)
    model3.constructFromMetaData(model_c_3.getMetaData())

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.addExecutionBlock(model3)

    workflow.addExecutionBlock(timeloop)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    # var1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    # var2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    application.run()

