""" """

# import Qt
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

# import helpers
from helpers import getTextSize


class Button(QtWidgets.QGraphicsItem):
    """ """
    def __init__(self, node, text, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, **kwargs)
        self.node = node
        self.text = text
        self.h = 20
        self.w = 20
        self.fillColor = QtGui.QColor(255, 255, 255)
        self.textColor = QtGui.QColor(0, 0, 0)

    def boundingRect(self):
        rect = QtCore.QRectF(self.x(),
                             self.y(),
                             self.w,
                             self.h)
        return rect

    def paint(self, painter, option, widget):
        # Draw background rectangle.
        text_size = getTextSize(self.text, painter=painter)
        self.w = text_size.width()+10

        painter.setPen(QtGui.QPen(self.textColor))
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.drawRoundedRect(self.boundingRect(), self.node.roundness, self.node.roundness)

        # rect = QtCore.QRectF(0, 0, 50, 50)
        # painter.drawRoundedRect(rect)

        painter.setPen(QtGui.QPen(self.textColor))

        # # centered text
        # text_size = getTextSize(painter, self.text)
        # painter.drawText(self.x() + (self.node.w - text_size.width()) / 2,
        #                  self.y() + (self.h + text_size.height() / 2) / 2,
        #                  self.text)

        # left aligned text

        painter.drawText(self.x(),
                         self.y() + (self.h + text_size.height() / 2) / 2,
                         self.text)

    def destroy(self):
        """Remove this object from the scene and delete it."""
        print("destroy header:", self)
        scene = self.node.scene()
        scene.removeItem(self)
        del self
