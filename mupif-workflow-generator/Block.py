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

from mupif import Application as mupifApplication
import inspect
import imp
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
    def __init__(self, parent, loc_scene):
        self.loc_scene = loc_scene
        SequentialBlock.__init__(self, parent, self)
        self.name = "WorkflowBlock"
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.widget = parent

    def getScene(self):
        return self.loc_scene

    def getAllDataLinks(self):
        answer = []
        for block in self.getChildExecutionBlocks(None, True):
            for datalink in block.getConnectedDataLinks():
                if datalink not in answer:
                    answer.append(datalink)
        return answer

    def addAddBlockMenuActions(self, menu):

        def _updateChildrenPosition():
            # self.updateChildrenPosition()
            self.updateChildrenSizeAndPositionAndResizeSelf()
            self.updateDataLinksPath()

        new_action = menu.addAction("Update position of child blocks")
        new_action.triggered.connect(_updateChildrenPosition)

        sub_menu = menu.addMenu("Add")

        def _addTimeLoopBlock():
            new_time_loop_block = TimeLoopBlock(self, self)
            self.addExecutionBlock(new_time_loop_block)

        add_time_loop_block_action = sub_menu.addAction("TimeLoop Block")
        add_time_loop_block_action.triggered.connect(_addTimeLoopBlock)

        def _addVariableBlock():
            new_block = VariableBlock(self, self.workflow)
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
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in WorkflowBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addAddBlockMenuActions(menu)
        menu.exec(QtGui.QCursor.pos())

    def convertDataLinksToJSON(self):
        return_json_array = []
        for datalink in self.getAllDataLinks():
            return_json_array.append(datalink.getDictForJSON())
        return return_json_array

    def convertToJSON(self):
        return_json_array = ExecutionBlock.convertToJSON(self)
        return_json_array.extend(self.convertDataLinksToJSON())
        return return_json_array

    def loadFromJSON(self, json_data):
        print("\n\n\nLoading workflow from JSON\n")
        for e in json_data['elements']:
            if e['classname'] == 'WorkflowBlock':
                self.uuid = e['uuid']
                break
        for e in json_data['elements']:
            print("importing %s" % e['classname'])

            if e['classname'] == 'TimeLoopBlock':
                new_e = TimeLoopBlock(None, self)
                new_e.uuid = e['uuid']
                e_parent_e = self.widget.getNodeById(e['parent_uuid'])
                new_e.parent = e_parent_e
                new_e.setParentItem(e_parent_e)

            if e['classname'] == 'VariableBlock':
                new_e = VariableBlock(None, self)
                new_e.uuid = e['uuid']
                e_parent_e = self.widget.getNodeById(e['parent_uuid'])
                new_e.parent = e_parent_e
                new_e.setParentItem(e_parent_e)
                new_e.setValue(e['value'])

            if e['classname'] == 'ModelBlock':
                model_found = False
                for model in ExecutionBlock.list_of_models:
                    if model.__name__ == e['model_classname']:
                        model_found = True
                        new_block_class = model()
                        new_e = ModelBlock(None, self)
                        new_e.constructFromModelMetaData(new_block_class)
                        new_e.uuid = e['uuid']
                        e_parent_e = self.widget.getNodeById(e['parent_uuid'])
                        new_e.parent = e_parent_e
                        new_e.setParentItem(e_parent_e)
                if not model_found:
                    print("MODEL CLASS NOT FOUND IN KNOWN MODELS")

            if e['classname'] == 'InputDataSlot' or e['classname'] == 'OutputDataSlot':
                ds = self.getDataSlot(parent_uuid=e['parent_uuid'], name=e['name'], recursive_search=True)
                if ds:
                    ds.setUUID(e['uuid'])

            if e['classname'] == 'DataLink':
                ds1 = self.getDataSlot(uuid=e['ds1_uuid'], recursive_search=True)
                ds2 = self.getDataSlot(uuid=e['ds2_uuid'], recursive_search=True)
                if ds1 and ds2:
                    if (isinstance(ds1, InputDataSlot) and isinstance(ds2, OutputDataSlot)) or (isinstance(ds1, OutputDataSlot) and isinstance(ds2, InputDataSlot)):
                        ds1.connectTo(ds2)

        self.updateChildrenSizeAndPositionAndResizeSelf()
        self.widget.view.redrawDataLinks()


class VariableBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.value = 0.
        self.addDataSlot(OutputDataSlot(self, "value", float, False))
        self.getDataSlots()[0].displayName = "%le" % self.value
        self.variable_name = ""

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
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in VariableBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addMoveMenuActions(menu)
        self.addDeleteMenuActions(menu)
        self.addVariableBlockMenuActions(menu)
        menu.exec(QtGui.QCursor.pos())

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.value = val
        self.getDataSlots()[0].displayName = "%le" % self.value

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'value': self.getValue()})
        return answer


class ModelBlock(ExecutionBlock):
    def __init__(self, parent, workflow, model=None, model_name=None):
        ExecutionBlock.__init__(self, parent, workflow)
        self.model = model
        self.name = model_name

    def getInputSlots(self):
        return self.model.getInputSlots()

    def getOutputSlots(self):
        return self.model.getOutputSlots()

    def generateCode(self):
        return ["%s.solveStep(tstep)" % self.name]

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'model_classname': self.name})
        return answer

    def constructFromModelMetaData(self, model):
        if model.hasMetadata('name') and model.hasMetadata('inputs') and model.hasMetadata('outputs'):
            self.name = self.model = model.getMetadata('name')
            for slot in model.getMetadata('inputs'):
                self.addDataSlot(InputDataSlot(self, slot['name'], slot['type'], slot['optional']))
            for slot in model.getMetadata('outputs'):
                self.addDataSlot(OutputDataSlot(self, slot['name'], slot['type'], slot['optional']))
            self.updateHeaderText()

    @staticmethod
    def loadModelsFromGivenFile(full_path):
        mod_name, file_ext = os.path.splitext(os.path.split(full_path)[-1])
        py_mod = imp.load_source(mod_name, full_path)
        for mod in dir(py_mod):
            if not mod[0] == "_":
                my_class = getattr(py_mod, mod)
                if my_class.__name__ not in ExecutionBlock.getListOfModelNames() and inspect.isclass(my_class):
                    if issubclass(my_class, mupifApplication.Application):
                        ExecutionBlock.list_of_models.append(my_class)


class TimeLoopBlock(SequentialBlock):
    def __init__(self, parent, workflow):
        SequentialBlock.__init__(self, parent, workflow)
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
            new_block_class = ExecutionBlock.list_of_models[idx]()
            new_block = ModelBlock(self, self.workflow)
            new_block.constructFromModelMetaData(new_block_class)
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
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in TimeLoopBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addMoveMenuActions(menu)
        self.addDeleteMenuActions(menu)
        self.addAddBlockMenuActions(menu)
        self.addChildBlocksMenuActions(menu)
        menu.exec(QtGui.QCursor.pos())


