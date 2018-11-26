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

import mupif
import inspect
import importlib.util
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
            if len(iSlot.dataLinks) == 0 and iSlot.optional == False:
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
            return "self.%s.get(%s, %s)" % (self.code_name, slot.name, time)
        return ""

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
            elem.setTotalWidth(self.w-self.spacing*2)

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
        if is_parent_block:
            self.addMenuItems_AddStandardBlock(menu)
            self.addMenuItems_AddModelBlock(menu)

    def addCommonMenuActions(self, menu):
        if not isinstance(self, WorkflowBlock):
            self.addMoveMenuActions(menu)
            self.addDeleteMenuActions(menu)
        self.addCommonMenuActionsForParentBlocks(menu)

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
        while(True):
            i += 1
            new_name = "%s%d" % (base_name, i)
            if not new_name in self.workflow.getAllBlockCodeNames():
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

        ExecutionBlock.list_of_block_classes = []
        ExecutionBlock.list_of_block_classes.extend([TimeLoopBlock, VariableBlock, CustomPythonCodeBlock, IfElseBlock])

    def getScene(self):
        return self.loc_scene

    def getAllDataLinks(self):
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
                new_ds = ExternalInputDataSlot(self, e['name'], DataSlotType.getTypeFromName(e['type']))
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
            workflow_classname = "MyProblemClassWorkflow"
        else:
            workflow_classname = "MyProblemExecutionWorkflow"

        #

        self.generateAllBlockCodeNames()

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
                    params = "'name': '%s', 'type': '%s', 'optional': %s, 'description': '%s'" % (
                        s.name, DataSlotType.getNameFromType(s.type), False, "")

                    if code_add != "":
                        code_add = "%s, " % code_add
                    code_add = "%s{%s}" % (code_add, params)

            code.append("\t\tself.metadata.update({'inputs': [%s]})" % code_add)

            code_add = ""
            for s in self.getAllExternalDataSlots("in"):
                if s.connected():
                    params = "'name': '%s', 'type': '%s', 'optional': %s, 'description': '%s'" % (
                        s.name, DataSlotType.getNameFromType(s.type), True, "")

                    if code_add != "":
                        code_add = "%s, " % code_add
                    code_add = "%s{%s}" % (code_add, params)
            code.append("\t\tself.metadata.update({'outputs': [%s]})" % code_add)

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
                if i:
                    code_add += ", "
                code_add += "self.%s.getCriticalTimeStep()" % model.code_name
                i += 1
            code.append("\t\treturn min(%s)" % code_add)

        code.append("\t")

        # terminate

        code.append("\tdef terminate(self):")
        for model in all_model_blocks:
            if(isinstance(model, ModelBlock)):
                code.append("\t\tself.%s.terminate()" % model.code_name)
        code.append("\t")

        # solve or solveStep

        if class_code:
            code.append("\tdef solveStep(self, tstep, stageID=0, runInBackground=False):")
        else:
            code.append("\tdef solve(self, runInBackground=False):")

        for model in child_blocks:
            code.extend(model.generateExecutionCode(2))

        if not class_code:
            code.append("\t\tself.terminate()")
            code.append("")

        code.append("")

        # execution

        if not class_code:
            code.append("problem = %s()" % workflow_classname)
            code.append("problem.solve()")
            code.append("")
            code.append("")

        return replace_tabs_with_spaces_for_each_line(code)

    def getExecutionCode(self):
        return self.generateWorkflowCode(class_code=False)

    def getClassCode(self):
        return self.generateWorkflowCode(class_code=True)

    def getAllBlockCodeNames(self):
        return [block.code_name for block in self.getChildExecutionBlocks(None, True)]

    def generateAllBlockCodeNames(self):
        for block in self.getChildExecutionBlocks(None, True):
            block.code_name = ""
        for block in self.getChildExecutionBlocks(None, True):
            block.generateCodeName()


class VariableBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)
        self.value = 0.
        self.addDataSlot(OutputDataSlot(self, "value", DataSlotType.Scalar, False))
        self.getDataSlots()[0].displayName = "%le" % self.value
        self.variable_name = ""

    def addVariableBlockMenuItems(self, menu):
        sub_menu = menu.addMenu("Modify")

        def _changeValue():
            temp = QtWidgets.QInputDialog()
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter new value", "New value")
            if ok_pressed:
                self.value = float(new_value)
                self.getDataSlots()[0].displayName = "%le" % self.value

        change_value_action = sub_menu.addAction("Change value")
        change_value_action.triggered.connect(_changeValue)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addVariableBlockMenuItems(menu)

    def getValue(self):
        return self.value

    def setValue(self, val):
        self.value = val
        self.getDataSlots()[0].displayName = "%le" % self.value

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'value': self.getValue()})
        return answer

    def initializeFromJSONData(self, json_data):
        ExecutionBlock.initializeFromJSONData(self, json_data)
        self.setValue(json_data['value'])

    def generateCodeName(self, base_name='variable_'):
        ExecutionBlock.generateCodeName(self, base_name)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        return []

    def generateInitCode(self, indent=0):
        code = ExecutionBlock.generateInitCode(self)
        code.append("self.%s = %le" % (self.code_name, self.value))
        return push_indents_before_each_line(code, indent)

    def generateOutputDataSlotGetFunction(self, slot, time=''):
        return "self.%s" % self.code_name


class ModelBlock(ExecutionBlock):
    def __init__(self, parent, workflow, model=None, model_name=None):
        ExecutionBlock.__init__(self, parent, workflow)
        self.model = model
        self.name = model_name
        self.input_file = ""

    def setInputFile(self, input_file):
        self.input_file = input_file

    def getInputSlots(self):
        return self.model.getInputSlots()

    def getOutputSlots(self):
        return self.model.getOutputSlots()

    def generateInitCode(self, indent=0):
        code = ExecutionBlock.generateInitCode(self)
        input_file_add = ""
        if self.input_file != "":
            input_file_add = "file='%s', workdir='.'" % self.input_file
        code.append("self.%s = %s(%s)" % (self.code_name, self.name, input_file_add))
        return push_indents_before_each_line(code, indent)

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)

        for slot in self.getDataSlots(InputDataSlot):
            linked_slot = slot.getLinkedDataSlot()
            code.append("self.%s.set(%s)" % (
                self.code_name, linked_slot.owner.generateOutputDataSlotGetFunction(linked_slot, time)))

        code.append("self.%s.solveStep(%s)" % (self.code_name, timestep))

        return push_indents_before_each_line(code, indent)

    def getDictForJSON(self):
        answer = ExecutionBlock.getDictForJSON(self)
        answer.update({'model_classname': self.name})
        return answer

    def constructFromModelMetaData(self, model):
        if model.hasMetadata('name') and model.hasMetadata('inputs') and model.hasMetadata('outputs'):
            self.name = self.model = model.getMetadata('name')
            for slot in model.getMetadata('inputs'):
                self.addDataSlot(InputDataSlot(self, slot['name'], DataSlotType.getTypeFromName(slot['type']), slot['optional']))
            for slot in model.getMetadata('outputs'):
                self.addDataSlot(OutputDataSlot(self, slot['name'], DataSlotType.getTypeFromName(slot['type']), slot['optional']))
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
        def _set_input_file():
            temp = QtWidgets.QInputDialog()
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Enter input file name", "Input file:", QtWidgets.QLineEdit.Normal, self.input_file)
            if ok_pressed:
                self.input_file = new_value

        action = menu.addAction("Set input file")
        action.triggered.connect(_set_input_file)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addLocalMenuItems(menu)


class TimeLoopBlock(SequentialBlock):
    def __init__(self, parent, workflow):
        SequentialBlock.__init__(self, parent, workflow)
        self.addDataSlot(InputDataSlot(self, "start_time", DataSlotType.Scalar, False))
        self.addDataSlot(InputDataSlot(self, "target_time", DataSlotType.Scalar, False))

    def getStartTime(self):
        connected_slot = self.getDataSlotWithName("start_time").getLinkedDataSlot()
        if connected_slot:
            return connected_slot.owner.generateOutputDataSlotGetFunction(connected_slot)
        return "0."  # TODO call ERROR

    def getTargetTime(self):
        connected_slot = self.getDataSlotWithName("target_time").getLinkedDataSlot()
        if connected_slot:
            return connected_slot.owner.generateOutputDataSlotGetFunction(connected_slot)
        return "0."  # TODO call ERROR

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

        code.append("timeUnits = mupif.Physics.PhysicalQuantities.PhysicalUnit('s',   1.,    [0, 0, 1, 0, 0, 0, 0, 0, 0])")
        code.append("%s = time = mupif.Physics.PhysicalQuantities.PhysicalQuantity(%s, timeUnits)" % (
            var_time, self.getStartTime()))
        code.append("%s = mupif.Physics.PhysicalQuantities.PhysicalQuantity(%s, timeUnits)" % (
            var_target_time, self.getTargetTime()))
        code.append("%s = True" % var_compute)
        code.append("%s = 0" % var_time_step_number)

        code.append("while %s:" % var_compute)
        while_code = []

        code.append("\t%s += 1" % var_time_step_number)

        dt_code = "\t%s = min(" % var_dt
        first = True
        for model in self.getChildExecutionBlocks(ModelBlock):
            if not first:
                dt_code += ", "
            dt_code += "self.%s.getCriticalTimeStep()" % model.code_name
            first = False
        dt_code += ")"

        while_code.append("")
        while_code.append(dt_code)
        while_code.append("\t%s = min(%s+%s, %s)" % (var_time, var_time, var_dt, var_target_time))
        while_code.append("")

        while_code.append("\tif %s.inUnitsOf(timeUnits).getValue() + 1.e-6 > %s.inUnitsOf(timeUnits).getValue():" % (
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

    def generateInitCode(self, indent=0):
        return []

    def generateExecutionCode(self, indent=0, time='', timestep='tstep'):
        code = ExecutionBlock.generateExecutionCode(self)
        code.extend(self.code_lines)
        return push_indents_before_each_line(code, indent)

    def setCodeLines(self, lines):
        self.code_lines = lines

    def paint(self, painter, option, widget):
        ExecutionBlock.paint(self, painter, option, widget)

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

        load_code = sub_menu.addAction("Load from file")
        load_code.triggered.connect(_loadCode)

    def addMenuItems(self, menu):
        ExecutionBlock.addMenuItems(self, menu)
        self.addEditCodeItems(menu)


class IfElseBlock(ExecutionBlock):
    def __init__(self, parent, workflow):
        ExecutionBlock.__init__(self, parent, workflow)

