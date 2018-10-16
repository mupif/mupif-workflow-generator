"""Window class."""
import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import DataLink
import Block
import GraphWidget


CURRENT_ZOOM = 1.0
ALTERNATE_MODE_KEY = QtCore.Qt.Key_Alt


class Window(QtWidgets.QMainWindow):

    def __init__(self):
        super(Window, self).__init__()
        self.setGeometry(50, 50, 800, 800)
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)
        self.setWindowTitle("MuPIF Workflow Generator")
        # self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))

        # extractAction = QtWidgets.QAction("GET TO THE CHOPPAH!!!")
        # extractAction.setShortcut("Ctrl+Q")
        # extractAction.setStatusTip('Leave The App')
        # extractAction.triggered.connect(self.close_application)
        # def _extractAction():
        #     sys.exit()
        self.widget = GraphWidget.GraphWidget(self)
        self.resizeEvent(None)

        self.statusBar()

        # window menu definition
        main_menu = self.menuBar()
        #
        main_menu.setNativeMenuBar(False)
        workflow_menu = main_menu.addMenu('Workflow')
        workflow_action_generate_class_code = QtWidgets.QAction('Generate class code', self)
        workflow_action_generate_execution_code = QtWidgets.QAction('Generate execution code', self)
        workflow_action_save_to_file = QtWidgets.QAction('Save to file', self)
        workflow_action_load_from_file = QtWidgets.QAction('Load from file', self)
        workflow_menu.addAction(workflow_action_generate_class_code)
        workflow_menu.addAction(workflow_action_generate_execution_code)
        workflow_menu.addAction(workflow_action_save_to_file)
        workflow_menu.addAction(workflow_action_load_from_file)
        #
        apis_menu = main_menu.addMenu('APIs')
        apis_action_load_from_file = QtWidgets.QAction('Load API from file', self)
        apis_action_show_list = QtWidgets.QAction('List of available APIs', self)
        apis_menu.addAction(apis_action_load_from_file)
        apis_menu.addAction(apis_action_show_list)

        # fileMenu.triggered.connect(sys.exit)

        self.show()

    # def home(self):
    #     btn = QtWidgets.QPushButton("Quit", self)
    #     btn.clicked.connect(self.close_application)
    #     btn.resize(btn.minimumSizeHint())
    #     btn.move(10, 30)
    #     self.show()

    def close_application(self):
        print("whooaaaa so custom!!!")
        sys.exit()

    def resizeEvent(self, QResizeEvent):
        self.widget.setGeometry(10, 20, self.width() - 20, self.height() - 30)
