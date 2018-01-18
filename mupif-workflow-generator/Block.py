#
#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2015 Borek Patzak
#
#    Czech Technical University, Faculty of Civil Engineering,
#  Department of Structural Mechanics, 166 29 Prague, Czech Republic
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor,
# Boston, MA  02110-1301  USA
#

"""
 data structure for workflow editor

 The execution model is based on idea of combining ExecucutionBlocks
 Each block represents specific action or procedure and it is responsible
 for generating its code.
 The execution blocks can be composed/contain other blocks
 (an example is a time loop block, which contains blocks to be executed
  within a time loop)
 Each execution block can define its input and output slots, basically
 representing input and output parameters of particular block.
 The input/output slots can be connected using DataLink objects.

"""

#
# Data model
#
#
class DataProvider:
    def __init__(self):
        """Constructor"""
    def get (self, slot=None):
        """Returns the value associated with DataSlot"""
        return None
    def getOutputSlots(self):
        """Returns a list of output DataSlots"""
        return []

class DataConsumer:
    def __init__(self):
        """Constructor"""
    def set (self, value, slot=None):
        """sets the value associated with DataSlot"""
        return
    def getInputSlots(self):
        """Returns list of input DataSlots"""
        return []

class DataSlot:
    """
    Class describing input/output parameter of block
    """
    def __init__ (self, owner, name, type, optional=False):
        self.name = name
        self.owner = owner
        self.type = type
        self.optional = optional
    def __repr__(self):
        return "DataSlot (%s.%s %s)"%(self.owner.name, self.name, self.type)

class DataLink:
    """
    Represents a connection between source and receiver DataSlots
    """
    def __init__(self, input, output):
        self.input = input # DataProvider slot
        self.output = output # DataConsumer slot
    def __str__(self):
        return "Datalink (%s -> %s)"%(self.input.name, self.output.name)
    def __repr__(self):
        return self.__str__()


#
# Execution model
#
class ExecutionBlock (DataProvider, DataConsumer):
    """
    Abstract class representing execution block
    """
    def __init__ (self, workflow):
        self.blockList = []
        self.variables = {}
        self.workflow = workflow
        self.name = "ExecutionBlock"

    def setVariable(self, name, value):
        """Sets block variable"""
    def generateInitCode(self):
        """Generate initialization block code"""

    def generateCode(self):
        """returns tuple containing strings with code lines"""
        return ["block_execution"]

    def generateBlockInputs(self):
        inputLinks = self.workflow.getExecutionBlockDataLinks(self,mode="in")
        #print (inputLinks)
        inputSlots = self.getInputSlots()
        code = []
        # generate input code for each block input
        for iSlot in inputSlots:
            #print (iSlot)
            # try to locate corresponding dataLink
            iLink = [l for l in inputLinks if l.output.owner == self]
            #print (iLink)
            if (len(iLink)==0 and iSlot.optional==False):
                #raise AttributeError("No input link for slot detected")
                code.append("# No input for slot %s detected"%(iSlot.name))
            elif (len(iLink) > 1):
                raise AttributeError("Multiple input links for slot detected")
            else:
                source = iLink[0].input
                code.append("%s.set(name=%s, value=%s)" % (self.name,iSlot.name, source))
        return code


#
# Execution blocks: Implementation
#

class SequentialBlock (ExecutionBlock):
    """
    Implementation of sequential processing block
    """
    def __init__(self, workflow):
        ExecutionBlock.__init__(self, workflow)

    def generateCode(self):
        code = ["# Generating code for %s"%self.name]
        for iblock in self.blockList:
            code.append("# Generating code for %s"%(iblock.name))
            code.extend(iblock.generateBlockInputs()) # inputs generated based on block requirements
            code.extend(iblock.generateCode())
        return code


class WorkflowBlock (SequentialBlock):
    def __init__(self):
        ExecutionBlock.__init__(self, self)
        self.dataLinks=[] # data links (global in workflow)
        self.name="WorkflowBlock"

    def getExecutionBlockDataLinks (self, block, mode=""):
        answer = []
        for iLink in self.dataLinks:
            if ((mode=="in" or mode=="") and (iLink.output.owner == block)): #link output is block input
                answer.append(iLink)
            elif ((mode=="out" or mode=="") and (iLink.input.owner == block)): #link input is block output
                     answer.append(iLink)
        return answer
        body = SequentialBlock.generateCode(self)
        #print (body)
        for i in body:
            icode=i
            whilecode.append(icode) # indented sequential code


class ModelBlock(ExecutionBlock):
    def __init__(self, workflow, model, modelName):
        ExecutionBlock.__init__(self, workflow)
        self.model = model
        self.name=modelName

    def getInputSlots(self):
        return self.model.getInputSlots()
    def getOutputSlots(self):
        return self.model.getOutputSlots()
    def generateCode(self):
        return ["%s.solveStep(tstep)"%self.name]

class TimeLoopBlock (SequentialBlock):
    def __init__(self, workflow):
     SequentialBlock.__init__(self, workflow)
     self.dataSlots = [DataSlot(self, "target_time", float, False),
                       DataSlot(self, "start_time", float, False)]
     self.name="TimeLoopBlock"

    def getInputSlots(self):
        return self.dataSlots

    def setVariable(self, name, value):
                     self.variables[name]=value

    def generateCode(self):
        code = ["time=%(start_time)f"%self.variables,
                "while (time<=%(target_time)f):"%self.variables]
        whilecode=[]
        dtcode = "deltaT = min("
        for i in  self.blockList:
            if (isinstance(i, ModelBlock)):
                dtcode+=("%s.getCriticalTimeStep()"%(i.name))
        dtcode+=")"
        whilecode.append(dtcode)
        whilecode.extend(SequentialBlock.generateCode(self))
        whilecode.append("time=min(time+deltaT, target_time)")

        code.append(whilecode)
        code.append("")

        return code
