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


class ExecutionBlock (QtWidgets.QGraphicsWidget):
    """
    Abstract class representing execution block
    """
    list_of_models = []

    def __init__(self, workflow, **kwargs):
        QtWidgets.QGraphicsWidget.__init__(self, kwargs.get("parent", None))
        # self.blockList = [] blocks kept in self.childItems()
        # self.dataSlots = [] data slots kept in self.childItems()
        self.workflow = workflow
        self.name = kwargs.get("name", "ExecutionBlock")

        # This unique id is useful for serialization/reconstruction.
        self.uuid = str(uuid.uuid4())
        # self.header = None

        self.x = 0
        self.y = 0
        self.w = 10
        self.h = 10

        self.spacing = 8
        # self.margin = self.spacing
        self.roundness = 0
        self.fillColor = QtGui.QColor(220, 220, 220)

        # self.addHeader(Header.Header(node=self, text=self.__class__.__name__))
        self.header = Header.Header(node=self, text=self.__class__.__name__)
        self.header.setPos(self.pos())
        self.header.setParentItem(self)
        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()

        # General configuration.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        # self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setAcceptDrops(True)

        self.children_visible = True

    def generateInitCode(self):
        """Generate initialization block code"""

    def generateCode(self):
        """returns tuple containing strings with code lines"""
        return ["block_execution"]

    def getChildItems(self):
        return self.childItems()

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

    def getDataSlotWithName(self, name):
        """Return matching data slot by its name, None otherwise."""
        for slot in self.getDataSlots():
            if slot.name == name:
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
        slot.setParentItem(None)
        self.callUpdatePositionOfWholeWorkflow()

    def addExecutionBlock(self, block):
        block.setParentItem(self)

        self.callUpdatePositionOfWholeWorkflow()

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        blocks = []
        # for child in self.canvas.childItems():
        for child in self.childItems():
            print (child)
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

    def updateChildrenPosition_temp(self):

        slot_widths = [k.w + self.spacing * 3 + helpers.getTextSize(k.displayName).width() for k in self.getDataSlots()]
        slot_widths.append(0)
        max_slot_width = max(slot_widths)

        self.header.setY(0)
        self.header.setX(0)

        header_width = (2*self.spacing + helpers.getTextSize(self.header.text).width())
        width_child_max = max(header_width, max_slot_width)
        height_children = self.header.h + self.spacing

        # update data slots
        for elem in self.getDataSlots():
            elem.setY(height_children)
            print("Setting y of %s to %d" % (elem.__class__.__name__, height_children))
            width_child_max = max(width_child_max, elem.w)
            print("%s - w=%d" % (elem.name, elem.w))
            height_children += elem.h + self.spacing

        # update blocks
        for elem in self.getChildExecutionBlocks():
            # elem.updateChildrenPosition_temp()
            elem.setY(height_children)
            width_child_max = max(width_child_max, elem.w)
            print("%s - w=%d" % (elem.name, elem.w))

            height_children += elem.h + self.spacing
            elem.setX(self.spacing)

        # TODO check why it causes wider workflow block than necessary
        # rect = self.childrenBoundingRect()
        # if rect.width() > width_child_max:
        #     # if not isinstance(self, ExecutionBlock):
        #     width_child_max = rect.width()

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

        self.updateChildrenPosition_temp()

    def callUpdatePositionOfWholeWorkflow(self):
        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()

    def paint(self, painter, option, widget):
        """Draw the Node's container rectangle."""
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        # The bounding box is only as high as the header (we do this
        # to limit the area that is drag-enabled). Accommodate for that.
        bbox = self.boundingRect()
        print(self, bbox)
        painter.drawRoundedRect(self.x,
                                self.y,
                                self.w,  # bbox.width()
                                self.h,
                                self.roundness,
                                self.roundness)

    def updateDataLinksPath(self):
        # nodes = self.scene().selectedItems()
        nodes = self.getChildExecutionBlocks(None, True)
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        print("move:", self)
        nodes = self.scene().selectedItems()
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)

    def destroy(self):
        """Remove this Node, its Header, Knobs and connected Edges."""
        # TODO fix it
        print("destroy node:", self)
        self.header.destroy()
        for slot in self.dataSlots():
            slot.destroy()

        scene = self.scene()
        scene.removeItem(self)
        del self

    def addAddSlotMenuActions(self, menu):
        sub_menu = menu.addMenu("Add data slot")

        def _addInputSlot():
            self.addDataSlot(InputDataSlot(self, "new slot %d" % len(self.getDataSlots()), float, False))

        add_input_slot_action = sub_menu.addAction("Input slot")
        add_input_slot_action.triggered.connect(_addInputSlot)

        def _addOutputSlot():
            self.addDataSlot(OutputDataSlot(self, "new slot %d" % len(self.getDataSlots()), float, False))

        add_output_slot_action = sub_menu.addAction("Output slot")
        add_output_slot_action.triggered.connect(_addOutputSlot)

    def addShowHideMenuActions(self, menu):
        def _showHideChildren():
            if self.children_visible:
                self.children_visible = False
            else:
                self.children_visible = True

            blocks = self.childItems()
            i = 0
            for block in blocks:
                if i and ((not isinstance(block, InputDataSlot) and not isinstance(block, OutputDataSlot)) or self.children_visible):
                    block.setVisible(self.children_visible)
                i += 1

        if self.children_visible:
            show_hide_text = "Hide"
        else:
            show_hide_text = "Show"

        add_show_hide_children = menu.addAction("%s child elements" % show_hide_text)
        add_show_hide_children.triggered.connect(_showHideChildren)

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addAddSlotMenuActions(menu)
        self.addShowHideMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())

    # def resizeMe(self, w, h):
    #     self.w = w
    #     self.h = h

    # def resizeForChildren(self):
    #     print("\n\nRESIZING ---------------------------------\n\n")
    #     rect = self.childrenBoundingRect()
    #
    #     self.resizeMe(rect.width(), rect.height())
    #     # rect = QtCore.QRectF(10, 10, 100, 100)
    #     # self.setGeometry(rect)

    # def updateChildrenPosition(self, color_id=0):
    #     print("\nPositioning child blocks of %s\n" % self.name)
    #     if color_id:
    #         self.fillColor = QtGui.QColor(220, 220, 220)
    #         child_color_id = 0
    #
    #     else:
    #         self.fillColor = QtGui.QColor(180, 180, 180)
    #         child_color_id = 1
    #
    #     width_child_max = 0
    #     height_children = self.header.h + 10
    #     child_blocks = self.getChildExecutionBlocks()
    #
    #     child_slots = self.getDataSlots()
    #     for slot in child_slots:
    #         if slot.w > width_child_max:
    #             width_child_max = slot.w
    #         print("%s - w=%d" % (slot.name, slot.w))
    #
    #         height_children += slot.h + 10
    #
    #     for block in child_blocks:
    #         block.updateChildrenPosition(child_color_id)
    #         block.setY(height_children)
    #         if block.w > width_child_max:
    #             width_child_max = block.w
    #         print("%s - w=%d" % (block.name, block.w))
    #
    #         height_children += block.h + 10
    #         block.setX(20)
    #
    #     rect = self.childrenBoundingRect()
    #     if rect.width() > width_child_max:
    #         # if not isinstance(self, ExecutionBlock):
    #         width_child_max = rect.width()
    #     print("%s's rect - w=%d" % (self.name, rect.width()))
    #
    #     self.h = height_children + 10
    #     self.w = width_child_max + 40
    #
    #     print("setting %s - w=%d" % (self.name, self.w))
    #
    #     for slot in child_slots:
    #         if isinstance(slot, InputDataSlot):
    #             slot.setX(20)
    #         else:
    #             slot.setX(self.w-slot.w-20)
    #
    #             print("\nEND of positioning child blocks of %s\n" % self.name)
