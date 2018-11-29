"""Window class."""
import sys
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5 import QtWidgets
import DataLink
import Block
import GraphWidget
import os
import json


CURRENT_ZOOM = 1.0
ALTERNATE_MODE_KEY = QtCore.Qt.Key_Alt


class Window(QtWidgets.QMainWindow):

    def __init__(self, parent):
        super(Window, self).__init__()
        self.application = parent
        self.setGeometry(50, 50, 800, 1000)
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

        def _new_blank_workflow():
            self.widget.clearScene()

        def _save_to_json_file():
            json_code = self.widget.workflow.convertToJSON()
            overall_json = {'elements': json_code}
            json_to_be_saved = json.dumps(overall_json)
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                "Save Workflow to JSON File",
                os.path.join(QtCore.QDir.currentPath(), "scene.json"),
                "JSON File (*.json)"
            )
            if file_path:
                f = open(file_path, "w")
                f.write(json_to_be_saved)
                f.close()

        def _load_from_json_file():
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Workflow JSON File",
                os.path.join(QtCore.QDir.currentPath(), "scene.json"),
                "JSON File (*.json)"
            )
            if file_path:
                f = open(file_path, "r")
                json_loaded = f.read()
                f.close()
                json_data = json.loads(json_loaded)

                self.widget.clearScene()
                self.widget.workflow.loadFromJSON(json_data)

        def _load_models():
            file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self,
                "Open Python File",
                os.path.join(QtCore.QDir.currentPath(), "model.py"),
                "Python File (*.py)"
            )
            if file_path:
                Block.ModelBlock.loadModelsFromGivenFile(file_path)
                self.updateMenuListOfAPI()

        def formatCodeToText(code, level=-1):
            text_code = ""
            if isinstance(code, str):
                text_code += "%s%s\n" % ('\t' * level, code)
            else:
                for line in code:
                    text_code += formatCodeToText(line, level + 1)
            return text_code

        def printCode(code, level=-1):
            print(formatCodeToText(code, level))

        def _generate_class_code():
            if self.widget.workflow.checkConsistency(execution=False):
                code = self.widget.workflow.getClassCode()
                # temporary printing into console
                print("\nClass code:\n\n%s" % formatCodeToText(code))
                # saving into file
                file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    "Save Python Class Code to File",
                    os.path.join(QtCore.QDir.currentPath(), "class_code.py"),
                    "Python File (*.py)"
                )
                if file_path:
                    f = open(file_path, "w")
                    f.write(formatCodeToText(code))
                    f.close()
            else:
                print("Workflow.checkConsistency() returned False")
                QtWidgets.QMessageBox.about(self, "Workflow consistency error",
                                            "Workflow.checkConsistency() returned False\nCheck whether all Compulsory "
                                            "DataSlots are connected.")

        def _show_class_code():
            if self.widget.workflow.checkConsistency(execution=False):
                code = self.widget.workflow.getClassCode()
                self.code_editor = QtWidgets.QTextEdit()
                for line in code:
                    self.code_editor.append(line)
                self.code_editor.resize(300, 300)
                self.code_editor.setReadOnly(True)
                self.code_editor.show()
            else:
                print("Workflow.checkConsistency() returned False")
                QtWidgets.QMessageBox.about(self, "Workflow consistency error",
                                            "Workflow.checkConsistency() returned False\nCheck whether all Compulsory "
                                            "DataSlots are connected.")

        def _generate_execution_code():
            if self.widget.workflow.checkConsistency(execution=True):
                code = self.widget.workflow.getExecutionCode()
                # temporary printing into console
                print("\nExecution code:\n\n%s" % formatCodeToText(code))
                # saving into file
                file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                    self,
                    "Save Python Execution Code to File",
                    os.path.join(QtCore.QDir.currentPath(), "execution_code.py"),
                    "Python File (*.py)"
                )
                if file_path:
                    f = open(file_path, "w")
                    f.write(formatCodeToText(code))
                    f.close()
            else:
                print("Workflow.checkConsistency() returned False")
                QtWidgets.QMessageBox.about(self, "Workflow consistency error",
                                            "Workflow.checkConsistency() returned False\nCheck whether all Compulsory "
                                            "DataSlots are connected.\nExecution Workflow also cannot contain external "
                                            "DataSlots.")

        def _show_execution_code():
            if self.widget.workflow.checkConsistency(execution=True):
                code = self.widget.workflow.getExecutionCode()
                self.code_editor = QtWidgets.QTextEdit()
                for line in code:
                    self.code_editor.append(line)
                self.code_editor.resize(300, 300)
                self.code_editor.setReadOnly(True)
                self.code_editor.show()
            else:
                print("Workflow.checkConsistency() returned False")
                QtWidgets.QMessageBox.about(self, "Workflow consistency error",
                                            "Workflow.checkConsistency() returned False\nCheck whether all Compulsory "
                                            "DataSlots are connected.\nExecution Workflow also cannot contain external "
                                            "DataSlots.")

        def _run_execution_code():
            if self.widget.workflow.checkConsistency(execution=True):
                code = self.widget.workflow.getExecutionCode()
                temp_file = 'sldfjlksdajlvkasd.py'
                f = open(temp_file, "w")
                f.write(formatCodeToText(code))
                f.close()
                os.system("python3 %s" % temp_file)
            else:
                print("Workflow.checkConsistency() returned False")
                QtWidgets.QMessageBox.about(self, "Workflow consistency error",
                                            "Workflow.checkConsistency() returned False\nCheck whether all Compulsory "
                                            "DataSlots are connected.\nExecution Workflow also cannot contain external "
                                            "DataSlots.")

        main_menu.setNativeMenuBar(False)
        workflow_menu = main_menu.addMenu('Workflow')
        #
        workflow_action_new_blank_workflow = QtWidgets.QAction('New blank workflow', self)
        workflow_action_new_blank_workflow.triggered.connect(_new_blank_workflow)
        workflow_action_new_blank_workflow.setShortcut("Ctrl+N")

        workflow_action_show_class_code = QtWidgets.QAction('Show class code', self)
        workflow_action_show_class_code.triggered.connect(_show_class_code)

        workflow_action_save_class_code = QtWidgets.QAction('Save class code', self)
        workflow_action_save_class_code.triggered.connect(_generate_class_code)

        workflow_action_save_execution_code = QtWidgets.QAction('Save execution code', self)
        workflow_action_save_execution_code.triggered.connect(_generate_execution_code)

        workflow_action_show_execution_code = QtWidgets.QAction('Show execution code', self)
        workflow_action_show_execution_code.triggered.connect(_show_execution_code)

        workflow_action_run_execution_code = QtWidgets.QAction('Run execution code', self)
        workflow_action_run_execution_code.triggered.connect(_run_execution_code)

        workflow_action_save_to_file = QtWidgets.QAction('Save to file', self)
        workflow_action_save_to_file.triggered.connect(_save_to_json_file)
        workflow_action_save_to_file.setShortcut("Ctrl+S")

        workflow_action_load_from_file = QtWidgets.QAction('Load from file', self)
        workflow_action_load_from_file.triggered.connect(_load_from_json_file)
        workflow_action_load_from_file.setShortcut("Ctrl+L")
        #
        workflow_menu.addAction(workflow_action_new_blank_workflow)
        workflow_menu.addAction(workflow_action_show_class_code)
        workflow_menu.addAction(workflow_action_save_class_code)
        workflow_menu.addAction(workflow_action_show_execution_code)
        workflow_menu.addAction(workflow_action_save_execution_code)
        workflow_menu.addAction(workflow_action_run_execution_code)
        workflow_menu.addAction(workflow_action_save_to_file)
        workflow_menu.addAction(workflow_action_load_from_file)
        #
        self.apis_menu = main_menu.addMenu('APIs')
        apis_action_load_from_file = QtWidgets.QAction('Load API from file', self)
        apis_action_load_from_file.triggered.connect(_load_models)
        self.apis_menu.addAction(apis_action_load_from_file)

        self.apis_list_of_models = self.apis_menu.addMenu('List of available APIs')
        for api in Block.ExecutionBlock.list_of_models:
            action = QtWidgets.QAction(api.__name__, self)
            self.apis_list_of_models.addAction(action)

        self.show()

    def updateMenuListOfAPI(self):
        self.apis_list_of_models.clear()
        for api in Block.ExecutionBlock.list_of_models:
            action = QtWidgets.QAction(api.__name__, self)
            self.apis_list_of_models.addAction(action)

    def close_application(self):
        sys.exit()

    def resizeEvent(self, event):
        self.widget.setGeometry(10, 20, self.width() - 20, self.height() - 30)

