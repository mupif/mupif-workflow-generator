"""Node header."""

# import Qt
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# import helpers
from helpers import getTextSize


class Header(QtWidgets.QGraphicsItem):
    """A Header is a child of a Node and gives it a title.

    Its width resizes automatically to match the Node's width.
    """
    def __init__(self, node, text, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, **kwargs)
        self.node = node
        self.text = text
        self.h = 20
        self.fillColor = QtGui.QColor(90, 90, 90)
        self.textColor = QtGui.QColor(240, 240, 240)

    def boundingRect(self):
        nodebox = self.node.boundingRect()
        rect = QtCore.QRectF(self.x(),
                             self.y(),
                             nodebox.width(),
                             self.h)
        return rect

    def paint(self, painter, option, widget):
        # Draw background rectangle.
        bbox = self.boundingRect()

        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        # painter.setBrush(self.fillColor)
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.drawRoundedRect(bbox,
                                self.node.roundness,
                                self.node.roundness)

        # Draw header label.
        if self.node.isSelected():
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
        else:
            painter.setPen(QtGui.QPen(self.textColor))

        # # centered text
        # text_size = getTextSize(painter, self.text)
        # painter.drawText(self.x() + (self.node.w - text_size.width()) / 2,
        #                  self.y() + (self.h + text_size.height() / 2) / 2,
        #                  self.text)

        # left aligned text
        text_size = getTextSize(self.text, painter=painter)
        painter.drawText(self.x() + self.node.spacing,
                         self.y() + (self.h + text_size.height() / 2) / 2,
                         self.text)

    def destroy(self):
        """Remove this object from the scene and delete it."""
        scene = self.node.scene()
        scene.removeItem(self)
        del self
