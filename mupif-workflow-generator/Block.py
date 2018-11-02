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
from DataLink import *
from Button import *
import uuid
import Header
import json


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


class ExecutionBlock (QtWidgets.QGraphicsWidget):
    """
    Abstract class representing execution block
    """
    list_of_models = []

    def __init__(self, parent, workflow, **kwargs):
        QtWidgets.QGraphicsWidget.__init__(self, kwargs.get("parent", None))
        self.workflow = workflow
        self.name = kwargs.get("name", "ExecutionBlock")
        self.parent = parent

        # This unique id is useful for serialization/reconstruction.
        self.uuid = str(uuid.uuid4())

        self.x = 0
        self.y = 0
        self.w = 10
        self.h = 10

        self.spacing = 10
        self.roundness = 0
        self.fillColor = QtGui.QColor(220, 220, 220)

        self.header = Header.Header(self, self.__class__.__name__)
        self.header.setParentItem(self)

        # General configuration.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setAcceptDrops(True)

        self.children_visible = True

        self.button_menu = Button(self, "...")
        self.button_menu.setParentItem(self)

        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()

    def generateInitCode(self):
        """Generate initialization block code"""

    def generateCode(self):
        """returns tuple containing strings with code lines"""
        return ["block_execution"]

    def getChildItems(self):
        return self.childItems()

    def updateHeaderText(self, val=None):
        if val:
            self.header.text = val
        else:
            self.header.text = self.name

    def getDataSlots(self, cls = None):
        """Return a list of data slots.
            If the optional `cls` is specified, return only Slots of that class.
            This is useful e.g. to get all Input or Output Slots.
        """
        slots = []
        for child in self.getChildItems():
            if isinstance(child, DataSlot):
                slots.append(child)
        if cls:
            slots = list(filter(lambda k: k.__class__ is cls, slots))
        return slots

    def getAllDataSlots(self, recursive=False):
        array = self.getDataSlots()
        if recursive:
            for block in self.getChildExecutionBlocks():
                array.extend(block.getAllDataSlots(True))
        return array

    def getDataSlotWithUUID(self, uuid, recursive_search=False):
        for slot in self.getAllDataSlots(recursive_search):
            if slot.uuid == uuid:
                return slot
        return None

    def getDataSlotWithName(self, name):
        """Return matching data slot by its name, None otherwise."""
        for slot in self.getDataSlots():
            if slot.name == name:
                return slot
        return None

    def getDataSlot(self, name=None, uuid=None, parent_uuid=None, recursive_search=False):
        if name or uuid or parent_uuid:
            for slot in self.getAllDataSlots(recursive_search):
                if (not name or (slot.name == name and slot.name)) and (not uuid or (slot.uuid == uuid and slot.uuid)) and (not parent_uuid or (slot.getParentUUID() == parent_uuid and slot.getParentUUID())):
                    return slot
        return None

    def addDataSlot(self, slot):
        """Add the given Slot to this Node.
        A Slot must have a unique name, meaning there can be no duplicates within
        a Node (the displayNames are not constrained though).
        Assign ourselves as the slot's parent item (which also will put it onto
        the current scene, if not yet done) and adjust or size for it.
        The position of the slot is set relative to this Node and depends on it
        either being an Input- or Output slot.
        """
        slot_names = [k.name for k in self.getDataSlots()]
        print("adding slot, existing Slots:", self.getDataSlots(), slot_names)
        if slot.name in slot_names:
            raise DuplicateKnobNameError(
                "Slot names must be unique, but {0} already exists."
                .format(slot.name))
        slot.setParentItem(self)
        slot.spacing = self.spacing
        self.callUpdatePositionOfWholeWorkflow()

    def removeDataSlot(self, slot):
        """Remove the Knob reference to this node and resize."""
        # slot.setParentItem(None)
        slot.destroy()
        self.callUpdatePositionOfWholeWorkflow()

    def addExecutionBlock(self, block):
        block.setParentItem(self)
        self.callUpdatePositionOfWholeWorkflow()

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        blocks = []
        # for child in self.canvas.childItems():
        for child in self.childItems():
            # print(child)
            if isinstance(child, ExecutionBlock):
                blocks.append(child)
                if recursive:
                    blocks += child.getChildExecutionBlocks(cls, recursive)
        if cls:
            blocks = list(filter(lambda k: k.__class__ is cls, blocks))
        return blocks

    def getBlocks(self, cls = None):
        """Return a list of data slots.
            If the optional `cls` is specified, return only Slots of that class.
            This is useful e.g. to get all Input or Output Slots.
        """
        return_array = []
        for child in self.getChildItems():
            if isinstance(child, ExecutionBlock):
                return_array.append(child)
        if cls:
            return_array = list(filter(lambda k: k.__class__ is cls, return_array))
        return return_array

    def generateBlockInputs(self):
        input_slots = self.getDataSlots(InputDataSlot)
        # print ("Slots: ",input_slots)
        code = []
        # generate input code for each block input
        for iSlot in input_slots:
            # try to locate corresponding dataLink
            # print (iLink)
            if len(iSlot.dataLinks) == 0 and iSlot.optional == False:
                # raise AttributeError("No input link for slot detected")
                code.append("# No input for slot %s detected" % iSlot.name)
            elif len(iSlot.dataLinks) > 1:
                raise AttributeError("Multiple input links for slot detected")
            else:
                source = iSlot.dataLinks[0]
                code.append("%s.set(name=%s, value=%s)" % (self.name, iSlot.name, source))
        return code

    def boundingRect(self):
        """Return the bounding box of the Node, limited in height to its Header.
        This is so that the drag & drop sensitive area for the Node is only
        active when hovering its Header, as otherwise there would be conflicts
        with the hover events for the Node's Knobs.
        """
        rect = QtCore.QRectF(self.x,
                             self.y,
                             self.w,
                             self.h)
        return rect

    def minimumWidth(self):
        return self.w

    def minimumHeight(self):
        return self.h

    def sizeHint(self, which, constraint):
        return QtCore.QSizeF(self.w, self.h)

    def updateChildrenPosition(self):

        slot_widths = [k.w + self.spacing * 3 + helpers.getTextSize(k.displayName).width() for k in self.getDataSlots()]
        slot_widths.append(0)
        max_slot_width = max(slot_widths)

        self.header.setX(0)
        self.header.setY(0)

        header_width = (2*self.spacing + helpers.getTextSize(self.header.text).width())

        header_width += (2*self.spacing + helpers.getTextSize(self.button_menu.text).width())

        width_child_max = max(header_width, max_slot_width)
        height_children = self.header.h + self.spacing

        # update data slots
        for elem in self.getDataSlots():
            elem.setY(height_children)
            width_child_max = max(width_child_max, elem.w)
            height_children += elem.h + self.spacing

        # update blocks
        for elem in self.getChildExecutionBlocks():
            elem.setY(height_children)
            width_child_max = max(width_child_max, elem.w)

            height_children += elem.h + self.spacing
            elem.setX(self.spacing)

        self.h = height_children
        self.w = width_child_max + self.spacing*2

        for elem in self.getDataSlots():
            if isinstance(elem, InputDataSlot):
                elem.setX(self.spacing)
            else:
                elem.setX(self.w-elem.w-self.spacing)

    def updateChildrenSizeAndPositionAndResizeSelf(self, color_id=0):
        if color_id:
            self.fillColor = QtGui.QColor(220, 220, 220)
            child_color_id = 0

        else:
            self.fillColor = QtGui.QColor(180, 180, 180)
            child_color_id = 1

        # call it for child blocks
        for elem in self.getChildExecutionBlocks():
            elem.updateChildrenSizeAndPositionAndResizeSelf(child_color_id)

        self.updateChildrenPosition()

    def callUpdatePositionOfWholeWorkflow(self):
        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()
        self.workflow.widget.view.redrawDataLinks()

    def paint(self, painter, option, widget):
        """Draw the Node's container rectangle."""
        painter.setBrush(QtGui.QBrush(self.fillColor))
        # painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.setPen(QtGui.QPen(QtGui.QColor(20, 20, 20)))
        painter.drawRoundedRect(self.x,
                                self.y,
                                self.w,
                                self.h,
                                self.roundness,
                                self.roundness)

    def getConnectedDataLinks(self):
        answer = []
        for dataslot in self.getDataSlots():
            for datalink in dataslot.dataLinks:
                answer.append(datalink)
        return answer

    def updateDataLinksPath(self):
        # nodes = self.scene().selectedItems()
        nodes = self.getChildExecutionBlocks(None, True)
        for node in nodes:
            for dataslot in node.getDataSlots():
                for datalink in dataslot.dataLinks:
                    datalink.updatePath()

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        nodes = self.scene().selectedItems()
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)

    def destroy(self):
        """Remove this Block, its Header, menu Button, DataSlots, child Blocks and connected DataLinks."""
        # TODO fix it
        self.header.destroy()
        self.button_menu.destroy()
        for slot in self.getDataSlots():
            slot.destroy()
        for block in self.getChildExecutionBlocks():
            block.destroy()

        scene = self.scene()
        scene.removeItem(self)
        self.callUpdatePositionOfWholeWorkflow()
        del self

    def addAddStandardBlockMenuAction(self, menu):

        # def _updateChildrenPosition():
        #     self.updateChildrenSizeAndPositionAndResizeSelf()
        #     self.updateDataLinksPath()
        #
        # new_action = menu.addAction("Update position of child blocks")
        # new_action.triggered.connect(_updateChildrenPosition)

        sub_menu = menu.addMenu("Add standard block")

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

        # def _generateCode():
        #     code = self.generateCode()
        #     print()
        #     print()
        #     print()
        #     printCode(code)
        #     print()
        #     print()
        #     print()
        #
        # addGenerateCodeAction = menu.addAction("Generate code")
        # addGenerateCodeAction.triggered.connect(_generateCode)

    def addAddModelBlockMenuAction(self, menu):
        sub_menu = menu.addMenu("Add model block")

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

    def moveChildBlock(self, block, direction):
        child_blocks = self.getChildExecutionBlocks()
        block_id = -5
        if block in child_blocks:
            block_id = child_blocks.index(block)

        if (direction == "up" and block_id > 0) or (direction == "down" and block_id < len(child_blocks)-1):
            scene = self.scene()
            for block in child_blocks:
                scene.removeItem(block)
            idx = 0
            for block in child_blocks:
                if direction == "up" and idx == block_id-1:
                    self.addExecutionBlock(child_blocks[block_id])
                if not idx == block_id:
                    self.addExecutionBlock(block)
                if direction == "down" and idx == block_id + 1:
                    self.addExecutionBlock(child_blocks[block_id])
                idx += 1

    def addMoveMenuActions(self, menu):
        def _move_up():
            self.parent.moveChildBlock(self, 'up')

        def _move_down():
            self.parent.moveChildBlock(self, 'down')

        move_menu = menu.addMenu("Move")
        move_up = move_menu.addAction("Up")
        move_up.triggered.connect(_move_up)
        move_down = move_menu.addAction("Down")
        move_down.triggered.connect(_move_down)

    def addDeleteMenuActions(self, menu):
        def _delete():
            self.destroy()

        delete_menu = menu.addAction("Delete")
        delete_menu.triggered.connect(_delete)

    def addCommonMenuActionsForParentBlocks(self, menu):
        is_parent_block = True
        if isinstance(self, ModelBlock):
            is_parent_block = False
        if isinstance(self, VariableBlock):
            is_parent_block = False
        if is_parent_block:
            self.addAddStandardBlockMenuAction(menu)
            self.addAddModelBlockMenuAction(menu)

    def addCommonMenuActions(self, menu):
        if not isinstance(self, WorkflowBlock):
            self.addMoveMenuActions(menu)
            self.addDeleteMenuActions(menu)
        self.addCommonMenuActionsForParentBlocks(menu)

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in ExecutionBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addCommonMenuActions(menu)
        menu.exec(QtGui.QCursor.pos())

    def getParentUUID(self):
        if self.parentItem():
            return self.parentItem().uuid
        else:
            return None

    def getDictForJSON(self):
        answer = {'classname': self.__class__.__name__, 'uuid': self.uuid, 'parent_uuid': self.getParentUUID()}
        return answer

    def convertToJSON(self):
        return_json_array = []
        return_json_array.append(self.getDictForJSON())

        for elem in self.getDataSlots():
            return_json_array.append(elem.getDictForJSON())

        for elem in self.getChildExecutionBlocks():
            return_json_array.extend(elem.convertToJSON())

        return return_json_array

    @staticmethod
    def getListOfModelNames():
        array = [m.__name__ for m in ExecutionBlock.list_of_models]
        return array


class SequentialBlock (ExecutionBlock):
    """
    Implementation of sequential processing block
    """
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)

    def generateCode(self):
        code = ["# Generating code for %s" % self.name]
        for i_block in self.getChildExecutionBlocks():
            code.append("# Generating code for %s"%(i_block.name))
            code.extend(i_block.generateBlockInputs())  # inputs generated based on block requirements
            code.extend(i_block.generateCode())
        return code

    def boundingRect(self):
        """Return the bounding box of the Node, limited in height to its Header.
        This is so that the drag & drop sensitive area for the Node is only
        active when hovering its Header, as otherwise there would be conflicts
        with the hover events for the Node's Knobs.
        """
        rect = QtCore.QRectF(self.x,
                             self.y,
                             self.w,
                             self.h)
        return rect

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        nodes = self.getChildExecutionBlocks(recursive=True)
        nodes.append(self)
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)


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

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in WorkflowBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addCommonMenuActions(menu)
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
        self.addCommonMenuActions(menu)
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

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in TimeLoopBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addCommonMenuActions(menu)
        menu.exec(QtGui.QCursor.pos())


class CustomPythonCodeBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.code_lines = []

    def generateCode(self):
        return self.code_lines

