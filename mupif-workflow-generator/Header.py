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
    def __init__(self, parent, text, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, **kwargs)
        self.parent = parent
        self.text = text
        self.h = 20
        self.w = 20
        self.fillColor = QtGui.QColor(90, 90, 90)
        self.textColor = QtGui.QColor(240, 240, 240)

    def updateWidth(self):
        self.w = self.parent.w

    def boundingRect(self):
        self.updateWidth()
        rect = QtCore.QRectF(self.x(),
                             self.y(),
                             self.w,
                             self.h)
        return rect

    def paint(self, painter, option, widget):
        text_size = getTextSize(self.text, painter=painter)
        bbox = self.boundingRect()

        painter.setPen(QtGui.QPen(QtCore.Qt.NoPen))
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.drawRoundedRect(bbox,
                                self.parent.roundness,
                                self.parent.roundness)

        # Draw header label.
        if self.parent.isSelected():
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 0)))
        else:
            painter.setPen(QtGui.QPen(self.textColor))

        painter.drawText(self.x() + self.parent.spacing,
                         self.y() + (self.h + text_size.height() / 2) / 2,
                         self.text)

    def destroy(self):
        """Remove this object from the scene and delete it."""
        scene = self.parent.scene()
        scene.removeItem(self)
        del self
