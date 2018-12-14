#
#           MuPIF: Multi-Physics Integration Framework
#               Copyright (C) 2010-2018 Borek Patzak
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

import mupif
import inspect
import importlib.util
from DataLink import *
from Button import *
from Label import *
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


def generate_indents(n):
    return "\t"*n


def push_indents_before_each_line(code_lines, indent):
    new_code_lines = []
    for line in code_lines:
        new_code_lines.append(generate_indents(indent) + line)
    return new_code_lines


def replace_tabs_with_spaces_for_each_line(code_lines):
    new_code_lines = []
    for line in code_lines:
        new_code_lines.append(line.replace("\t", " "*4))
    return new_code_lines


class ExecutionBlock (QtWidgets.QGraphicsWidget):
    """
    Abstract class representing execution block
    """
    list_of_models = []
    list_of_model_dependencies = []
    list_of_block_classes = []

    def __init__(self, parent, workflow, **kwargs):
        QtWidgets.QGraphicsWidget.__init__(self, kwargs.get("parent", None))
        self.workflow = workflow
        self.name = kwargs.get("name", "ExecutionBlock")
        self.parent = parent

        self.code_name = ""

        # This unique id is useful for serialization/reconstruction.
        self.uuid = str(uuid.uuid4())

        self.x = 0
        self.y = 0
        self.w = 10
        self.h = 10

        self.spacing = 10
        self.roundness = 0
        self.fillColor = QtGui.QColor(220, 220, 220)

        self.label = Label(self)

        self.header = Header.Header(self, self.__class__.__name__)
        self.header.setParentItem(self)

        self.clonable = False

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

    def clone(self):
        """"""

    def setPropertiesFromAnotherBlockOfSameType(self, block):
        """"""

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """

    @staticmethod
    def getIDOfModelInList(model):
        if model in ExecutionBlock.list_of_models:
            return ExecutionBlock.list_of_models.index(model)
        return -1

    def getIDOfModelNameInList(self, model_name):
        if model_name in self.getListOfModelClassnames():
            return self.getListOfModelClassnames().index(model_name)
        return -1

    def generateInitCode(self, indent=0):
        """Generate initialization block code"""
        code = ["", "# initialization code of %s (%s)" % (self.code_name, self.name)]
        return push_indents_before_each_line(code, indent)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        """returns tuple containing strings with code lines"""
        code = ["", "# execution code of %s (%s)" % (self.code_name, self.name)]
        return push_indents_before_each_line(code, indent)

    def generateBlockInputs(self):
        input_slots = self.getDataSlots(InputDataSlot)
        # print ("Slots: ",input_slots)
        code = []
        # generate input code for each block input
        for iSlot in input_slots:
            # try to locate corresponding dataLink
            # print (iLink)
            if len(iSlot.dataLinks) == 0 and not iSlot.optional:
                # raise AttributeError("No input link for slot detected")
                code.append("# No input for slot %s detected" % iSlot.name)
            elif len(iSlot.dataLinks) > 1:
                raise AttributeError("Multiple input links for slot detected")
            else:
                source = iSlot.dataLinks[0]
                code.append("%s.set(name=%s, value=%s)" % (self.name, iSlot.name, source))
        return code

    def generateOutputDataSlotGetFunction(self, slot, time=''):
        if slot in self.getDataSlots(OutputDataSlot):
            if isinstance(slot.obj_id, str):
                obj_id = "'%s'" % slot.obj_id
            else:
                obj_id = str(slot.obj_id)
            return "self.%s.get(%s, %s, %s)" % (self.code_name, slot.obj_type, time, obj_id)
        return "None"

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
        # TODO
        slot_names = [k.name for k in self.getDataSlots()]
        # print("adding slot, existing Slots:", self.getDataSlots(), slot_names)
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
        """Return a list of child blocks.
            If the optional `cls` is specified, return only blocks of that class.
            This is useful e.g. to get all Input or Output Slots.
        """
        return_array = []
        for child in self.getChildItems():
            if isinstance(child, ExecutionBlock):
                return_array.append(child)
        if cls:
            return_array = list(filter(lambda k: k.__class__ is cls, return_array))
        return return_array

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

        slot_widths = [self.spacing * 2 + k.getNeededWidth() for k in self.getDataSlots()]
        slot_widths.append(0)
        max_slot_width = max(slot_widths)

        self.header.setX(0)
        self.header.setY(0)

        header_width = (2*self.spacing + helpers.getTextSize(self.header.text).width())

        header_width += (2*self.spacing + helpers.getTextSize(self.button_menu.text).width())

        width_child_max = max(header_width, max_slot_width, self.label.getNeededWidth())

        height_children = self.header.h + self.spacing

        self.label.x = self.spacing
        self.label.y = height_children
        if self.label.shouldBePainted():
            height_children += self.label.getHeight() + self.spacing

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
            elem.setTotalWidth(self.w-self.spacing*2)

    def updateChildrenSizeAndPositionAndResizeSelf(self, color_id=0):
        if color_id:
            child_color_id = 0
        else:
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

    def addMenuItems_AddStandardBlock(self, menu):
        sub_menu = menu.addMenu("Add standard block")

        def _addStandardBlock(idx):
            new_block = ExecutionBlock.list_of_block_classes[idx](self, self.workflow)
            self.addExecutionBlock(new_block)

        cls_id = 0
        for block_class in ExecutionBlock.list_of_block_classes:
            add_model_block_action = sub_menu.addAction(block_class.__name__)
            add_model_block_action.triggered.connect(lambda checked, idx=cls_id: _addStandardBlock(idx))
            cls_id += 1

    def addMenuItems_AddModelBlock(self, menu):
        sub_menu = menu.addMenu("Add model block")

        def _addModelBlock(idx):
            new_block_class = ExecutionBlock.list_of_models[idx]()
            new_block = ModelBlock(self, self.workflow)
            new_block.constructFromModelMetaData(new_block_class)
            self.addExecutionBlock(new_block)

        cls_id = 0
        for model in ExecutionBlock.list_of_models:
            add_model_block_action = sub_menu.addAction(model.__name__)
            add_model_block_action.triggered.connect(lambda checked, idx=cls_id: _addModelBlock(idx))
            cls_id += 1

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
        if isinstance(self, CustomPythonCodeBlock):
            is_parent_block = False
        if isinstance(self, CustomNameVariableBlock):
            is_parent_block = False
        if is_parent_block:
            self.addMenuItems_AddStandardBlock(menu)
            self.addMenuItems_AddModelBlock(menu)

    def addCloneAction(self, menu):
        if self.clonable:
            def _clone():
                self.clone()

            clone_menu = menu.addAction("Clone")
            clone_menu.triggered.connect(_clone)

    def addCommonMenuActions(self, menu):
        if not isinstance(self, WorkflowBlock):
            self.addMoveMenuActions(menu)
            self.addDeleteMenuActions(menu)
        self.addCommonMenuActionsForParentBlocks(menu)
        self.addCloneAction(menu)

    def addMenuItems(self, menu):
        self.addCommonMenuActions(menu)

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addMenuItems(menu)
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
    def getListOfModelClassnames():
        array = [m.__name__ for m in ExecutionBlock.list_of_models]
        return array

    @staticmethod
    def getListOfModelDependencies():
        return ExecutionBlock.list_of_model_dependencies

    @staticmethod
    def getListOfStandardBlockClassnames():
        array = [m.__name__ for m in ExecutionBlock.list_of_block_classes]
        return array

    def initializeFromJSONData(self, json_data):
        self.uuid = json_data['uuid']
        e_parent_e = self.workflow.widget.getNodeById(json_data['parent_uuid'])
        self.parent = e_parent_e
        self.setParentItem(e_parent_e)

    def generateNewDataSlotName(self, base="data_slot_"):
        names = [n.name for n in self.getAllDataSlots()]
        i = 0
        while True:
            i += 1
            new_name = "%s%d" % (base, i)
            if not new_name in names:
                return new_name

    def generateCodeName(self, base_name='block_'):
        i = 0
        while True:
            i += 1
            new_name = "%s%d" % (base_name, i)
            if new_name not in self.workflow.getAllElementCodeNames():
                self.code_name = new_name
                return


class SequentialBlock (ExecutionBlock):
    """
    Implementation of sequential processing block
    """
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)

        for block in self.getChildExecutionBlocks():
            code.extend(block.generateExecutionCode())

        return push_indents_before_each_line(code, indent)

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
        self.workflow_name = "MyProblemClassWorkflow"

        ExecutionBlock.list_of_block_classes = []
        ExecutionBlock.list_of_block_classes.extend([TimeLoopBlock, FloatVariableBlock, CustomPythonCodeBlock])
        ExecutionBlock.list_of_block_classes.extend([ConstantPropertyBlock, ConstantPhysicalQuantityBlock])
        ExecutionBlock.list_of_block_classes.extend([IfElseBlock, CustomNameVariableBlock])

    def getScene(self):
        return self.loc_scene

    def getAllDataLinks(self):
        """

        :return: Returns datalinks of the whole workflow.
        :rtype DataLink[]
        """
        answer = []
        for block in self.getChildExecutionBlocks(None, True):
            for datalink in block.getConnectedDataLinks():
                if datalink not in answer:
                    answer.append(datalink)
        return answer

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

            if e['classname'] == 'ExternalInputDataSlot':
                new_ds = ExternalInputDataSlot(self, e['name'], DataSlotType.getTypeFromName(e['type']), True, None,
                                               e['obj_type'], e['obj_id'])
                new_ds.uuid = e['uuid']
                self.addDataSlot(new_ds)

            elif e['classname'] == 'ExternalOutputDataSlot':
                new_ds = ExternalOutputDataSlot(self, e['name'], e['type'])
                new_ds.uuid = e['uuid']
                self.addDataSlot(new_ds)

            elif e['classname'] in ExecutionBlock.getListOfStandardBlockClassnames():
                cls_id = ExecutionBlock.getListOfStandardBlockClassnames().index(e['classname'])
                new_e = ExecutionBlock.list_of_block_classes[cls_id](None, self)
                new_e.initializeFromJSONData(e)

            elif e['classname'] == 'ModelBlock':
                if e['model_classname'] in ExecutionBlock.getListOfModelClassnames():
                    cls_id = ExecutionBlock.getListOfModelClassnames().index(e['model_classname'])
                    new_block_class = ExecutionBlock.list_of_models[cls_id]()
                    new_e = ModelBlock(None, self)
                    new_e.constructFromModelMetaData(new_block_class)
                    new_e.initializeFromJSONData(e)

                else:
                    print("MODEL CLASS NOT FOUND IN KNOWN MODELS")

            else:
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

    def addExternalDataSlotItems(self, menu):
        def _add_external_input_dataslot():
            new_slot = ExternalOutputDataSlot(self, self.generateNewDataSlotName("ExternalInputDataSlot_"), DataSlotType.Scalar)
            self.addDataSlot(new_slot)

        def _add_external_output_dataslot():
            new_slot = ExternalInputDataSlot(self, self.generateNewDataSlotName("ExternalOutputDataSlot_"), DataSlotType.Scalar)
            self.addDataSlot(new_slot)

        temp_menu = menu.addMenu("Add external DataSlot")
        add_input = temp_menu.addAction("Input")
        add_input.triggered.connect(_add_external_input_dataslot)
        add_output = temp_menu.addAction("Output")
        add_output.triggered.connect(_add_external_output_dataslot)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addExternalDataSlotItems(menu)

    def checkConsistency(self, execution=False):
        data_slots = self.getAllDataSlots(True)
        for ds in data_slots:
            if not ds.optional and not ds.connected():
                print("Some compulsory DataSlots are not connected.")
                return False
            if execution and (isinstance(ds, ExternalInputDataSlot) or isinstance(ds, ExternalOutputDataSlot)):
                if ds.connected():
                    print("Usage of External DataSlots is not allowed in execution Workflow.")
                    return False
        return True

    def getAllExternalDataSlots(self, only=""):
        eds = []
        for slot in self.getAllDataSlots():
            if isinstance(slot, ExternalInputDataSlot) and (only == "" or only == "in"):
                eds.append(slot)
            if isinstance(slot, ExternalOutputDataSlot) and (only == "" or only == "out"):
                eds.append(slot)
        return eds

    def generateWorkflowCode(self, class_code):
        if class_code:
            workflow_classname = self.workflow_name
        else:
            workflow_classname = "MyProblemExecutionWorkflow"

        #

        self.generateAllElementCodeNames()

        all_model_blocks = self.getChildExecutionBlocks(None, True)
        child_blocks = self.getChildExecutionBlocks()

        code = ["import mupif"]

        for model in self.getChildExecutionBlocks(ModelBlock, True):
            code.append(model.getModelDependency())

        code.append("")
        code.append("")
        code.append("class %s(mupif.Workflow.Workflow):" % workflow_classname)
        code.append("\tdef __init__(self):")
        code.append("\t\tmupif.Workflow.Workflow.__init__(self)")

        # metadata

        if class_code:
            code.append("\t\tself.metadata.update({'name': '%s'})" % workflow_classname)

            code_add = ""
            for s in self.getAllExternalDataSlots("out"):
                if s.connected():
                    params = "'name': '%s', 'type': '%s', 'optional': %s, 'description': '%s', 'obj_type': '%s', " \
                             "'obj_id': '%s'" % (
                                s.name, DataSlotType.getNameFromType(s.type), False, "",
                                s.getLinkedDataSlot().obj_type, s.obj_id)

                    if code_add != "":
                        code_add = "%s, " % code_add
                    code_add = "%s{%s}" % (code_add, params)

            code.append("\t\tself.metadata.update({'inputs': [%s]})" % code_add)

            code_add = ""
            for s in self.getAllExternalDataSlots("in"):
                if s.connected():
                    params = "'name': '%s', 'type': '%s', 'optional': %s, 'description': '%s', 'obj_type': '%s', " \
                             "'obj_id': '%s'" % (
                                s.name, DataSlotType.getNameFromType(s.type), True, "",
                                s.getLinkedDataSlot().obj_type, s.obj_id)

                    if code_add != "":
                        code_add = "%s, " % code_add
                    code_add = "%s{%s}" % (code_add, params)

            code.append("\t\tself.metadata.update({'outputs': [%s]})" % code_add)

            # initialization of workflow inputs
            for s in self.getAllExternalDataSlots("out"):
                if s.connected():
                    code.append("\t")
                    code.append("\t\t# initialization code of external input")
                    code.append("\t\tself.%s = None" % s.code_name)
                    code.append("\t\t# It should be defined from outside using set() method.")

        # init codes of child blocks

        for model in all_model_blocks:
            code.extend(model.generateInitCode(2))

        # get critical time step

        if class_code:
            code.append("\t")
            code.append("\tdef getCriticalTimeStep(self):")
            code_add = ""
            i = 0
            for model in child_blocks:
                if isinstance(model, ModelBlock):
                    if i:
                        code_add += ", "
                    code_add += "self.%s.getCriticalTimeStep()" % model.code_name
                    i += 1
            code.append("\t\treturn min([%s])" % code_add)

        if class_code:
            #
            #
            # set method

            code.append("\t")
            code.append("\t# set method for all external inputs")
            code.append("\tdef set(self, obj, objectID=0):")
            code.append("\t\t\t")
            code.append("\t\t# in case of Property")
            code.append("\t\tif isinstance(obj, mupif.Property.Property):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("out"):
                if s.connected():
                    if s.type == DataSlotType.Property:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\tself.%s = obj" % s.code_name)

            code.append("\t\t\t")
            code.append("\t\t# in case of Field")
            code.append("\t\tif isinstance(obj, mupif.Field.Field):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("out"):
                if s.connected():
                    if s.type == DataSlotType.Field:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\tself.%s = obj" % s.code_name)

            code.append("\t\t\t")
            code.append("\t\t# in case of Function")
            code.append("\t\tif isinstance(obj, mupif.Function.Function):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("out"):
                if s.connected():
                    if s.type == DataSlotType.Function:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\tself.%s = obj" % s.code_name)

            #
            #
            # get method

            code.append("\t")
            code.append("\t# set method for all external inputs")
            code.append("\tdef get(self, objectType, time=None, objectID=0):")
            code.append("\t\t\t")
            code.append("\t\t# in case of Property")
            code.append("\t\tif isinstance(objectType, mupif.propertyID.PropertyID):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("in"):
                if s.connected():
                    if s.type == DataSlotType.Property:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\treturn self.%s" %
                                    s.getLinkedDataSlot().owner.generateOutputDataSlotGetFunction(s.getLinkedDataSlot(),
                                                                                                  'time'))

            code.append("\t\t\t")
            code.append("\t\t# in case of Field")
            code.append("\t\tif isinstance(objectType, mupif.fieldID.FieldID):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("in"):
                if s.connected():
                    if s.type == DataSlotType.Field:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\treturn %s" %
                                    s.getLinkedDataSlot().owner.generateOutputDataSlotGetFunction(s.getLinkedDataSlot(),
                                                                                                  'time'))

            code.append("\t\t\t")
            code.append("\t\t# in case of Function")
            code.append("\t\tif isinstance(objectType, mupif.functionID.FunctionID):")
            code.append("\t\t\tpass")
            for s in self.getAllExternalDataSlots("in"):
                if s.connected():
                    if s.type == DataSlotType.Function:
                        code.append("\t\t\tif objectID == '%s':" % s.name)
                        code.append("\t\t\t\treturn self.%s" %
                                    s.getLinkedDataSlot().owner.generateOutputDataSlotGetFunction(s.getLinkedDataSlot(),
                                                                                                  'time'))
            code.append("\t\t")
            code.append("\t\treturn None")

        # terminate

        code.append("\t")
        code.append("\tdef terminate(self):")
        for model in all_model_blocks:
            if isinstance(model, ModelBlock):
                code.append("\t\tself.%s.terminate()" % model.code_name)
        code.append("\t")

        # solve or solveStep

        if class_code:
            code.append("\tdef solveStep(self, tstep, stageID=0, runInBackground=False):")
        else:
            code.append("\tdef solve(self, runInBackground=False):")

        for model in child_blocks:
            code.extend(model.generateExecutionCode(2, "tstep.getTime()"))

        if not class_code:
            code.append("")
            code.append("\t\t# terminate all models")
            code.append("\t\tself.terminate()")
            code.append("")

        code.append("")

        # execution

        if not class_code:
            code.append("problem = %s()" % workflow_classname)
            code.append("problem.solve()")
            code.append("")
            code.append("print('Simulation has finished.')")
            code.append("")
            code.append("")

        return replace_tabs_with_spaces_for_each_line(code)

    def getExecutionCode(self):
        return self.generateWorkflowCode(class_code=False)

    def getClassCode(self):
        return self.generateWorkflowCode(class_code=True)

    def getAllElementCodeNames(self):
        code_names = [block.code_name for block in self.getChildExecutionBlocks(None, True)]
        code_names.extend([slot.code_name for slot in self.getAllExternalDataSlots()])
        return code_names

    def generateAllElementCodeNames(self):
        # for block in self.getChildExecutionBlocks(None, True):
        #     block.code_name = ""
        for block in self.getChildExecutionBlocks(None, True):
            block.generateCodeName()
        for slot in self.getAllExternalDataSlots():
            slot.generateCodeName()

    def generateOutputDataSlotGetFunction(self, slot, time=''):
        return slot.getCodeRepresentation()


class VariableBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.value = None
        self.fillColor = QtGui.QColor(255, 124, 128)

    def paint(self, painter, option, widget):
        ExecutionBlock.paint(self, painter, option, widget)

    def generateCodeName(self, base_name='variable_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def setValueFromTextInput(self, val):
        """"""

    def addSpecificMenuItems(self, menu):
        def _setValue():
            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Set value", "")
            if ok_pressed:
                self.setValueFromTextInput(new_value)
                self.updateLabel()

        action = menu.addAction("Set value")
        action.triggered.connect(_setValue)

    def getCodeRepresentation(self):
        return "self.%s" % self.code_name

    def generateOutputDataSlotGetFunction(self, slot, time=''):
        return self.getCodeRepresentation()


class FloatVariableBlock(VariableBlock):
    def __init__(self, parent, workflow):
        VariableBlock.__init__(self, parent, workflow)
        self.value = 0.
        self.updateLabel()
        self.addDataSlot(OutputDataSlot(self, "value", DataSlotType.Scalar, False))

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """
        self.label.setText("value = %.3le" % self.value)

    def setValueFromTextInput(self, val):
        self.value = float(val)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addSpecificMenuItems(menu)

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.value = val
        self.updateLabel()

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'value': self.getValue()})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        self.setValue(json_data['value'])

    def generateCodeName(self, base_name='float_variable_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        return []

    def generateInitCode(self, indent=0):
        """
        Generates the initialization code of this block.
        :param int indent: number of indents to be added before each line
        :return: array of code lines
        :rtype str[]
        """
        if self.getDataSlotWithName("value").connected():
            code = ExecutionBlock.generateInitCode(self)
            code.append("self.%s = %le" % (self.code_name, self.value))
            return push_indents_before_each_line(code, indent)
        return []

    def generateOutputDataSlotGetFunction(self, slot, time='', get_variable=False):
        if get_variable:
            return self.getCodeRepresentation()
        return self.generatePropertyCode()

    def generatePropertyCode(self):
        value = "(%s,)" % self.getCodeRepresentation()
        propID = "0"
        valueType = "mupif.ValueType.ValueType.Scalar"
        units = "mupif.Physics.PhysicalQuantities.PhysicalUnit('', 1., [0, 0, 0, 0, 0, 0, 0, 0, 0])"
        objectID = "0"
        return "mupif.Property.ConstantProperty(%s, %s, %s, %s, None, %s)" % (
            value, propID, valueType, units, objectID)


class ConstantPropertyBlock(VariableBlock):
    def __init__(self, parent, workflow):
        VariableBlock.__init__(self, parent, workflow)
        self.addDataSlot(OutputDataSlot(self, "value", DataSlotType.Property, False))
        self.value = ()
        self.propID = None
        self.valueType = None
        self.units = None
        self.objectID = 0
        self.updateLabel()
        self.clonable = True

    def clone(self):
        block = ConstantPropertyBlock(self.parent, self.workflow)
        block.setPropertiesFromAnotherBlockOfSameType(self)
        self.parent.addExecutionBlock(block)

    def setPropertiesFromAnotherBlockOfSameType(self, block):
        """

        :param ConstantPropertyBlock block:
        :return: 
        """
        self.value = block.value
        self.propID = block.propID
        self.valueType = block.valueType
        self.units = block.units
        self.objectID = block.objectID
        self.updateLabel()

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """
        self.label.setText("value           = %s\npropID        = %s\nvalueType = %s\nunits           = %s\n"
                           "objectID    = %s" % (
                            self.value, self.propID, self.valueType, self.units, self.objectID))

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'value': self.value})
        answer.update({'propID': str(self.propID)})
        answer.update({'valueType': str(self.valueType)})
        answer.update({'units': self.units})
        answer.update({'objectID': str(self.objectID)})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        t = ()
        for e in json_data['value']:
            t = t + (float(e),)
        self.setValue(t)
        self.setPropertyID(json_data['propID'])
        self.setValueType(json_data['valueType'])
        self.setUnits(json_data['units'])
        self.setObjectID(json_data['objectID'])

    def generateCodeName(self, base_name='constant_property_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def generateInitCode(self, indent=0):
        """
        Generates the initialization code of this block.
        :param int indent: number of indents to be added before each line
        :return: array of code lines
        :rtype str[]
        """
        if self.getDataSlotWithName("value").connected():
            code = ExecutionBlock.generateInitCode(self)
            code.append("self.%s = mupif.Property.ConstantProperty("
                        "%s, mupif.propertyID.%s, mupif.ValueType.%s, mupif.Physics.PhysicalQuantities._unit_table['%s'], "
                        "None, %s)" % (
                            self.code_name, self.value, self.propID, self.valueType, self.units, self.objectID))
            return push_indents_before_each_line(code, indent)
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        return []

    def setValue(self, val):
        self.value = val
        self.updateLabel()

    def setPropertyID(self, val):
        self.propID = val
        self.updateLabel()

    def setValueType(self, val):
        self.valueType = val
        self.updateLabel()

    def setObjectID(self, val):
        self.objectID = val
        self.updateLabel()

    def setUnits(self, val):
        self.units = val
        self.updateLabel()

    def addSpecificMenuItems(self, menu):
        sub_menu = menu.addMenu("Modify")

        def _setValue():
            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter new value", "")
            if ok_pressed:
                t = ()
                for e in new_value.split(' '):
                    t = t + (float(e),)
                self.setValue(t)

        def _setPropertyID():
            items = ['']
            items.extend(list(map(str, mupif.propertyID.PropertyID)))
            items_real = [0]
            items_real.extend(list(mupif.propertyID.PropertyID))

            selected_id = 0
            if str(self.propID) in items:
                selected_id = items.index(str(self.propID))

            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            item, ok = QtWidgets.QInputDialog.getItem(temp, "Choose PropertyID", "", items, selected_id, False)
            if ok and item:
                if item in items:
                    selected_id = items.index(item)
                    self.setPropertyID(items_real[selected_id])

        def _setValueType():
            # if self.getDataSlotWithName('value').connected():
            #     QtWidgets.QMessageBox.about(self.workflow.widget, "Action denied",
            #                                 "Cannot change ValueType while the DataSlot is connected.")
            # else:
            items = ['']
            items.extend(list(map(str, mupif.ValueType.ValueType)))
            items_real = [0]
            items_real.extend(list(mupif.ValueType.ValueType))

            selected_id = 0
            if str(self.valueType) in items:
                selected_id = items.index(str(self.valueType))

            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            item, ok = QtWidgets.QInputDialog.getItem(temp, "Choose ValueType", "", items, selected_id, False)
            if ok and item:
                if item in items:
                    selected_id = items.index(item)
                    self.valueType = items_real[selected_id]
                    self.updateLabel()

        def _setObjectID():
            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getInt(temp, "Set objectID", "", value=self.objectID, min=0)
            if ok_pressed:
                self.setObjectID(new_value)

        def _setUnits():
            # if self.getDataSlotWithName('value').connected():
            #     QtWidgets.QMessageBox.about(self.workflow.widget, "Action denied",
            #                                 "Cannot change Units while the DataSlot is connected.")
            # else:
            items = ['']
            items.extend(list(map(str, mupif.Physics.PhysicalQuantities._unit_table)))
            items_real = [0]
            items_real.extend(list(mupif.Physics.PhysicalQuantities._unit_table))

            selected_id = 0
            if str(self.units) in items:
                selected_id = items.index(str(self.units))

            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            item, ok = QtWidgets.QInputDialog.getItem(temp, "Choose Units", "", items, selected_id, False)
            if ok and item:
                if item in items:
                    selected_id = items.index(item)
                    self.setUnits(items_real[selected_id])

        action = sub_menu.addAction("Set value")
        action.triggered.connect(_setValue)
        action = sub_menu.addAction("Set PropertyID")
        action.triggered.connect(_setPropertyID)
        action = sub_menu.addAction("Set ValueType")
        action.triggered.connect(_setValueType)
        action = sub_menu.addAction("Set units")
        action.triggered.connect(_setUnits)
        action = sub_menu.addAction("Set objectID")
        action.triggered.connect(_setObjectID)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addSpecificMenuItems(menu)


class ConstantPhysicalQuantityBlock(VariableBlock):
    def __init__(self, parent, workflow):
        VariableBlock.__init__(self, parent, workflow)
        self.addDataSlot(OutputDataSlot(self, "value", DataSlotType.PhysicalQuantity, False))
        self.value = 0.
        self.units = None
        self.updateLabel()
        self.clonable = True

    def clone(self):
        block = ConstantPhysicalQuantityBlock(self.parent, self.workflow)
        block.setPropertiesFromAnotherBlockOfSameType(self)
        self.parent.addExecutionBlock(block)

    def setPropertiesFromAnotherBlockOfSameType(self, block):
        """

        :param ConstantPhysicalQuantityBlock block:
        :return:
        """
        self.value = block.value
        self.units = block.units
        self.updateLabel()

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """
        self.label.setText("value = %s\nunits = %s" % (self.value, self.units))

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'value': self.value})
        answer.update({'units': self.units})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        self.setValue(json_data['value'])
        self.setUnits(json_data['units'])

    def generateCodeName(self, base_name='constant_physical_quantity_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def generateInitCode(self, indent=0):
        """
        Generates the initialization code of this block.
        :param int indent: number of indents to be added before each line
        :return: array of code lines
        :rtype str[]
        """
        if self.getDataSlotWithName("value").connected():
            code = ExecutionBlock.generateInitCode(self)
            code.append("self.%s = mupif.Physics.PhysicalQuantities.PhysicalQuantity(%s, "
                        "mupif.Physics.PhysicalQuantities._unit_table['%s'])" % (
                            self.code_name, self.value, self.units))
            return push_indents_before_each_line(code, indent)
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        return []

    def setValue(self, val):
        self.value = val
        self.updateLabel()

    def setUnits(self, val):
        self.units = val
        self.updateLabel()

    def addSpecificMenuItems(self, menu):
        sub_menu = menu.addMenu("Modify")

        def _setValue():
            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getDouble(temp, "Set value", "", value=self.value)
            if ok_pressed:
                self.setValue(new_value)

        def _setUnits():
            # if self.getDataSlotWithName('value').connected():
            #     QtWidgets.QMessageBox.about(self.workflow.widget, "Action denied",
            #                                 "Cannot change Units while the DataSlot is connected.")
            # else:
            items = ['']
            items.extend(list(map(str, mupif.Physics.PhysicalQuantities._unit_table)))
            items_real = [0]
            items_real.extend(list(mupif.Physics.PhysicalQuantities._unit_table))

            selected_id = 0
            if str(self.units) in items:
                selected_id = items.index(str(self.units))

            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            item, ok = QtWidgets.QInputDialog.getItem(temp, "Choose Units", "", items, selected_id, False)
            if ok and item:
                if item in items:
                    selected_id = items.index(item)
                    self.setUnits(items_real[selected_id])

        action = sub_menu.addAction("Set value")
        action.triggered.connect(_setValue)
        action = sub_menu.addAction("Set units")
        action.triggered.connect(_setUnits)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addSpecificMenuItems(menu)


class ModelBlock(ExecutionBlock):
    def __init__(self, parent, workflow, model=None, model_name=None):
        ExecutionBlock.__init__(self, parent, workflow)
        self.model = model
        self.name = model_name
        self.input_file_name = ""
        self.input_file_directory = "."
        self.fillColor = QtGui.QColor(183, 222, 232)

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """
        label_text = ""
        if self.input_file_name != "":
            label_text += "input_file = '%s'\nworkdir = '%s'" % (self.input_file_name, self.input_file_directory)
        self.label.setText(label_text)

    def paint(self, painter, option, widget):
        ExecutionBlock.paint(self, painter, option, widget)

    def setInputFile(self, val):
        """
        Sets the input file name.
        :param str val: input file name
        """
        self.input_file_name = val
        self.updateLabel()

    def setInputFilePath(self, val):
        """
        Sets the input file directory.
        :param str val: input file directory.
        """
        self.input_file_directory = val
        self.updateLabel()

    def getInputSlots(self):
        return self.model.getInputSlots()

    def getOutputSlots(self):
        return self.model.getOutputSlots()

    def generateInitCode(self, indent=0):
        """
        Generates the initialization code of this block.
        :param int indent: number of indents to be added before each line
        :return: array of code lines
        :rtype str[]
        """
        code = ExecutionBlock.generateInitCode(self)
        input_file_add = ""
        if self.input_file_name != "":
            input_file_add = "file='%s', workdir='%s'" % (self.input_file_name, self.input_file_directory)
        code.append("self.%s = %s(%s)" % (self.code_name, self.name, input_file_add))
        return push_indents_before_each_line(code, indent)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)

        for slot in self.getDataSlots(InputDataSlot):
            linked_slot = slot.getLinkedDataSlot()
            if linked_slot:
                code.append("self.%s.set(%s, %d)" % (
                    self.code_name, linked_slot.owner.generateOutputDataSlotGetFunction(linked_slot, time),
                    slot.obj_id))

        code.append("self.%s.solveStep(%s)" % (self.code_name, timestep))

        return push_indents_before_each_line(code, indent)

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'model_classname': self.name})
        answer.update({'model_input_file_name': self.input_file_name})
        answer.update({'model_input_file_directory': self.input_file_directory})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        self.input_file_name = json_data['model_input_file_name']
        self.input_file_directory = json_data['model_input_file_directory']

    def constructFromModelMetaData(self, model):
        if model.hasMetadata('name') and model.hasMetadata('inputs') and model.hasMetadata('outputs'):
            self.name = self.model = model.getMetadata('name')
            for slot in model.getMetadata('inputs'):
                obj_id = 0
                if 'obj_id' in slot:
                    obj_id = slot['obj_id']
                self.addDataSlot(
                    InputDataSlot(self, slot['name'], DataSlotType.getTypeFromName(slot['type']), slot['optional'],
                                  None, slot['obj_type'], obj_id))
            for slot in model.getMetadata('outputs'):
                obj_id = 0
                if 'obj_id' in slot:
                    obj_id = slot['obj_id']
                self.addDataSlot(
                    OutputDataSlot(self, slot['name'], DataSlotType.getTypeFromName(slot['type']), slot['optional'],
                                   None, slot['obj_type'], obj_id))
            self.updateHeaderText()

    @staticmethod
    def loadModelsFromGivenFile(full_path):
        mod_name, file_ext = os.path.splitext(os.path.split(full_path)[-1])
        spec = importlib.util.spec_from_file_location(mod_name, full_path)
        py_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py_mod)
        for mod in dir(py_mod):
            if not mod[0] == "_":
                my_class = getattr(py_mod, mod)
                if hasattr(my_class, '__name__'):
                    if my_class.__name__ not in ExecutionBlock.getListOfModelClassnames() and inspect.isclass(my_class):
                        if issubclass(my_class, mupif.Application.Application) or issubclass(my_class,
                                                                                            mupif.Workflow.Workflow):
                            ExecutionBlock.list_of_models.append(my_class)
                            ExecutionBlock.list_of_model_dependencies.append("from %s import %s" % (
                                py_mod.__name__, my_class.__name__))

    def generateCodeName(self, base_name='model_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def getModelDependency(self):
        model_id = self.getIDOfModelNameInList(self.name)
        if model_id > -1:
            return ExecutionBlock.list_of_model_dependencies[model_id]
        return "# dependency of %s not found" % self.code_name

    def addLocalMenuItems(self, menu):
        def _set_input_file_name():
            temp = QtWidgets.QInputDialog()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter input file name", "", QtWidgets.QLineEdit.Normal, self.input_file_name)
            if ok_pressed:
                self.setInputFile(new_value)

        def _set_input_file_directory():
            temp = QtWidgets.QInputDialog()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter input file directory", "", QtWidgets.QLineEdit.Normal, self.input_file_directory)
            if ok_pressed:
                self.setInputFilePath(new_value)

        submenu = menu.addMenu("Set input file")

        action = submenu.addAction("File name")
        action.triggered.connect(_set_input_file_name)

        action = submenu.addAction("File directory")
        action.triggered.connect(_set_input_file_directory)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addLocalMenuItems(menu)


class TimeLoopBlock(SequentialBlock):
    def __init__(self, parent, workflow):
        SequentialBlock.__init__(self, parent, workflow)
        self.addDataSlot(InputDataSlot(self, "start_time", DataSlotType.PhysicalQuantity, False))
        self.addDataSlot(InputDataSlot(self, "target_time", DataSlotType.PhysicalQuantity, False))
        self.addDataSlot(InputDataSlot(self, "max_dt", DataSlotType.PhysicalQuantity, True))
        self.fillColor = QtGui.QColor(255, 255, 153)

    def getStartTime(self):
        connected_slot = self.getDataSlotWithName("start_time").getLinkedDataSlot()
        if connected_slot:
            return connected_slot.owner.generateOutputDataSlotGetFunction(connected_slot)
        return None

    def getTargetTime(self):
        connected_slot = self.getDataSlotWithName("target_time").getLinkedDataSlot()
        if connected_slot:
            return connected_slot.owner.generateOutputDataSlotGetFunction(connected_slot)
        return None

    def getMaxDt(self):
        connected_slot = self.getDataSlotWithName("max_dt").getLinkedDataSlot()
        if connected_slot:
            return connected_slot.owner.generateOutputDataSlotGetFunction(connected_slot)
        return None

    def generateInitCode(self, indent=0):
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)
        var_time = "%s_time" % self.code_name
        var_target_time = "%s_target_time" % self.code_name
        var_dt = "%s_dt" % self.code_name
        var_compute = "%s_compute" % self.code_name
        var_time_step = "%s_time_step" % self.code_name
        var_time_step_number = "%s_time_step_number" % self.code_name

        code.append("time_units = mupif.Physics.PhysicalQuantities.PhysicalUnit('s', 1., [0, 0, 1, 0, 0, 0, 0, 0, 0])")

        code.append("%s = %s" % (var_time, self.getStartTime()))
        code.append("%s = %s" % (var_target_time, self.getTargetTime()))

        code.append("%s = True" % var_compute)
        code.append("%s = 0" % var_time_step_number)

        code.append("while %s:" % var_compute)
        while_code = []

        code.append("\t%s += 1" % var_time_step_number)

        dt_code = "\t%s = min([" % var_dt
        first = True

        if self.getMaxDt():
            dt_code += self.getMaxDt()
            first = False

        for model in self.getChildExecutionBlocks(ModelBlock):
            if not first:
                dt_code += ", "
            dt_code += "self.%s.getCriticalTimeStep()" % model.code_name
            first = False
        dt_code += "])"

        while_code.append("")
        while_code.append(dt_code)
        while_code.append("\t%s = min(%s+%s, %s)" % (var_time, var_time, var_dt, var_target_time))
        while_code.append("")

        while_code.append("\tif %s.inUnitsOf(time_units).getValue() + 1.e-6 > %s.inUnitsOf(time_units).getValue():" % (
            var_time, var_target_time))
        while_code.append("\t\t%s = False" % var_compute)

        while_code.append("\t")
        while_code.append("\t%s = mupif.TimeStep.TimeStep(%s, %s, %s, n=%s)" % (
            var_time_step, var_time, var_dt, var_target_time, var_time_step_number))
        # while_code.append("\t")

        for block in self.getChildExecutionBlocks():
            while_code.extend(block.generateExecutionCode(1, "%s.getTime()" % var_time_step, var_time_step))

        code.extend(while_code)
        code.append("")

        return push_indents_before_each_line(code, indent)

    def generateCodeName(self, base_name='timeloop_'):
        ExecutionBlock.generateCodeName(self, base_name)


def linesToText(lines):
    text = ""
    for line in lines:
        text = "%s\n%s" % (text, line)
        return text


class CustomPythonCodeBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.code_lines = ["# CustomPythonBlock code"]
        self.updateLabel()
        self.fillColor = QtGui.QColor(255, 255, 255)

    def generateInitCode(self, indent=0):
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)
        code.extend(self.code_lines)
        return push_indents_before_each_line(code, indent)

    def setCodeLines(self, lines):
        self.code_lines = lines
        self.updateLabel()

    def paint(self, painter, option, widget):
        ExecutionBlock.paint(self, painter, option, widget)

    def updateLabel(self):
        """
        Updates the block's label according to the block's properties.
        """
        lenght = len(self.code_lines)
        if lenght > 1:
            self.label.setText("%d lines of code" % lenght)
        else:
            self.label.setText("%d line of code" % lenght)

    def addEditCodeItems(self, menu):
        sub_menu = menu.addMenu("Code")

        def _showCode():
            self.code_editor = QtWidgets.QTextEdit()
            for line in self.code_lines:
                self.code_editor.append(line)
            self.code_editor.resize(300, 300)
            self.code_editor.setReadOnly(True)
            self.code_editor.show()

        show_code = sub_menu.addAction("Show")
        show_code.triggered.connect(_showCode)

        def _editCode():
            self.code_editor = QtWidgets.QTextEdit()
            for line in self.code_lines:
                self.code_editor.append(line)
            self.code_editor.resize(300, 300)
            self.code_editor.show()

            def _saveCode():
                self.code_lines = self.code_editor.toPlainText().split("\n")
                self.updateLabel()
                print("Code has been saved.")

            self.code_editor.textChanged.connect(_saveCode)

        edit_code = sub_menu.addAction("Edit")
        edit_code.triggered.connect(_editCode)

        def _loadCode():
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self.workflow.widget.window,
                "Open Python code File",
                os.path.join(QtCore.QDir.currentPath(), "code.py"),
                "Python File (*.py)"
            )
            if file_path:
                f = open(file_path, "r")
                code = f.read()
                f.close()
                self.code_lines = code.split("\n")
                self.updateLabel()

        load_code = sub_menu.addAction("Load from file")
        load_code.triggered.connect(_loadCode)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addEditCodeItems(menu)

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'code_lines': self.code_lines})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        self.setCodeLines(json_data['code_lines'])


class CustomNameVariableBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.addDataSlot(InputDataSlot(self, "value", DataSlotType.Field, True))
        self.custom_name = ""
        self.updateLabel()

    def updateLabel(self):
        self.label.setText("var_name = '%s'" % self.custom_name)

    def generateCodeName(self, base_name='custom_name_variable_'):
        if self.custom_name != "":
            if self.custom_name not in self.workflow.getAllElementCodeNames():
                self.code_name = self.custom_name
                return
        ExecutionBlock.generateCodeName(self, base_name)

    def addLocalMenuItems(self, menu):
        def _set_custom_name():
            temp = QtWidgets.QInputDialog()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Set variable name", "", QtWidgets.QLineEdit.Normal, self.custom_name)
            if ok_pressed:
                self.custom_name = new_value
                self.updateLabel()

        action = menu.addAction("Set variable name")
        action.triggered.connect(_set_custom_name)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addLocalMenuItems(menu)

    def generateInitCode(self, indent=0):
        if self.getDataSlotWithName("value").connected():
            code = ExecutionBlock.generateInitCode(self)
            code.append("self.%s = None  # its value will be defined later by its execution code" % self.code_name)
            return push_indents_before_each_line(code, indent)
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)

        for slot in self.getDataSlots(InputDataSlot):
            linked_slot = slot.getLinkedDataSlot()
            if linked_slot:
                code.append("self.%s = %s" % (
                    self.code_name, linked_slot.owner.generateOutputDataSlotGetFunction(linked_slot, time)))

        return push_indents_before_each_line(code, indent)


class IfElseBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)

