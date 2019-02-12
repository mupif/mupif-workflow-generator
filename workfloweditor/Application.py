"""Application class."""
import workflowgenerator
from .Window import *
from .GraphWidget import *
from . import Block


class Application:

    def __init__(self, workflow=None):
        self.app = QtWidgets.QApplication([])
        self.workflow = workflow
        self.window = Window(self)

    def run(self):
        sys.exit(self.app.exec())

    def exit(self):
        sys.exit()

    def addWorkflow(self):
        return self.window.widget.addWorkflowBlock()

    def getWorkflowBlock(self):
        """
        :rtype: Block.BlockVisual
        """
        return self.window.widget.getWorkflowBlock()

    def setRealWorkflow(self, workflow):
        """
        :param workflowgenerator.BlockWorkflow.BlockWorkflow workflow:
        """
        self.workflow = workflow

    def getRealWorkflow(self):
        """
        :rtype: workflowgenerator.BlockWorkflow.BlockWorkflow
        """
        return self.workflow

    def clearAll(self):
        self.getWorkflowBlock().destroy()

    def generateAll(self):
        workflow = self.generateVisualBlockForRealBlock(self.getRealWorkflow(), None, None)
        self.window.widget.workflow = workflow
        self.window.widget.addNode(self.window.widget.workflow)
        self.generateChildItems(workflow)

    def reGenerateAll(self):
        self.clearAll()
        self.generateAll()

    def generateVisualBlockForRealBlock(self, block_real, parent, workflow):
        """
        :param workflowgenerator.Block.Block block_real:
        :param Block.BlockVisual or None parent:
        :param Block.BlockVisual or None workflow:
        :rtype: Block.BlockVisual
        """
        block_new = Block.BlockVisual(block_real, parent, workflow, self.window.widget, self.window.widget.scene)

        return block_new

    def generateChildItems(self, block):
        """
        :param Block.BlockVisual block:
        """

        for real_block in block.getRealBlock().getBlocks():
            self.generateVisualBlockForRealBlock(real_block, block, block.workflow)
