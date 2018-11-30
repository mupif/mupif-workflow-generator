from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import helpers


class Label(QtWidgets.QGraphicsItem):
    """"""
    def __init__(self, owner, text='', parent=None, **kwargs):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.text = ""
        self.lines = []
        self.owner = owner
        self.setParentItem(self.owner)

        self.line_h = 14

        # Qt
        self.x = 0
        self.y = 0
        self.w = 14
        self.h = 14

        self.spacing = 5

        self.text_color = QtGui.QColor(10, 10, 10)

        self.setText(text, initialization=True)

    def __repr__(self):
        return "Label (%s.label: '%s')" % (self.owner.name, self.text)

    def getWidth(self):
        return self.w*len(self.lines)

    def getHeight(self):
        return self.h

    def paint(self, painter, option, widget):
        """Draw the label."""
        if self.shouldBePainted():
            text_size = helpers.getTextSize(self.text, painter=painter)
            self.w = text_size.width()
            painter.setPen(QtGui.QPen(self.text_color))
            y = int(self.y+self.line_h)
            self.lines = self.text.split('\n')
            for line in self.lines:
                painter.drawText(int(self.x), y, line)
                y += int(self.line_h)

    def shouldBePainted(self):
        if self.text == '':
            return False
        return True

    def boundingRect(self):
        rect = QtCore.QRectF(self.x,
                             self.y,
                             self.w,
                             self.h)
        return rect

    def setText(self, val, initialization=False):
        self.text = val
        self.lines = self.text.split('\n')
        self.h = self.line_h*len(self.lines)
        if not initialization:
            self.owner.callUpdatePositionOfWholeWorkflow()

    def getNeededWidth(self):
        max_width = 0
        for line in self.lines:
            width = helpers.getTextSize(line).width()
            if width > max_width:
                max_width = width
        return int(max_width)

