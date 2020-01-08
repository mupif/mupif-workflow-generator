import workflowgenerator
from . import Window
from .GraphWidget import *
from . import Block
import sys


class Application:

    def __init__(self, workflow=None):
        self.app = QtWidgets.QApplication([])
        self.workflow = workflow
        if self.workflow is None:
            self.workflow = workflowgenerator.BlockWorkflow.BlockWorkflow()
        self.window = Window.Window(self)

    def run(self):
        sys.exit(self.app.exec())

    def exit(self):
        sys.exit()

    def addWorkflow(self):
        return self.window.widget.addWorkflowBlock()

    def getWorkflowBlock(self):
        """:rtype: Block.BlockVisual"""
        return self.window.widget.getWorkflowBlock()

    def setRealWorkflow(self, workflow):
        """:param workflowgenerator.BlockWorkflow.BlockWorkflow workflow:"""
        self.workflow = workflow

    def getRealWorkflow(self):
        """:rtype: workflowgenerator.BlockWorkflow.BlockWorkflow"""
        return self.workflow

    def getWindow(self):
        """:rtype: Window.Window"""
        return self.window

    def clearAll(self):
        self.getWorkflowBlock().destroy()

    def generateAll(self):
        workflow = self.generateVisualBlockForRealBlock(self.getRealWorkflow(), None, None)
        self.window.widget.workflow = workflow
        self.window.widget.addNode(self.window.widget.workflow)
        self.generateChildItems(self.window.widget.workflow)
        for dl in self.getRealWorkflow().getDataLinks():
            slot_uids = dl.getSlotsUID()
            slot1 = self.getWorkflowBlock().getDataSlotWithUID(slot_uids[0], True)
            slot2 = self.getWorkflowBlock().getDataSlotWithUID(slot_uids[1], True)
            if slot1 is not None and slot2 is not None:
                slot1.connectTo(slot2)
            else:
                print("One or both slots to be connected were not found.")

        self.getWindow().setFixedWidth(self.getWorkflowBlock().w + 32)

        self.getRealWorkflow().printStructure()

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
        """:param Block.BlockVisual block:"""
        for real_block in block.getRealBlock().getBlocks():
            self.generateVisualBlockForRealBlock(real_block, block, block.workflow)
        for sub_block in block.getBlocks():
            self.generateChildItems(sub_block)
