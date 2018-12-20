from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from .helpers import getTextSize


class Button(QtWidgets.QGraphicsItem):
    """ """
    def __init__(self, parent, text, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, **kwargs)
        self.parent = parent
        self.text = text
        self.h = 20
        self.w = 20

        # self.fillColor_normal = QtGui.QColor(255, 255, 255)
        # self.fillColor_hover = QtGui.QColor(200, 200, 200)
        self.fillColor = QtGui.QColor(255, 255, 255)

        self.textColor = QtGui.QColor(0, 0, 0)

    def boundingRect(self):
        rect = QtCore.QRectF(self.x(),
                             self.y(),
                             self.w,
                             self.h)
        return rect

    def updatePosition(self):
        self.setX(self.parent.header.w / 2 - self.w / 2)
        self.setY(0)

    def paint(self, painter, option, widget):
        self.updatePosition()
        text_size = getTextSize(self.text, painter=painter)

        painter.setPen(QtGui.QPen(self.textColor))
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.drawRoundedRect(self.boundingRect(), self.parent.roundness, self.parent.roundness)

        painter.setPen(QtGui.QPen(self.textColor))

        painter.drawText(int(self.x() + (self.w - text_size.width()) / 2),
                         int(self.y() + (self.h + text_size.height() / 2) / 2),
                         self.text)

    def destroy(self):
        """Remove this object from the scene and delete it."""
        print("destroy button:", self)
        scene = self.parent.scene()
        scene.removeItem(self)
        del self

    # def hoverEnterEvent(self, e):
    #     print("button hover enter")
    #     self.fillColor = self.fillColor_hover
    #
    # def hoverLeaveEvent(self, e):
    #     print("button hover enter")
    #     self.fillColor = self.fillColor_normal

    def contextMenuEvent(self, event):
        self.parent.showMenu()

    def mousePressEvent(self, event):
        self.parent.showMenu()

