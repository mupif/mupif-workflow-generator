"""
Workflow editor widget

Requirements:
pip3 install pyqt5
pip3 install Qt.py
"""
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from . import GraphView
from . import Block


class GraphWidget (QtWidgets.QWidget):
    """ Represent workflow graph """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        # self.scene = Scene.Scene()
        self.view = GraphView.GraphView()
        self.window = parent
        self.scene = QtWidgets.QGraphicsScene()
        self.view.setScene(self.scene)
        self.workflow = Block.WorkflowBlock(self, self.scene)
        self.addNode(self.workflow)

        # self.layout = QtWidgets.QVBoxLayout()

        self.view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.view.setViewportUpdateMode(
            QtWidgets.QGraphicsView.FullViewportUpdate)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.view)
        self.setLayout(layout)

        self.nodeClasses = []

        # A cache for storing a representation of the current scene.
        # This is used for the Hold scene / Fetch scene feature.
        self.lastStoredSceneData = None
        # self.scene.addRect(0, 0, 10, 10, QtGui.QPen(QtCore.Qt.black), QtGui.QBrush(QtCore.Qt.transparent))

    def clearScene(self):
        """Remove everything in the current scene.
        FIXME: The GC does all the work here, which is probably not the
        finest solution, but works for now.
        """
        self.scene = QtWidgets.QGraphicsScene()
        self.view.setScene(self.scene)
        self.workflow = Block.WorkflowBlock(self, self.scene)
        self.addNode(self.workflow)

    def keyPressEvent(self, event):
        """React on various keys regarding Nodes."""

        # Delete selected nodes.
        if event.key() == QtCore.Qt.Key_Delete:
            selectedNodes = [i for i in self.scene.selectedItems()
                             if isinstance(i, Block.ExecutionBlock)]
            for node in selectedNodes:
                node.destroy()

        super(GraphWidget, self).keyPressEvent(event)

    def addWorkflowBlock(self):
        if not self.workflow:
            self.workflow = Block.WorkflowBlock(self, self.scene)
            self.addNode(self.workflow)
            return self.workflow
        return None

    def getWorkflowBlock(self):
        return self.workflow

    def addSceneMenuActions(self, menu):
        """Add scene specific actions like hold/fetch/save/load."""
        subMenu = menu.addMenu("Scene")

        clearSceneAction = subMenu.addAction("Clear")
        clearSceneAction.triggered.connect(self.clearScene)

        def _showAllElements():
            items = self.scene.items()
            for item in items:
                item.setVisible(True)

        showAllElements = subMenu.addAction("Show all elements")
        showAllElements.triggered.connect(_showAllElements)

    def contextMenuEvent(self, event):
        """Show a menu to create registered Nodes."""
        menu = QtWidgets.QMenu(self)
        # self.addNodesMenuActions(menu)
        self.addSceneMenuActions(menu)
        menu.exec(event.globalPos())

        super(GraphWidget, self).contextMenuEvent(event)

    def _createNode(self, _class, atMousePos=True, center=True):
        """The class must provide defaults in its constructor.
        We ensure the scene immediately has the Node added, otherwise
        the GC could snack it up right away.
        """
        node = _class()
        self.addNode(node)

        if atMousePos:
            mousePos = self.view.mapToScene(
                self.mapFromGlobal(QtGui.QCursor.pos()))
            node.setPos(mousePos)
        if center:
            self.view.centerOn(node.pos())

    def registerNodeClass(self, cls):
        if cls not in self.nodeClasses:
            self.nodeClasses.append(cls)
            print("registering %s", cls)

    def unregisterNodeClass(self, cls):
        if cls in self.nodeClasses:
            self.nodeClasses.remove(cls)

    def addNode(self, node):
        """Add a Node to the current scene.
        This is only necessary when the scene has not been passed on
        creation, e.g. when you create a Node programmatically.
        """
        if node not in self.scene.items():
            self.scene.addItem(node)

    def getNodeById(self, uuid):
        """Return Node that matches the given uuid string."""
        nodes = [i for i in self.scene.items() if isinstance(i, Block.ExecutionBlock)]
        for node in nodes:
            if node.uuid == uuid:
                return node
        return None

    def updateBlockPositions(self):
        d = self.getNodeById(0)
        d.widget.updateChildrenPosition()
        d.updateDataLinksPath()

    def getDataInJSON(self):
        """Returns JSON representation of the workflow"""

    def constructDataFromJSON(self, json_data):
        """Constructs the structure from JSON representation of the workflow"""



