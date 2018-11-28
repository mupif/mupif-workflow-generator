from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import helpers


class Label(QtWidgets.QGraphicsItem):
    """"""
    def __init__(self, owner, text='', parent=None, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.text = text
        self.owner = owner
        self.setParentItem(self.owner)

        # Qt
        self.x = 0
        self.y = 0
        self.w = 14
        self.h = 14

        self.spacing = 5

        self.text_color = QtGui.QColor(10, 10, 10)

    def __repr__(self):
        return "Label (%s.label: '%s')" % (self.owner.name, self.text)

    def getWidth(self):
        return self.w

    def getHeight(self):
        return self.h

    def paint(self, painter, option, widget):
        """Draw the label."""
        if self.shouldBePainted():
            text_size = helpers.getTextSize(self.text, painter=painter)
            self.w = text_size.width()
            painter.setPen(QtGui.QPen(self.text_color))
            painter.drawText(int(self.x), int(self.y+self.h), self.text)

    def shouldBePainted(self):
        if self.text == '':
            return False
        return True

