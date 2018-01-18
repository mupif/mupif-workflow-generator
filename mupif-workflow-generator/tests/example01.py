import Block
import collections

class ModelA(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None, "HeatSolver")
        self.outputSlots = [Block.DataSlot(self, "temperatureField", "field")]

    def getInputSlots(self):
        return []
    def getOutputSlots(self):
        return self.outputSlots

class ModelB(Block.ModelBlock):
    def __init__(self, workflow):
        Block.ModelBlock.__init__(self, workflow, None,"MechanicalSolver")
        self.inputSlots = [Block.DataSlot(self, "temperatureField", "field")]
        self.outputSlots = [Block.DataSlot(self, "DisplacementField", "field")]


    def getInputSlots(self):
        return self.inputSlots
    def getOutputSlots(self):
        return self.outputSlots

def printCode (code, level=-1):
    if isinstance(code, basestring):
        print ("%s%s"%('\t'*level, code))
    else:
        for line in code:
            printCode (line, level+1)


#
# here we set up the workflow model directly
# the other posibility is to create workflow model from file (json)
# (not yet available)
#
workflow = Block.WorkflowBlock()
model1 = ModelA(workflow)
model2 = ModelB(workflow)


timeloop = Block.TimeLoopBlock(workflow)

timeloop.blockList.append(model1)
timeloop.blockList.append(model2)
timeloop.setVariable("start_time", 0.0)
timeloop.setVariable("target_time", 1.0)
workflow.dataLinks.append(Block.DataLink(model1.outputSlots[0], model2.inputSlots[0]))

workflow.blockList.append(timeloop)
code = workflow.generateCode()

#print code
printCode(code)
