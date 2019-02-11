import mupif
import workflowgenerator
from .DataLink import *
from .Button import *
from . import Label
from . import Header
from . import Application
from . import helpers


class BlockVisual (QtWidgets.QGraphicsWidget):

    def __init__(self, block_real, parent, workflow, widget, scene, **kwargs):
        QtWidgets.QGraphicsWidget.__init__(self, kwargs.get("parent", None))

        self.widget = widget
        self.scene = scene

        self.block_real = block_real

        self.parent = parent
        self.workflow = workflow
        if self.parent is None:
            self.workflow = self
            self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)

        self.setParentItem(parent)

        self.x = 0
        self.y = 0
        self.w = 10
        self.h = 10

        self.spacing = 10
        self.roundness = 0
        self.fillColor = QtGui.QColor(220, 220, 220)

        self.label = Label.Label(self)
        self.labels = []

        self.header = Header.Header(self, self.block_real.getHeaderText())
        self.header.setParentItem(self)

        self.clonable = False

        # General configuration.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setCursor(QtCore.Qt.SizeAllCursor)
        self.setAcceptHoverEvents(True)
        self.setAcceptTouchEvents(True)
        self.setAcceptDrops(True)

        self.button_menu = Button(self, "...")
        self.button_menu.setParentItem(self)

        self.generateItems()

        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()

    def __repr__(self):
        return "%s (parent: %s)(representing: %s)" % (self.__class__.__name__, self.parent.__class__.__name__, self.getRealBlock())

    def getRealBlock(self):
        """
        :rtype: workflowgenerator.Block.Block
        """
        return self.block_real

    def getLabels(self):
        """
        :rtype: list of Label.Label
        """
        return self.labels

    def generateItems(self):
        for label_text in self.getRealBlock().getLabels():
            self.labels.append(Label.Label(self, label_text))

        for slot in self.getRealBlock().getSlots():
            new_slot = None
            if isinstance(slot, workflowgenerator.DataSlot.ExternalInputDataSlot):
                new_slot = ExternalInputDataSlot(slot, self, slot.name, slot.getType(), slot.getOptional(), self, slot.getObjType(), slot.getObjID())
            elif isinstance(slot, workflowgenerator.DataSlot.ExternalOutputDataSlot):
                new_slot = ExternalOutputDataSlot(slot, self, slot.name, slot.getType(), slot.getOptional(), self, slot.getObjType(), slot.getObjID())
            elif isinstance(slot, workflowgenerator.DataSlot.InputDataSlot):
                new_slot = InputDataSlot(slot, self, slot.name, slot.getType(), slot.getOptional(), self, slot.getObjType(), slot.getObjID())
            elif isinstance(slot, workflowgenerator.DataSlot.OutputDataSlot):
                new_slot = OutputDataSlot(slot, self, slot.name, slot.getType(), slot.getOptional(), self, slot.getObjType(), slot.getObjID())

            if new_slot is not None:
                self.addDataSlot(new_slot)

    def getApplication(self):
        """
        :rtype: Application.Application
        """
        return self.workflow.widget.window.application

    def getUID(self):
        return self.getRealBlock().getUID()

    def clone(self):
        """"""

    def setPropertiesFromAnotherBlockOfSameType(self, block):
        """"""

    def updateLabel(self):
        """
        Updates the block's label according to block's properties.
        """

    def getChildItems(self):
        """
        :rtype: list
        """
        return self.childItems()

    def updateHeaderText(self, val=None):
        if val:
            self.header.text = val
        else:
            self.header.text = self.name

    def getDataSlots(self, cls=None):
        """
        Return a list of data slots.
        If the optional `cls` is specified, return only Slots of that class.
        This is useful e.g. to get all Input or Output Slots.
        """
        slots = []
        for child in self.getChildItems():
            if isinstance(child, DataSlot):
                slots.append(child)
        if cls:
            slots = list(filter(lambda k: k.__class__ is cls, slots))
        return slots

    def getAllDataSlots(self, recursive=False):
        array = self.getDataSlots()
        if recursive:
            for block in self.getChildExecutionBlocks():
                array.extend(block.getAllDataSlots(True))
        return array

    def getDataSlotWithUUID(self, uid, recursive_search=False):
        for slot in self.getAllDataSlots(recursive_search):
            if slot.uid == uid:
                return slot
        return None

    def getDataSlotWithName(self, name):
        """Return matching data slot by its name, None otherwise."""
        for slot in self.getDataSlots():
            if slot.name == name:
                return slot
        return None

    def getDataSlot(self, name=None, uuid=None, parent_uuid=None, recursive_search=False):
        if name or uuid or parent_uuid:
            for slot in self.getAllDataSlots(recursive_search):
                if (not name or (slot.name == name and slot.name)) and (not uuid or (slot.uid == uuid and slot.uuid)) and (not parent_uuid or (slot.getParentUUID() == parent_uuid and slot.getParentUUID())):
                    return slot
        return None

    def addDataSlot(self, slot):
        """
        Add the given Slot to this Node.
        A Slot must have a unique name, meaning there can be no duplicates within
        a Node (the displayNames are not constrained though).
        Assign ourselves as the slot's parent item (which also will put it onto
        the current scene, if not yet done) and adjust or size for it.
        The position of the slot is set relative to this Node and depends on it
        either being an Input- or Output slot.
        """
        # TODO
        slot_names = [k.name for k in self.getDataSlots()]
        # print("adding slot, existing Slots:", self.getDataSlots(), slot_names)
        if slot.name in slot_names and False:  # TODO
            raise DuplicateKnobNameError(
                "Slot names must be unique, but {0} already exists."
                .format(slot.name))
        slot.setParentItem(self)
        slot.spacing = self.spacing
        self.callUpdatePositionOfWholeWorkflow()

    def removeDataSlot(self, slot):
        """Remove the Knob reference to this node and resize."""
        # slot.setParentItem(None)
        slot.destroy()
        self.callUpdatePositionOfWholeWorkflow()

    def addExecutionBlock(self, block):
        block.setParentItem(self)
        self.callUpdatePositionOfWholeWorkflow()

    def getChildExecutionBlocks(self, cls=None, recursive=False):
        blocks = []
        # for child in self.canvas.childItems():
        for child in self.childItems():
            # print(child)
            if isinstance(child, BlockVisual):
                blocks.append(child)
                if recursive:
                    blocks += child.getChildExecutionBlocks(cls, recursive)
        if cls:
            blocks = list(filter(lambda k: k.__class__ is cls, blocks))
        return blocks

    def getBlocks(self, cls=None):
        """Return a list of child blocks.
            If the optional `cls` is specified, return only blocks of that class.
            This is useful e.g. to get all Input or Output Slots.
        """
        return_array = []
        for child in self.getChildItems():
            if isinstance(child, BlockVisual):
                return_array.append(child)
        if cls:
            return_array = list(filter(lambda k: k.__class__ is cls, return_array))
        return return_array

    def boundingRect(self):
        """Return the bounding box of the Node, limited in height to its Header.
        This is so that the drag & drop sensitive area for the Node is only
        active when hovering its Header, as otherwise there would be conflicts
        with the hover events for the Node's Knobs.
        """
        rect = QtCore.QRectF(self.x,
                             self.y,
                             self.w,
                             self.h)
        return rect

    def minimumWidth(self):
        return self.w

    def minimumHeight(self):
        return self.h

    def sizeHint(self, which, constraint):
        return QtCore.QSizeF(self.w, self.h)

    def updateChildrenPosition(self):
        # TODO

        self.header.setX(0)
        self.header.setY(0)

        #
        # calculate size according to all items
        #

        height_of_all_content = self.header.h + self.spacing

        slot_widths = [k.getNeededWidth() for k in self.getDataSlots()]
        slot_widths.append(0)
        max_slot_width = max(slot_widths)

        header_width = (2*self.spacing + helpers.getTextSize(self.header.text).width())

        header_width += (2*self.spacing + helpers.getTextSize(self.button_menu.text).width())

        width_child_max = max(header_width, max_slot_width)

        for label in self.getLabels():
            width_child_max = max(width_child_max, label.getNeededWidth())
            height_of_all_content += label.h + self.spacing

        for elem in self.getDataSlots():
            height_of_all_content += elem.h + self.spacing

        for elem in self.getChildExecutionBlocks():
            width_child_max = max(width_child_max, elem.w)
            height_of_all_content += elem.h + self.spacing

        #
        # set the block's size
        #

        self.w = width_child_max + self.spacing * 2
        self.h = height_of_all_content

        #
        # set horizontal position of all elements
        #

        # dataslots
        for elem in self.getDataSlots():
            if isinstance(elem, InputDataSlot):
                elem.setX(self.spacing)
            else:
                elem.setX(self.w - elem.w - self.spacing)
            elem.setTotalWidth(self.w - self.spacing * 2)

        # labels
        for label in self.getLabels():
            label.x = self.spacing

        # blocks
        for elem in self.getChildExecutionBlocks():
            elem.setX(self.spacing)

        #
        # set vertical position of all elements according to the defined order
        #

        printed_elems = []
        current_height = self.header.h + self.spacing

        # set vertical position of all given elements

        for key, value in self.getRealBlock().getVisualStructureItems().items():
            if key == 'label':
                for elem in self.getLabels():
                    if elem not in printed_elems:
                        elem.y = current_height
                        current_height += elem.getHeight() + self.spacing
                        printed_elems.append(elem)
                        break
            elif key == 'slot':
                for elem in self.getDataSlots():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
                        break
            elif key == 'slots':
                for elem in self.getDataSlots():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
            elif key == 'block':
                for elem in self.getChildExecutionBlocks():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
                        break
            elif key == 'blocks':
                for elem in self.getChildExecutionBlocks():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)

        # set vertical position of all residual elements

        # labels
        for elem in self.getLabels():
            if elem not in printed_elems:
                elem.y = current_height
                current_height += elem.getHeight() + self.spacing
                printed_elems.append(elem)

        # slots
        for elem in self.getDataSlots():
            if elem not in printed_elems:
                elem.setY(current_height)
                current_height += elem.h + self.spacing
                printed_elems.append(elem)

        # blocks
        for elem in self.getChildExecutionBlocks():
            if elem not in printed_elems:
                elem.setY(current_height)
                current_height += elem.h + self.spacing
                printed_elems.append(elem)

    def updateChildrenSizeAndPositionAndResizeSelf(self, color_id=0):
        if color_id:
            child_color_id = 0
        else:
            child_color_id = 1

        # call it for child blocks
        for elem in self.getChildExecutionBlocks():
            elem.updateChildrenSizeAndPositionAndResizeSelf(child_color_id)

        self.updateChildrenPosition()

    def callUpdatePositionOfWholeWorkflow(self):
        self.workflow.updateChildrenSizeAndPositionAndResizeSelf()
        self.workflow.widget.view.redrawDataLinks()

    def paint(self, painter, option, widget):
        """Draw the Node's container rectangle."""
        painter.setBrush(QtGui.QBrush(self.fillColor))
        painter.setPen(QtGui.QPen(QtGui.QColor(20, 20, 20)))
        painter.drawRoundedRect(self.x,
                                self.y,
                                self.w,
                                self.h,
                                self.roundness,
                                self.roundness)

    def getConnectedDataLinks(self):
        answer = []
        for dataslot in self.getDataSlots():
            for datalink in dataslot.dataLinks:
                answer.append(datalink)
        return answer

    def updateDataLinksPath(self):
        nodes = self.getChildExecutionBlocks(None, True)
        for node in nodes:
            for dataslot in node.getDataSlots():
                for datalink in dataslot.dataLinks:
                    datalink.updatePath()

    def mouseMoveEvent(self, event):
        """Update selected item's (and children's) positions as needed.
        We assume here that only Nodes can be selected.
        We cannot just update our own childItems, since we are using
        RubberBandDrag, and that would lead to otherwise e.g. Edges
        visually lose their connection until an attached Node is moved
        individually.
        """
        nodes = self.scene.selectedItems()
        for node in nodes:
            for knob in node.getDataSlots():
                for edge in knob.dataLinks:
                    edge.updatePath()
        super(BlockVisual, self).mouseMoveEvent(event)

    def destroy(self):
        """Remove this Block, its Header, menu Button, DataSlots, child Blocks and connected DataLinks."""
        # TODO fix it
        self.header.destroy()
        self.button_menu.destroy()
        for slot in self.getDataSlots():
            slot.destroy()
        for block in self.getChildExecutionBlocks():
            block.destroy()

        scene = self.scene
        scene.removeItem(self)
        self.getApplication().reGenerateAll()
        self.callUpdatePositionOfWholeWorkflow()

        del self

    def addMenuItems_AddStandardBlock(self, menu):
        sub_menu = menu.addMenu("Add standard block")

        # def _addStandardBlock(idx):
        #     new_block = ExecutionBlock.list_of_block_classes[idx](self, self.workflow)
        #     self.addExecutionBlock(new_block)
        #
        # cls_id = 0
        # for block_class in ExecutionBlock.list_of_block_classes:
        #     add_model_block_action = sub_menu.addAction(block_class.__name__)
        #     add_model_block_action.triggered.connect(lambda checked, idx=cls_id: _addStandardBlock(idx))
        #     cls_id += 1

    def addMenuItems_AddModelBlock(self, menu):
        sub_menu = menu.addMenu("Add model block")

        # def _addModelBlock(idx):
        #     new_block_class = ExecutionBlock.list_of_models[idx]()
        #     new_block = ModelBlock(self, self.workflow)
        #     new_block.constructFromModelMetaData(new_block_class)
        #     self.addExecutionBlock(new_block)
        #
        # cls_id = 0
        # for model in ExecutionBlock.list_of_models:
        #     add_model_block_action = sub_menu.addAction(model.__name__)
        #     add_model_block_action.triggered.connect(lambda checked, idx=cls_id: _addModelBlock(idx))
        #     cls_id += 1

    def moveChildBlock(self, block, direction):
        child_blocks = self.getChildExecutionBlocks()
        block_id = -5
        if block in child_blocks:
            block_id = child_blocks.index(block)

        if (direction == "up" and block_id > 0) or (direction == "down" and block_id < len(child_blocks)-1):
            scene = self.scene
            for block in child_blocks:
                scene.removeItem(block)
            idx = 0
            for block in child_blocks:
                if direction == "up" and idx == block_id-1:
                    self.addExecutionBlock(child_blocks[block_id])
                if not idx == block_id:
                    self.addExecutionBlock(block)
                if direction == "down" and idx == block_id + 1:
                    self.addExecutionBlock(child_blocks[block_id])
                idx += 1

    def addMoveMenuActions(self, menu):
        def _move_up():
            self.parent.moveChildBlock(self, 'up')

        def _move_down():
            self.parent.moveChildBlock(self, 'down')

        move_menu = menu.addMenu("Move")
        move_up = move_menu.addAction("Up")
        move_up.triggered.connect(_move_up)
        move_down = move_menu.addAction("Down")
        move_down.triggered.connect(_move_down)

    def addDeleteMenuActions(self, menu):
        def _delete():
            self.destroy()

        delete_menu = menu.addAction("Delete")
        delete_menu.triggered.connect(_delete)

    def addCommonMenuActionsForParentBlocks(self, menu):
        pass

    def addCloneAction(self, menu):
        if self.clonable:
            def _clone():
                self.clone()

            clone_menu = menu.addAction("Clone")
            clone_menu.triggered.connect(_clone)

    def addCommonMenuActions(self, menu):
        if self.workflow is not self:
            self.addMoveMenuActions(menu)
            self.addDeleteMenuActions(menu)
        self.addCommonMenuActionsForParentBlocks(menu)
        self.addCloneAction(menu)

    def addMenuItems(self, menu):
        self.addCommonMenuActions(menu)

    def contextMenuEvent(self, event):
        self.showMenu()

    def showMenu(self):
        widget = self.workflow.widget
        menu = QtWidgets.QMenu(widget)
        self.addMenuItems(menu)
        menu.exec(QtGui.QCursor.pos())

    def getParentUUID(self):
        if self.parentItem():
            return self.parentItem().uuid
        else:
            return None

    def getDictForJSON(self):
        answer = {'classname': self.__class__.__name__, 'uuid': self.uuid, 'parent_uuid': self.getParentUUID()}
        return answer

    def convertToJSON(self):
        return_json_array = []
        return_json_array.append(self.getDictForJSON())

        for elem in self.getDataSlots():
            return_json_array.append(elem.getDictForJSON())

        for elem in self.getChildExecutionBlocks():
            return_json_array.extend(elem.convertToJSON())

        return return_json_array

    @staticmethod
    def getListOfModelClassnames():
        # array = [m.__name__ for m in ExecutionBlock.list_of_models]
        # return array
        return []

    @staticmethod
    def getListOfModelDependencies():
        # return ExecutionBlock.list_of_model_dependencies
        return []

    @staticmethod
    def getListOfStandardBlockClassnames():
        # array = [m.__name__ for m in ExecutionBlock.list_of_block_classes]
        # return array
        return []

    def getScene(self):
        return self.widget.scene

