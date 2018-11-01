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
from DataLink import *
from Button import *


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

    def moveChildBlock(self, block, direction):
        child_blocks = self.getChildExecutionBlocks()
        block_id = -5
        if block in child_blocks:
            block_id = child_blocks.index(block)

        if (direction == "up" and block_id > 0) or (direction == "down" and block_id < len(child_blocks)-1):
            scene = self.scene()
            for block in child_blocks:
                scene.removeItem(block)

            id = 0
            for block in child_blocks:
                if direction == "up" and id == block_id-1:
                    self.addExecutionBlock(child_blocks[block_id])

                if not id == block_id:
                    self.addExecutionBlock(block)

                if direction == "down" and id == block_id + 1:
                    self.addExecutionBlock(child_blocks[block_id])

                id += 1

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

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        print("showMenu call from %s defined in ExecutionBlock" % self.__class__.__name__)
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addMoveMenuActions(menu)
        self.addDeleteMenuActions(menu)
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


