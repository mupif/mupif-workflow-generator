import models
import mupif
import workfloweditor

if __name__ == '__main__':
    workfloweditor.Block.ModelBlock.loadModelsFromGivenFile("models.py")

    application = workfloweditor.Application.Application()
    application.window.setGeometry(400, 200, 500, 1020)

    workflow = application.getWorkflowBlock()

    workflow.addDataSlot(workfloweditor.DataLink.ExternalInputDataSlot(workflow, 'temperature', workfloweditor.DataLink.DataSlotType.Field))
    workflow.addDataSlot(workfloweditor.DataLink.ExternalInputDataSlot(workflow, 'displacement', workfloweditor.DataLink.DataSlotType.Field))
    workflow.addDataSlot(workfloweditor.DataLink.ExternalOutputDataSlot(workflow, 'top_temperature', workfloweditor.DataLink.DataSlotType.Property))

    property1 = workfloweditor.Block.ConstantPropertyBlock(workflow, workflow)
    property1.setValue((0.,))
    property1.setPropertyID(mupif.propertyID.PropertyID.PID_Temperature)
    property1.setValueType(mupif.ValueType.ValueType.Scalar)
    property1.setUnits('degC')
    workflow.addExecutionBlock(property1)

    property2 = workfloweditor.Block.ConstantPropertyBlock(workflow, workflow)
    property2.setValue((0.,))
    property2.setPropertyID(mupif.propertyID.PropertyID.PID_Temperature)
    property2.setValueType(mupif.ValueType.ValueType.Scalar)
    property2.setUnits('degC')
    workflow.addExecutionBlock(property2)

    model_c_2 = models.thermal_nonstat()
    model_c_3 = models.mechanical()

    model1 = workfloweditor.Block.ModelBlock(workflow, workflow)
    model1.constructFromModelMetaData(model_c_2)
    model1.setInputFile('inputT13.in')
    workflow.addExecutionBlock(model1)

    model2 = workfloweditor.Block.ModelBlock(workflow, workflow)
    model2.constructFromModelMetaData(model_c_3)
    model2.setInputFile('inputM13.in')
    workflow.addExecutionBlock(model2)

    model1.getDataSlotWithName('temperature').connectTo(model2.getDataSlotWithName('temperature'))

    model1.getDataSlotWithName('top edge temperature convection').connectTo(
        workflow.getDataSlotWithName('top_temperature'))
    model1.getDataSlotWithName('bottom edge temperature Dirichlet').connectTo(
        property1.getDataSlotWithName('value'))
    model1.getDataSlotWithName('left edge temperature Dirichlet').connectTo(
        property2.getDataSlotWithName('value'))

    model1.getDataSlotWithName('temperature').connectTo(workflow.getDataSlotWithName('temperature'))
    model2.getDataSlotWithName('displacement').connectTo(workflow.getDataSlotWithName('displacement'))

    application.run()

