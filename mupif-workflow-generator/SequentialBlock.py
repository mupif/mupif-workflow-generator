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


from ExecutionBlock import *


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


class SequentialBlock (ExecutionBlock):
    """
    Implementation of sequential processing block
    """
    def __init__(self, workflow):
        self.canvas = QtWidgets.QGraphicsWidget()
        ExecutionBlock.__init__(self, workflow)
        self.layout = QtWidgets.QGraphicsLinearLayout()
        self.layout.setSpacing(self.spacing)
        self.canvas.setLayout(self.layout)
        self.canvas.setParentItem(self)

        palette = QtGui.QPalette()
        palette.setColor(QtGui.QPalette.Window, QtCore.Qt.yellow)
        self.canvas.setPalette(palette)

    def addExecutionBlock(self, block):
        print ("Adding block:", self, block)
        self.layout.addItem(block)
        self.adjustSize()
        block.workflow.updateChildrenSizeAndPositionAndResizeSelf()
        # self.updateSizeForChildren()

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        blocks = []
        for child in self.canvas.childItems():
            print (child)
            if isinstance(child, ExecutionBlock):
                blocks.append(child)
                if recursive:
                    blocks += child.getChildExecutionBlocks(cls, recursive)
        if cls:
            blocks = list(filter(lambda k: k.__class__ is cls, blocks))
        return blocks

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
        #                    self.header.h)
        return rect

    # def updateSizeForChildren(self):
    #     """Adjust width and height as needed for header and knobs."""
    #     ExecutionBlock.updateSizeForChildren(self)
    #     self.w = max(self.w, self.boundingRect().width())
    #     self.h = max(self.h, self.boundingRect().height())
    #     print("Canvas: ", self.boundingRect())
    #     print ("SeqBlock:", self, "height:", self.h, "width:", self.w)

    def paint(self, painter, option, widget):
        # get bounding box of childItems
        # painter.setBrush(QtGui.QBrush(self.fillColor))
        # painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))

        # childRect = self.childrenBoundingRect()
        # painter.drawRoundedRect(self.x,
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
        print("move:", self)
        nodes = self.getChildExecutionBlocks(recursive=True)
        nodes.append(self)
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(ExecutionBlock, self).mouseMoveEvent(event)

