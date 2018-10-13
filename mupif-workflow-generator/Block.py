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


from SequentialBlock import *


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


def printCode(code, level=-1):
    if isinstance(code, str):
        print("%s%s" % ('\t'*level, code))
    else:
        for line in code:
            printCode(line, level+1)


class WorkflowBlock(SequentialBlock):
    def __init__(self, loc_scene):
        self.loc_scene = loc_scene
        SequentialBlock.__init__(self, self)
        self.name = "WorkflowBlock"
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)

    def getScene(self):
        return self.loc_scene

    def getExecutionBlockDataLinks(self, block, mode=""):
        answer = []
        for iLink in self.dataLinks:
            if (mode == "in" or mode == "") and (iLink.output.owner == block):  # link output is block input
                answer.append(iLink)
            elif (mode == "out" or mode == "") and (iLink.input.owner == block):  # link input is block output
                answer.append(iLink)
        return answer
        body = SequentialBlock.generateCode(self)
        # print (body)
        for i in body:
            i_code = i
            while_code.append(i_code)  # indented sequential code

    def addAddBlockMenuActions(self, menu):

        def _updateChildrenPosition():
            self.updateChildrenPosition()
            self.updateDataLinksPath()

        new_action = menu.addAction("Update position of child blocks")
        new_action.triggered.connect(_updateChildrenPosition)

        sub_menu = menu.addMenu("Add")

        def _addTimeLoopBlock():
            new_time_loop_block = TimeLoopBlock(self)
            self.addExecutionBlock(new_time_loop_block)

        add_time_loop_block_action = sub_menu.addAction("TimeLoop Block")
        add_time_loop_block_action.triggered.connect(_addTimeLoopBlock)

        def _addVariableBlock():
            new_block = VariableBlock(self.workflow)
            self.addExecutionBlock(new_block)

        add_variable_block_action = sub_menu.addAction("Variable")
        add_variable_block_action.triggered.connect(_addVariableBlock)

        def _generateCode():
            code = self.generateCode()
            print()
            print()
            print()
            printCode(code)
            print()
            print()
            print()

        addGenerateCodeAction = menu.addAction("Generate code")
        addGenerateCodeAction.triggered.connect(_generateCode)

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addAddBlockMenuActions(menu)
        self.addShowHideMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())


class VariableBlock(ExecutionBlock):
    def __init__(self, workflow):
        ExecutionBlock.__init__(self, workflow)
        self.value = 0.
        self.addDataSlot(OutputDataSlot(self, "value", float, False))
        self.getDataSlots()[0].displayName = "%le" % self.value

    def addVariableBlockMenuActions(self, menu):
        sub_menu = menu.addMenu("Modify")

        def _changeValue():
            temp = QtWidgets.QInputDialog()
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter new value", "New value")
            if ok_pressed:
                self.value = float(new_value)
                self.getDataSlots()[0].displayName = "%le" % self.value

        change_value_action = sub_menu.addAction("Change value")
        change_value_action.triggered.connect(_changeValue)

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addVariableBlockMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.value = val
        self.getDataSlots()[0].displayName = "%le" % self.value


class ModelBlock(ExecutionBlock):
    def __init__(self, workflow, model, model_name):
        ExecutionBlock.__init__(self, workflow)
        self.model = model
        self.name = model_name

    def getInputSlots(self):
        return self.model.getInputSlots()

    def getOutputSlots(self):
        return self.model.getOutputSlots()

    def generateCode(self):
        return ["%s.solveStep(tstep)" % self.name]


class TimeLoopBlock(SequentialBlock):
    def __init__(self, workflow):
        SequentialBlock.__init__(self, workflow)
        self.addDataSlot(InputDataSlot(self, "start_time", float, False))
        self.addDataSlot(InputDataSlot(self, "target_time", float, False))

    def getStartTime(self):
        if len(self.getDataSlotWithName("start_time").dataLinks):
            this_slot = self.getDataSlotWithName("start_time")
            connected_block = this_slot.dataLinks[0].giveTheOtherSlot(this_slot).owner
            if type(connected_block).__name__ == "VariableBlock":
                return connected_block.getValue()
        return 0

    def getTargetTime(self):
        if len(self.getDataSlotWithName("target_time").dataLinks):
            this_slot = self.getDataSlotWithName("target_time")
            connected_block = this_slot.dataLinks[0].giveTheOtherSlot(this_slot).owner
            if type(connected_block).__name__ == "VariableBlock":
                return connected_block.getValue()
        return 0

    def setVariable(self, name, value):
        self.variables[name] = value

    def generateCode(self):
        code = ["time=%f" % self.getStartTime(),
                "while (time<=%f):" % self.getTargetTime()]
        while_code = []
        dt_code = "deltaT = min("
        for i in self.getChildExecutionBlocks():
            if isinstance(i, ModelBlock):
                dt_code += ("%s.getCriticalTimeStep()" % i.name)
        dt_code += ")"
        while_code.append(dt_code)
        while_code.extend(SequentialBlock.generateCode(self))
        while_code.append("time=min(time+deltaT, target_time)")

        code.append(while_code)
        code.append("")

        return code

    def addAddBlockMenuActions(self, menu):
        sub_menu = menu.addMenu("Add")

        def _addModelBlock(idx):
            new_block = ExecutionBlock.list_of_models[idx](self.workflow)
            self.addExecutionBlock(new_block)

        idx = 0
        for model in ExecutionBlock.list_of_models:
            add_model_block_action = sub_menu.addAction(model.__name__)
            add_model_block_action.triggered.connect(lambda checked, idx=idx: _addModelBlock(idx))
            idx += 1

    def addChildBlocksMenuActions(self, menu):
        sub_menu = menu.addMenu("Child blocks")

        temp_child_blocks = self.getChildExecutionBlocks()
        block_id = 0
        for block in temp_child_blocks:
            block_id += 1
            sub_sub_menu = sub_menu.addMenu("%d) %s" % (block_id, block.name))
            add_action = sub_sub_menu.addAction("delete")
            sub_sub_sub_menu = sub_sub_menu.addMenu("move")

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addAddBlockMenuActions(menu)
        self.addShowHideMenuActions(menu)
        self.addChildBlocksMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())


