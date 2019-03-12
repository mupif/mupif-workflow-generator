import models
import mupif
import sys
sys.path.append('../../..')
import workfloweditor
import workflowgenerator

if __name__ == '__main__':

    workflowgenerator.BlockWorkflow.BlockWorkflow.loadModelsFromGivenFile("models.py")

    workflow = workflowgenerator.BlockWorkflow.BlockWorkflow()

    workflow.addDataSlot(
        workflowgenerator.DataSlot.ExternalInputDataSlot('temperature', workflowgenerator.DataSlot.DataSlotType.Field))
    workflow.addDataSlot(
        workflowgenerator.DataSlot.ExternalInputDataSlot('displacement', workflowgenerator.DataSlot.DataSlotType.Field))
    workflow.addDataSlot(workflowgenerator.DataSlot.ExternalOutputDataSlot('top_temperature',
                                                                           workflowgenerator.DataSlot.DataSlotType.Property))

    property1 = workflowgenerator.BlockConstProperty.BlockConstProperty()
    property1.setValue((0.,))
    property1.setPropertyID(mupif.PropertyID.PID_Temperature)
    property1.setValueType(mupif.ValueType.Scalar)
    property1.setUnits('degC')
    workflow.addBlock(property1)

    property2 = workflowgenerator.BlockConstProperty.BlockConstProperty()
    property2.setValue((0.,))
    property2.setPropertyID(mupif.PropertyID.PID_Temperature)
    property2.setValueType(mupif.ValueType.Scalar)
    property2.setUnits('degC')
    workflow.addBlock(property2)

    model_c_2 = models.thermal_nonstat()
    model_c_3 = models.mechanical()

    model1 = workflowgenerator.BlockModel.BlockModel(model_c_2)
    model1.constructFromModelMetaData()
    model1.setInputFile('inputT13.in')
    workflow.addBlock(model1)

    model2 = workflowgenerator.BlockModel.BlockModel(model_c_3)
    model2.constructFromModelMetaData()
    model2.setInputFile('inputM13.in')
    workflow.addBlock(model2)

    model1.getDataSlotWithName('temperature').connectTo(model2.getDataSlotWithName('temperature'))
    model1.getDataSlotWithName('temperature').connectTo(workflow.getDataSlotWithName('temperature'))
    model2.getDataSlotWithName('displacement').connectTo(workflow.getDataSlotWithName('displacement'))

    model1.getDataSlotWithName('top edge temperature Cauchy').connectTo(
        workflow.getDataSlotWithName('top_temperature'))

    model1.getDataSlotWithName('bottom edge temperature Dirichlet').connectTo(
        property1.getDataSlotWithName('value'))
    model1.getDataSlotWithName('left edge temperature Dirichlet').connectTo(
        property2.getDataSlotWithName('value'))

    print("\nWorkflowStructure:")
    workflow.printStructure()
    print("")

    #

    application = workfloweditor.Application.Application(workflow)
    application.window.setGeometry(400, 200, 450, 850)
    application.generateAll()

    for block in application.getWorkflowBlock().getBlocks():
        print(block)

    application.run()
