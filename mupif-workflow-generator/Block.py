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

# import Qt
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

import helpers
from exceptions import DuplicateKnobNameError, KnobConnectionError
import Header
from edge import Edge

import os

windows = os.name == "nt"
DELETE_MODIFIER_KEY = QtCore.Qt.AltModifier if windows else QtCore.Qt.ControlModifier


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

    def get(self, slot=None):
        """Returns the value associated with DataSlot"""
        return None

    def getOutputSlots(self):
        """Returns a list of output DataSlots"""
        return []


class DataConsumer:
    def __init__(self):
        """Constructor"""

    def set(self, value, slot=None):
        """sets the value associated with DataSlot"""
        return

    def getInputSlots(self):
        """Returns list of input DataSlots"""
        return []


# Currently only affects Knob label placement.
FLOW_LEFT_TO_RIGHT = "flow_left_to_right"
FLOW_RIGHT_TO_LEFT = "flow_right_to_left"


class DataSlot (QtWidgets.QGraphicsItem):
    """
    Class describing input/output parameter of block
    """
    def __init__(self, owner, name, type, optional=False,parent=None, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.name = name
        self.owner = owner
        self.type = type
        self.optional = optional

        # Qt
        self.x = 0
        self.y = 0
        self.w = 10
        self.h = 10

        self.margin = 5
        self.flow = FLOW_LEFT_TO_RIGHT

        self.maxConnections = -1  # A negative value means 'unlimited'.
        self.displayName = self.name

        self.labelColor = QtGui.QColor(10, 10, 10)
        self.fillColor = QtGui.QColor(130, 130, 130)
        self.highlightColor = QtGui.QColor(255, 255, 0)

        # Temp store for Edge currently being created.
        self.newEdge = None
        self.dataLinks = []  # data
        self.setAcceptHoverEvents(True)

    def __repr__(self):
        return "DataSlot (%s.%s %s)"%(self.owner.name, self.name, self.type)

    def node(self):
        """The Node that this Slot belongs to is its parent item."""
        return self.parentItem()

    def connectTo(self, slot):
        """Convenience method to connect this to another DataSlot.

        This creates an Edge and directly connects it, in contrast to the mouse
        events that first create an Edge temporarily and only connect if the
        user releases on a valid target Knob.
        """
        if slot is self:
            return

        self.checkMaxConnections(slot)

        edge = DataLink()
        edge.source = self
        edge.target = slot

        self.addDataConnection(edge)
        slot.addDataConnection(edge)

        edge.updatePath()

    def addDataConnection(self, edge):
        """Add the given Edge to the internal tracking list.

        This is only one part of the Slot connection procedure. It enables us to
        later traverse the whole graph and to see how many connections there
        currently are.

        Also make sure it is added to the QGraphicsScene, if not yet done.
        """
        self.dataLinks.append(edge)
        # print (self)
        scene = self.scene()
        # print (scene)
        if edge not in scene.items():
            scene.addItem(edge)

    def removeDataConnection (self, edge):
        """Remove th given Edge from the internal tracking list.

        If it is unknown, do nothing. Also remove it from the QGraphicsScene.
        """
        self.dataLinks.remove(edge)
        scene = self.scene()
        if edge in scene.items():
            scene.removeItem(edge)

    def boundingRect(self):
        """Return the bounding box of this Knob."""
        rect = QtCore.QRectF(self.x,
                             self.y,
                             self.w,
                             self.h)
        return rect

    def highlight(self, toggle):
        """Toggle the highlight color on/off.

        Store the old color in a new attribute, so it can be restored.
        """
        if toggle:
            self._oldFillColor = self.fillColor
            self.fillColor = self.highlightColor
        else:
            self.fillColor = self._oldFillColor

    def paint(self, painter, option, widget):
        """Draw the Knob's shape and label."""
        bbox = self.boundingRect()

        # Draw a filled rectangle.
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.drawRect(bbox)

        # Draw a text label next to it. Position depends on the flow.
        text_size = helpers.getTextSize(self.displayName, painter=painter)

        # if self.flow == FLOW_LEFT_TO_RIGHT:
        #     x = bbox.right() + self.margin
        # elif self.flow == FLOW_RIGHT_TO_LEFT:
        #     x = bbox.left() - self.margin - text_size.width()
        # else:
        #     raise UnknownFlowError(
        #         "Flow not recognized: {0}".format(self.flow))
        if self.__class__ == InputDataSlot:
            x = bbox.right() + self.margin
        else:
            x = bbox.left() - self.margin - text_size.width()
        y = bbox.bottom()

        painter.setPen(QtGui.QPen(self.labelColor))
        painter.drawText(x, y, self.displayName)

    def hoverEnterEvent(self, event):
        """Change the Slot's rectangle color."""
        self.highlight(True)
        super(DataSlot, self).hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        """Change the Slot's rectangle color."""
        self.highlight(False)
        super(DataSlot, self).hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        """Handle Edge creation."""
        if event.button() == QtCore.Qt.LeftButton:
            print("create dataLink")

            self.newEdge = Edge()
            self.newEdge.source = self
            self.newEdge.targetPos = event.scenePos()
            self.newEdge.updatePath()

            # Make sure this is removed if the user cancels.
            self.addDataConnection(self.newEdge)
            return

    def mouseMoveEvent(self, event):
        """Update Edge position when currently creating one."""
        if self.newEdge:
            print("update edge")
            self.newEdge.targetPos = event.scenePos()
            self.newEdge.updatePath()

    def mouseReleaseEvent(self, event):
        """Finish Edge creation (if validations are passed).

        TODO: This currently implements some constraints regarding the Knob
          connection logic, for which we should probably have a more
          flexible approach.
        """
        print("trying to connect two knobs (block)")
        if event.button() == QtCore.Qt.LeftButton:

            node = self.parentItem()
            scene = node.scene()
            x = event.scenePos().x()
            y = event.scenePos().y()
            print(x)
            print(y)
            qtr = QtGui.QTransform()
            target = scene.itemAt(x, y, qtr)
            # pos = event.scenePos()
            # target = QtGui.qApp.widgetsAt(pos)[0]

            # target = scene.itemAt(event.scenePos())

            try:
                if self.newEdge and target:

                    if self.newEdge.source is target:
                        raise KnobConnectionError(
                            "Can't connect a Knob to itself.")

                    if isinstance(target, DataSlot):
                        # self.addDataSlot(OutputDataSlot())  # ???

                        if type(self) == type(target):
                            raise KnobConnectionError(
                                "Can't connect Knobs of same type.")

                        if 1 == 0:
                            raise KnobConnectionError(
                                "Can't connect Knobs of different value types.")

                        newConn = set([self, target])
                        for edge in self.dataLinks:  # edges
                            existingConn = set([edge.source, edge.target])
                            diff = existingConn.difference(newConn)
                            if not diff:
                                raise KnobConnectionError(
                                    "Connection already exists.")
                                return

                        self.checkMaxConnections(target)

                        print("finish edge")
                        target.addDataConnection(self.newEdge)
                        self.newEdge.target = target
                        self.newEdge.updatePath()
                        self.finalizeEdge(self.newEdge)
                        self.newEdge = None
                        return

                raise KnobConnectionError(
                    "Edge creation cancelled by user.")

            except KnobConnectionError as err:
                print(err)
                # Abort Edge creation and do some cleanup.
                self.removeDataConnection(self.newEdge)
                self.newEdge = None

    def checkMaxConnections(self, slot):
        """Check if both this and the target Knob do accept another connection.

        Raise a KnobConnectionError if not.
        """
        no_limits = self.maxConnections < 0 and slot.maxConnections < 0
        if no_limits:
            return

        num_source_connections = len(self.dataLinks)  # Edge already added.
        num_target_connections = len(slot.dataLinks) + 1

        print(num_source_connections, num_target_connections)

        source_max_reached = num_source_connections > self.maxConnections
        target_max_reached = num_target_connections > slot.maxConnections

        if source_max_reached or target_max_reached:
            raise KnobConnectionError(
                "Maximum number of connections reached.")

    def finalizeEdge(self, edge):
        """This intentionally is a NoOp on the Knob baseclass.

        It is meant for subclass Knobs to implement special behaviour
        that needs to be considered when connecting two Knobs.
        """
        pass

    def destroy(self):
        """Remove this Slot, its Edges and associations."""
        print("destroy slot:", self)
        edges_to_delete = self.dataLinks[::]  # Avoid shrinking during deletion.
        for edge in edges_to_delete:
            edge.destroy()
        # node = self.parentItem()
        # if node:
        #     node.removeSlot(self)

        self.scene().removeItem(self)
        del self

    # def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
    #     temp = QtWidgets.QInputDialog()
    #     new_name, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Change name of the slot", "New name")
    #     if ok_pressed:
    #         self.name = new_name
    #         self.displayName = self.name

    def addSlotMenuActions(self, menu):
        subMenu = menu.addMenu("Data slot")

        def _rename():
            temp = QtWidgets.QInputDialog()
            new_name, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Change name of the slot", "New name")
            if ok_pressed:
                self.name = new_name
                self.displayName = self.name

        renameSlotAction = subMenu.addAction("Rename")
        renameSlotAction.triggered.connect(_rename)

        def _delete():
            self.destroy()
            print("TODO")

        deleteSlotAction = subMenu.addAction("Delete")
        deleteSlotAction.triggered.connect(_delete)

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addSlotMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())


def ensureEdgeDirection(edge):
    """Make sure the Edge direction is as described below.

       .source --> .target
    OutputKnob --> InputKnob

    Which basically translates to:

    'The Node with the OutputKnob is the child of the Node with the InputKnob.'

    This may seem the exact opposite way as expected, but makes sense
    when seen as a hierarchy: A Node which output depends on some other
    Node's input can be seen as a *child* of the other Node. We need
    that information to build a directed graph.

    We assume here that there always is an InputKnob and an OutputKnob
    in the given Edge, just their order may be wrong. Since the
    serialization relies on that order, it is enforced here.
    """
    print("ensure edge direction")
    if isinstance(edge.target, OutputDataSlot):
        assert isinstance(edge.source, InputDataSlot)
        current_target = edge.source
        edge.source = edge.target
        edge.target = current_target
    else:
        assert isinstance(edge.source, OutputDataSlot)
        assert isinstance(edge.target, InputDataSlot)

    print("src:", edge.source.__class__.__name__,
          "trg:", edge.target.__class__.__name__)


class InputDataSlot (DataSlot):
    """
    Class describing input/output parameter of block
    """
    def __init__(self, owner, name, type, optional=False):
        DataSlot.__init__(self, owner, name, type, optional)

    def __repr__(self):
        return "InputDataSlot (%s.%s %s)" % (self.owner.name, self.name, self.type)


class OutputDataSlot (DataSlot):
    """
    Class describing input/output parameter of block
    """
    def __init__ (self, owner, name, type, optional=False):
        DataSlot.__init__(self, owner, name, type, optional)

    def __repr__(self):
        return "OutputDataSlot (%s.%s %s)" % (self.owner.name, self.name, self.type)


class DataLink (QtWidgets.QGraphicsPathItem):
    """
    Represents a connection between source and receiver DataSlots
    """
    def __init__(self, input=None, output=None, **kwargs):
        super(DataLink, self).__init__(**kwargs)

        self.lineColor = QtGui.QColor(10, 10, 10)
        self.removalColor = QtCore.Qt.red
        self.thickness = 1

        self.source = None  # DataProvider slot
        self.target = None  # DataConsumer slot

        self.sourcePos = QtCore.QPointF(0, 0)
        self.targetPos = QtCore.QPointF(0, 0)

        self.curv1 = 0.6
        self.curv3 = 0.4

        self.curv2 = 0.2
        self.curv4 = 0.8

        self.setAcceptHoverEvents(True)

    def __str__(self):
        return "Datalink (%s -> %s)"%(self.source, self.target)

    def __repr__(self):
        return self.__str__()

    def mousePressEvent(self, event):
        """Delete Edge if icon is clicked with DELETE_MODIFIER_KEY pressed."""
        left_mouse = event.button() == QtCore.Qt.LeftButton
        mod = event.modifiers() == DELETE_MODIFIER_KEY
        if left_mouse and mod:
            self.destroy()

    def updatePath(self):
        """Adjust current shape based on Knobs and curvature settings."""
        if self.source:
            self.sourcePos = self.source.mapToScene(
                self.source.boundingRect().center())

        if self.target:
            self.targetPos = self.target.mapToScene(
                self.target.boundingRect().center())

        path = QtGui.QPainterPath()
        path.moveTo(self.sourcePos)

        dx = self.targetPos.x() - self.sourcePos.x()
        dy = self.targetPos.y() - self.sourcePos.y()

        ctrl1 = QtCore.QPointF(self.sourcePos.x() + dx * self.curv1,
                               self.sourcePos.y() + dy * self.curv2)
        ctrl2 = QtCore.QPointF(self.sourcePos.x() + dx * self.curv3,
                               self.sourcePos.y() + dy * self.curv4)
        path.cubicTo(ctrl1, ctrl2, self.targetPos)
        self.setPath(path)

    def paint(self, painter, option, widget):
        """Paint Edge color depending on modifier key pressed or not."""
        mod = QtWidgets.QApplication.keyboardModifiers() == DELETE_MODIFIER_KEY
        if mod:
            self.setPen(QtGui.QPen(self.removalColor, self.thickness))
        else:
            self.setPen(QtGui.QPen(self.lineColor, self.thickness))

        # self.setBrush(QtCore.Qt.NoBrush)
        self.setZValue(-1)
        super(DataLink, self).paint(painter, option, widget)

    def destroy(self):
        """Remove this Edge and its reference in other objects."""
        print("destroy edge:", self)
        if self.source:
            self.source.removeDataConnection(self)
        if self.target:
            self.target.removeDataConnection(self)
        del self


#
# Execution model
#
# class ExecutionBlock (Qt.QtWidgets.QGraphicsItem):


class ExecutionBlock (QtWidgets.QGraphicsWidget):
    """
    Abstract class representing execution block
    """
    def __init__(self, workflow, **kwargs):
        QtWidgets.QGraphicsWidget.__init__(self, kwargs.get("parent", None))
        # self.blockList = [] #blocks slots kept in self.childItems()
        self.variables = {}
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

        self.margin = 6
        self.roundness = 0
        self.fillColor = QtGui.QColor(220, 220, 220)
        self.addHeader(Header.Header(node=self, text=self.__class__.__name__))

        # General configuration.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setAcceptDrops(True)

    def setVariable(self, name, value):
        """Sets block variable"""

    def generateInitCode(self):
        """Generate initialization block code"""

    def generateCode(self):
        """returns tuple containing strings with code lines"""
        return ["block_execution"]

    def _getDataSlots(self):
        """Return a list of data slots."""
        return self.childItems()

    def getDataSlots (self, cls = None):
        """Return a list of data slots.
            If the optional `cls` is specified, return only Slots of that class.
            This is useful e.g. to get all Input or Output Slots.
        """
        slots= []
        for child in self._getDataSlots():
            if isinstance(child, DataSlot):
                slots.append(child)
        if cls:
            slots = list(filter(lambda k: k.__class__ is cls, slots))
        return slots

    def getDataSlotWithName (self, name):
        """Return matching data slot by its name, None otherwise."""
        for slot in self.getDataSlots():
            if slot.name == name:
                return slot
        return None

    def generateBlockInputs(self):
        inputSlots = self.getDataSlots(InputDataSlot)
        #print ("Slots: ",inputSlots)
        code = []
        # generate input code for each block input
        for iSlot in inputSlots:
            # try to locate corresponding dataLink
            #print (iLink)
            if (len(iSlot.dataLinks)==0 and iSlot.optional==False):
                #raise AttributeError("No input link for slot detected")
                code.append("# No input for slot %s detected"%(iSlot.name))
            elif (len(iSlot.dataLinks) > 1):
                raise AttributeError("Multiple input links for slot detected")
            else:
                source = iSlot.dataLinks[0]
                code.append("%s.set(name=%s, value=%s)" % (self.name,iSlot.name, source))
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
        #                    self.header.h)
        return rect

    def minimumWidth(self):
        return self.w

    def minimumHeight (self):
        return self.h

    def sizeHint (self, which, constraint):
        return QtCore.QSizeF(self.w, self.h)

    def updateSizeForChildren(self):
        """Adjust width and height as needed for header and knobs."""

        def adjustHeight():
            """Adjust height to fit header and all knobs."""
            slots = [c for c in self._getDataSlots() if isinstance(c, DataSlot)]
            #print (slots, self._getDataSlots())
            slotsHeight = sum([k.h + self.margin for k in slots])
            heightNeeded = self.header.h + slotsHeight + self.margin
            self.h = heightNeeded
            #print ("Adjusted height:", self.h)

        def adjustWidth():
            """Adjust width as needed for the widest child item."""
            headerWidth = (self.margin + helpers.getTextSize(self.header.text).width())

            slots = [c for c in self._getDataSlots() if isinstance(c, DataSlot)]
            slotWidths = [k.w + self.margin + helpers.getTextSize(k.displayName).width()
                          for k in slots]
            maxWidth = max([headerWidth] + slotWidths)
            #print (slotWidths)
            self.w = maxWidth + self.margin

        adjustWidth()
        adjustHeight()
        print (self, "height:", self.h, "width:", self.w)

    def addHeader(self, header):
        """Assign the given header and adjust the Node's size for it."""
        self.header = header
        header.setPos(self.pos())
        header.setParentItem(self)
        self.updateSizeForChildren()

    def addDataSlot(self, slot):
        """Add the given Slot to this Node.
        A Slot must have a unique name, meaning there can be no duplicates within
        a Node (the displayNames are not constrained though).
        Assign ourselves as the slot's parent item (which also will put it onto
        the current scene, if not yet done) and adjust or size for it.
        The position of the slot is set relative to this Node and depends on it
        either being an Input- or Output slot.
        """
        slotNames = [k.name for k in self.getDataSlots()]
        print("adding slot, existing Slots:", self.getDataSlots(), slotNames)
        if slot.name in slotNames:
            raise DuplicateKnobNameError(
                "Slot names must be unique, but {0} already exists."
                .format(slot.name))

        children = [c for c in self.childItems()]
        yOffset = sum([c.boundingRect().height() + self.margin for c in children])
        print (yOffset)
        xOffset = self.margin / 2

        slot.setParentItem(self)
        slot.margin = self.margin
        self.updateSizeForChildren()

        bbox = self.boundingRect()
        if isinstance(slot, OutputDataSlot):
            slot.setPos(bbox.right() - slot.w + xOffset, yOffset)
            pass
        elif isinstance(slot, InputDataSlot):
            slot.setPos(bbox.left() - xOffset, yOffset)
            pass

    def removeDataSlot(self, slot):
        """Remove the Knob reference to this node and resize."""
        slot.setParentItem(None)
        self.updateSizeForChildren()

    def addExecutionBlock(self, block):
        pass

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        return []

    def paint(self, painter, option, widget):
        """Draw the Node's container rectangle."""
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        # The bounding box is only as high as the header (we do this
        # to limit the area that is drag-enabled). Accommodate for that.
        bbox = self.boundingRect()
        print (self, bbox)
        painter.drawRoundedRect(self.x,
                                self.y,
                                self.w, #bbox.width(),
                                self.h,
                                self.roundness,
                                self.roundness)

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        print ("move:", self)
        nodes = self.scene().selectedItems()
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)

    def destroy(self):
        """Remove this Node, its Header, Knobs and connected Edges."""
        print("destroy node:", self)
        self.header.destroy()
        for slot in self.dataSlots():
            slot.destroy()

        scene = self.scene()
        scene.removeItem(self)
        del self

    def addAddSlotMenuActions(self, menu):
        subMenu = menu.addMenu("Add data slot")

        def _addInputSlot():
            self.addDataSlot(InputDataSlot(self, "new slot %d" % len(self.getDataSlots()), float, False))

        addInputSlotAction = subMenu.addAction("Input slot")
        addInputSlotAction.triggered.connect(_addInputSlot)

        def _addOutputSlot():
            self.addDataSlot(OutputDataSlot(self, "new slot %d" % len(self.getDataSlots()), float, False))

        addOutputSlotAction = subMenu.addAction("Output slot")
        addOutputSlotAction.triggered.connect(_addOutputSlot)

    def contextMenuEvent(self, event):
        temp = QtWidgets.QWidget()
        menu = QtWidgets.QMenu(temp)
        self.addAddSlotMenuActions(menu)
        menu.exec_(QtGui.QCursor.pos())

    # def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
    #     temp = QtWidgets.QInputDialog()
    #     new_name, ok_pressed = QtWidgets.QInputDialog.getText(temp, "Change name of the block", "New name")
    #     if ok_pressed:
    #         self.name = new_name

#
# Execution blocks: Implementation
#


class SequentialBlock (ExecutionBlock):
    """
    Implementation of sequential processing block
    """
    def __init__(self, workflow):
        self.canvas = QtWidgets.QGraphicsWidget()
        ExecutionBlock.__init__(self, workflow)
        #self.canvas = Qt.QtWidgets.QGraphicsWidget()
        self.layout = QtWidgets.QGraphicsLinearLayout()
        self.layout.setSpacing (20)
        self.canvas.setLayout(self.layout)
        self.canvas.setParentItem(self)

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtCore.Qt.yellow)
        self.canvas.setPalette(palette)
        #print (self.scene())
        #self.group = Qt.QtWidgets.QGraphicsItemGroup(parent=self)
        #print (self.group)

    def addExecutionBlock(self, block):
        print ("Adding block:", self, block)
        self.layout.addItem(block)
        self.adjustSize()
        self.updateSizeForChildren()

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        blocks= []
        for child in self.canvas.childItems():
            print (child)
            if isinstance(child, ExecutionBlock):
                blocks.append(child)
                if recursive :
                    blocks += child.getChildExecutionBlocks(cls, recursive)
        if cls:
            blocks = list(filter(lambda k: k.__class__ is cls, blocks))
        return blocks

    def generateCode(self):
        code = ["# Generating code for %s"%self.name]
        for iblock in self.getChildExecutionBlocks():
            code.append("# Generating code for %s"%(iblock.name))
            code.extend(iblock.generateBlockInputs()) # inputs generated based on block requirements
            code.extend(iblock.generateCode())
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
        #                    self.header.h)
        return rect

    def updateSizeForChildren(self):
        """Adjust width and height as needed for header and knobs."""
        ExecutionBlock.updateSizeForChildren(self)
        self.w = max(self.w, self.boundingRect().width())
        self.h = max(self.h, self.boundingRect().height())
        print("Canvas: ", self.boundingRect())
        print ("SeqBlock:", self, "height:", self.h, "width:", self.w)

    def paint(self, painter, option, widget):
        # get bounding box of childItems
        #painter.setBrush(QtGui.QBrush(self.fillColor))
        #painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        #childRect = self.childrenBoundingRect()
        #painter.drawRoundedRect(self.x,
        #                        self.y,
        #                        childRect.width(),
        #                        childRect.height(),
        #                        self.roundness,
        #                        self.roundness)

        ExecutionBlock.paint(self, painter, option, widget)

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        print ("move:", self)
        nodes = self.getChildExecutionBlocks(recursive=True)
        nodes.append(self)
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)


class WorkflowBlock(SequentialBlock):
    def __init__(self):
        SequentialBlock.__init__(self, self)
        self.name = "WorkflowBlock"

    def getExecutionBlockDataLinks (self, block, mode=""):
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
            icode=i
            whilecode.append(icode) # indented sequential code


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


class TimeLoopBlock (SequentialBlock):
    def __init__(self, workflow):
        SequentialBlock.__init__(self, workflow)
        self.addDataSlot(InputDataSlot(self, "target_time", float, False))
        self.addDataSlot(InputDataSlot(self, "start_time", float, False))

    def setVariable(self, name, value):
        self.variables[name] = value

    def generateCode(self):
        code = ["time=%(start_time)f" % self.variables,
                "while (time<=%(target_time)f):" % self.variables]
        whilecode = []
        dtcode = "deltaT = min("
        for i in self.getChildExecutionBlocks():
            if isinstance(i, ModelBlock):
                dtcode += ("%s.getCriticalTimeStep()" % i.name)
        dtcode+=")"
        whilecode.append(dtcode)
        whilecode.extend(SequentialBlock.generateCode(self))
        whilecode.append("time=min(time+deltaT, target_time)")

        code.append(whilecode)
        code.append("")

        return code
