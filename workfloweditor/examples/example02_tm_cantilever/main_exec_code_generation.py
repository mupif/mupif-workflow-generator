import sys
sys.path.append('../../..')
import field_to_vtk
import class_code
import workfloweditor
import workflowgenerator

if __name__ == '__main__':

    workflowgenerator.BlockWorkflow.BlockWorkflow.loadModelsFromGivenFile("class_code.py")
    workflowgenerator.BlockWorkflow.BlockWorkflow.loadModelsFromGivenFile("field_to_vtk.py")

    workflow = workflowgenerator.BlockWorkflow.BlockWorkflow()

    model_c_1 = class_code.MyProblemClassWorkflow()

    cfq1 = workflowgenerator.BlockConstPhysicalQuantity.BlockConstPhysicalQuantity()
    cfq1.setValue(0.)
    cfq1.setUnits('s')
    workflow.addBlock(cfq1)

    cfq2 = workflowgenerator.BlockConstPhysicalQuantity.BlockConstPhysicalQuantity()
    cfq2.setValue(10.)
    cfq2.setUnits('s')
    workflow.addBlock(cfq2)

    cfq3 = workflowgenerator.BlockConstPhysicalQuantity.BlockConstPhysicalQuantity()
    cfq3.setValue(0.5)
    cfq3.setUnits('s')
    workflow.addBlock(cfq3)

    property1 = workflowgenerator.BlockConstProperty.BlockConstProperty()
    property1.setValue((10.,))
    property1.setPropertyID('mupif.PropertyID.PID_Temperature')
    property1.setValueType('mupif.ValueType.Scalar')
    property1.setUnits('degC')
    workflow.addBlock(property1)

    timeloop = workflowgenerator.BlockTimeloop.BlockTimeloop()

    model1 = workflowgenerator.BlockModel.BlockModel(model_c_1)
    model1.constructFromModelMetaData()
    timeloop.addBlock(model1)

    export_class = field_to_vtk.field_export_to_VTK()

    export_block1 = workflowgenerator.BlockModel.BlockModel(export_class)
    export_block1.constructFromModelMetaData()
    timeloop.addBlock(export_block1)

    export_block2 = workflowgenerator.BlockModel.BlockModel(export_class)
    export_block2.constructFromModelMetaData()
    timeloop.addBlock(export_block2)

    workflow.addBlock(timeloop)

    cfq1.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("start_time"))
    cfq2.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("target_time"))
    cfq3.getDataSlotWithName("value").connectTo(timeloop.getDataSlotWithName("max_dt"))

    model1.getDataSlotWithName("temperature temperature").connectTo(export_block1.getDataSlotWithName("field"))
    model1.getDataSlotWithName("displacement displacement").connectTo(export_block2.getDataSlotWithName("field"))
    model1.getDataSlotWithName("top_temperature top_temperature").connectTo(property1.getDataSlotWithName("value"))

    print("\nWorkflowStructure:")
    workflow.printStructure()
    print("")

    #

    application = workfloweditor.Application.Application(workflow)
    application.window.setGeometry(400, 200, 450, 900)
    application.generateAll()

    for block in application.getWorkflowBlock().getBlocks():
        print(block)

    application.run()
