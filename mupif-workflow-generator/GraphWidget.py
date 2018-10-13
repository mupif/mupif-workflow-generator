"""
Workflow editor widget

Requirements:
pip3 install pyqt5
pip3 install Qt.py
"""
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets

import GraphView
import Block
import os


class GraphWidget (QtWidgets.QWidget):
    """ Represent workflow graph """
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent=parent)

        self.scene = QtWidgets.QGraphicsScene()
        self.view = GraphView.GraphView()
        self.view.setScene(self.scene)

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

    def keyPressEvent(self, event):
        """React on various keys regarding Nodes."""

        # Delete selected nodes.
        if event.key() == QtCore.Qt.Key_Delete:
            selectedNodes = [i for i in self.scene.selectedItems()
                             if isinstance(i, Block.ExecutionBlock)]
            for node in selectedNodes:
                node.destroy()

        super(GraphWidget, self).keyPressEvent(event)

    def addSceneMenuActions(self, menu):
        """Add scene specific actions like hold/fetch/save/load."""
        subMenu = menu.addMenu("Scene")

        def _saveSceneAs():
            # filePath, _ = QtGui.QFileDialog.getSaveFileName(
            filePath, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Scene to JSON",
                os.path.join(QtCore.QDir.currentPath(), "scene.json"),
                "JSON File (*.json)"
            )
            if filePath:
                # sceneData = serializer.serializeScene(self.scene)
                sceneData = self.saveGeometry()
                serializer.saveSceneToFile(sceneData, filePath)

        saveToAction = subMenu.addAction("Save As...")
        saveToAction.triggered.connect(_saveSceneAs)

        def _loadSceneFrom():
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Scene JSON File",
                os.path.join(QtCore.QDir.currentPath(), "scene.json"),
                "JSON File (*.json)"
            )
            if filePath:
                sceneData = serializer.loadSceneFromFile(filePath)
                if sceneData:
                    self.clearScene()
                    serializer.reconstructScene(self, sceneData)

        loadFromAction = subMenu.addAction("Open File...")
        loadFromAction.triggered.connect(_loadSceneFrom)

        def _mergeSceneFrom():
            filePath, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Scene JSON File",
                os.path.join(QtCore.QDir.currentPath(), "scene.json"),
                "JSON File (*.json)"
            )
            if filePath:
                sceneData = serializer.mergeSceneFromFile(filePath)
                if sceneData:
                    # Select only new nodes so they can be moved.
                    old_nodes = set(self.view.nodes())
                    serializer.reconstructScene(self, sceneData)
                    all_nodes = set(self.view.nodes())
                    merged_nodes = all_nodes - old_nodes
                    for node in merged_nodes:
                        node.setSelected(True)

        mergeFromAction = subMenu.addAction("Merge File...")
        mergeFromAction.triggered.connect(_mergeSceneFrom)

        subMenu.addSeparator()

        def _storeCurrentScene():
            self.lastStoredSceneData = serializer.serializeScene(self.scene)
            QtWidgets.QMessageBox.information(self, "Hold",
                                          "Scene state holded.")

        holdAction = subMenu.addAction("Hold")
        holdAction.triggered.connect(_storeCurrentScene)

        def _loadLastStoredScene():
            if not self.lastStoredSceneData:
                print("scene data is empty, nothing to load")
                return
            self.clearScene()
            serializer.reconstructScene(self, self.lastStoredSceneData)
            QtWidgets.QMessageBox.information(self, "Fetch",
                                          "Scene state fetched.")

        fetchAction = subMenu.addAction("Fetch")
        fetchAction.triggered.connect(_loadLastStoredScene)

        subMenu.addSeparator()

        clearSceneAction = subMenu.addAction("Clear")
        clearSceneAction.triggered.connect(self.clearScene)

        subMenu.addSeparator()

        def _layoutScene():
            # self.layout()
            # QtWidgets.QWidget.setLayout(self.layout())
            # autoLayout(self.scene)
            self.view.redrawEdges()

        layoutSceneAction = subMenu.addAction("Auto Layout")
        layoutSceneAction.triggered.connect(_layoutScene)

        def _addWorkflowBlock():
            new_workflow = Block.WorkflowBlock(self.scene)
            self.addNode(new_workflow)

        addWorkflowBlockAction = subMenu.addAction("Add WorkflowBlock")
        addWorkflowBlockAction.triggered.connect(_addWorkflowBlock)

        def _showAllElements():
            items = self.scene.items()
            for item in items:
                item.setVisible(True)

        showAllElements = subMenu.addAction("Show all elements")
        showAllElements.triggered.connect(_showAllElements)

    # def addNodesMenuActions(self, menu):
    #     subMenu = menu.addMenu("Nodes")
    #
    #     def _passNode():
    #         pass
    #
    #     nid = 0
    #     for node in self.scene.items():
    #         nid += 1
    #         someAction = subMenu.addAction("Node_%d" % nid)
    #         someAction.triggered.connect(_passNode)
    #
    #     for cls in self.nodeClasses:
    #         action = subMenu.addAction(cls.__name__)
    #
    #         def actionf(cc):
    #             return lambda: self._createNode(cc)
    #         print ("Adding action", self, cls.__name__, cls)
    #         action.triggered.connect(actionf(cls))

    def contextMenuEvent(self, event):
        """Show a menu to create registered Nodes."""
        menu = QtWidgets.QMenu(self)
        # self.addNodesMenuActions(menu)
        self.addSceneMenuActions(menu)
        menu.exec_(event.globalPos())

        super(GraphWidget, self).contextMenuEvent(event)

    def _createNode(self, _class, atMousePos=True, center=True):
        """The class must provide defaults in its constructor.
        We ensure the scene immediately has the Node added, otherwise
        the GC could snack it up right away.
        """
        #print ("Node created", self, _class)
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
        nodes = [i for i in self.scene.items() if isinstance(i, Node)]
        for node in nodes:
            if node.uuid == uuid:
                return node
        return None

    def updateBlockPositions(self):
        d = self.getNodeById(0)
        d.widget.updateChildrenPosition()
        d.updateDataLinksPath()

