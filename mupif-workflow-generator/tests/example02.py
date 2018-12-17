from example02_models import *
from Application import *

if __name__ == '__main__':

    ModelBlock.loadModelsFromGivenFile("example02_models.py")

    application = Application()
    workflow = application.getWorkflowBlock()

    cfq1 = ConstantPhysicalQuantityBlock(workflow, workflow)
    cfq1.setValue(0.)
    cfq1.setUnits('s')
    workflow.addExecutionBlock(cfq1)

    cfq2 = ConstantPhysicalQuantityBlock(workflow, workflow)
    cfq2.setValue(5.)
    cfq2.setUnits('s')
    workflow.addExecutionBlock(cfq2)

    timeloop = TimeLoopBlock(workflow, workflow)

    model_c_1 = FireDynamicsSimulator()
    model_c_2 = HeatSolver()
    model_c_3 = MechanicalSolver()

    model1 = ModelBlock(timeloop, workflow)
    model1.constructFromModelMetaData(model_c_1)
    model2 = ModelBlock(timeloop, workflow)
    model2.constructFromModelMetaData(model_c_2)
    model3 = ModelBlock(timeloop, workflow)
    model3.constructFromModelMetaData(model_c_3)

    timeloop.addExecutionBlock(model1)
    timeloop.addExecutionBlock(model2)
    timeloop.addExecutionBlock(model3)

    workflow.addExecutionBlock(timeloop)

    model1.getDataSlotWithName("ASTField").connectTo(model2.getDataSlotWithName("ASTField"))
    model2.getDataSlotWithName("TemperatureField").connectTo(model3.getDataSlotWithName("TemperatureField"))
    cfq1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    cfq2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))

    application.run()

