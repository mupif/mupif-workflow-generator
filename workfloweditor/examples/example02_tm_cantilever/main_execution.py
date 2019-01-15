import sys
sys.path.append('../..')
import class_code
import field_to_vtk
import workfloweditor
import mupif

if __name__ == '__main__':
    workfloweditor.Block.ModelBlock.loadModelsFromGivenFile("class_code.py")
    workfloweditor.Block.ModelBlock.loadModelsFromGivenFile("field_to_vtk.py")

    application = workfloweditor.Application.Application()
    application.window.setGeometry(400, 200, 420, 1020)

    workflow = application.getWorkflowBlock()

    model_c_4 = class_code.MyProblemClassWorkflow()

    cfq1 = workfloweditor.Block.ConstantPhysicalQuantityBlock(workflow, workflow)
    cfq1.setValue(0.)
    cfq1.setUnits('s')
    workflow.addExecutionBlock(cfq1)

    cfq2 = workfloweditor.Block.ConstantPhysicalQuantityBlock(workflow, workflow)
    cfq2.setValue(10.)
    cfq2.setUnits('s')
    workflow.addExecutionBlock(cfq2)

    cfq3 = workfloweditor.Block.ConstantPhysicalQuantityBlock(workflow, workflow)
    cfq3.setValue(0.5)
    cfq3.setUnits('s')
    workflow.addExecutionBlock(cfq3)

    property1 = workfloweditor.Block.ConstantPropertyBlock(workflow, workflow)
    property1.setValue((10.,))
    property1.setPropertyID(mupif.propertyID.PropertyID.PID_Temperature)
    property1.setValueType(mupif.ValueType.ValueType.Scalar)
    property1.setUnits('degC')
    workflow.addExecutionBlock(property1)

    timeloop = workfloweditor.Block.TimeLoopBlock(workflow, workflow)

    model4 = workfloweditor.Block.ModelBlock(timeloop, workflow)
    model4.constructFromModelMetaData(model_c_4)
    timeloop.addExecutionBlock(model4)

    export_class = field_to_vtk.field_export_to_VTK()

    export_block1 = workfloweditor.Block.ModelBlock(timeloop, workflow)
    export_block1.constructFromModelMetaData(export_class)
    timeloop.addExecutionBlock(export_block1)

    export_block2 = workfloweditor.Block.ModelBlock(timeloop, workflow)
    export_block2.constructFromModelMetaData(export_class)
    timeloop.addExecutionBlock(export_block2)

    workflow.addExecutionBlock(timeloop)

    cfq1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    cfq2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))
    cfq3.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("max_dt"))

    model4.getDataSlotWithName("temperature").connectTo(export_block1.getDataSlotWithName("field"))
    model4.getDataSlotWithName("displacement").connectTo(export_block2.getDataSlotWithName("field"))
    model4.getDataSlotWithName("top_temperature").connectTo(property1.getDataSlotWithName("value"))

    application.run()

