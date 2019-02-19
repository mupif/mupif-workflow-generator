import mupif
import workflowgenerator
from .DataLink import *
from .Button import *
from . import Label
from . import Header
from . import Application
from . import helpers


class BlockVisual (QtWidgets.QGraphicsWidget):

    def __init__(self, block_real, parent, workflow, widget, scene):
        """
        :param workflowgenerator.Block.Block block_real:
        :param Block.BlockVisual parent:
        :param Block.BlockVisual workflow:
        :param widget:
        :param scene:
        """
        kwargs = {}
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

    def getChildItems(self):
        """
        :rtype: list
        """
        return self.childItems()

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

    def getDataSlotWithUID(self, uid, recursive_search=False):
        for slot in self.getAllDataSlots(recursive_search):
            if slot.getUID() == uid:
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
        Add the given Slot to this Block.
        A Slot must have a unique name, meaning there can be no duplicates within
        a Node (the displayNames are not constrained though).
        Assign ourselves as the slot's parent item (which also will put it onto
        the current scene, if not yet done) and adjust or size for it.
        The position of the slot is set relative to this Node and depends on it
        either being an Input or Output slot.
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

        for keyword in self.getRealBlock().getVisualStructureItems():
            if keyword == 'label':
                for elem in self.getLabels():
                    if elem not in printed_elems:
                        elem.y = current_height
                        current_height += elem.getHeight() + self.spacing
                        printed_elems.append(elem)
                        break
            elif keyword == 'slot':
                for elem in self.getDataSlots():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
                        break
            elif keyword == 'slots':
                for elem in self.getDataSlots():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
            elif keyword == 'block':
                for elem in self.getChildExecutionBlocks():
                    if elem not in printed_elems:
                        elem.setY(current_height)
                        current_height += elem.h + self.spacing
                        printed_elems.append(elem)
                        break
            elif keyword == 'blocks':
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
        for label in self.getLabels()[:]:
            label.destroy()
        for slot in self.getDataSlots()[:]:
            slot.destroy()
        for block in self.getBlocks()[:]:
            block.destroy()
        self.scene.removeItem(self)

        del self

    def getWorkflowBlock(self):
        return self.workflow

    def addMenuItems(self, menu):
        def _queryToWorkflowGenerator(uid, keyword, value):
            self.getRealBlock().getWorkflowBlock().modificationQueryForItemWithUID(uid, keyword, value)
            self.getApplication().reGenerateAll()

        def _getTextValue(inp_caption):
            """
            :param str inp_caption:
            :rtype: str or None
            """
            dialog_temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = dialog_temp.width()
            dh = dialog_temp.height()
            dialog_temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getText(dialog_temp, inp_caption, "")
            if ok_pressed:
                return new_value
            return None

        def _getIntValue(inp_caption):
            """
            :param str inp_caption:
            :rtype: int or None
            """
            dialog_temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = dialog_temp.width()
            dh = dialog_temp.height()
            dialog_temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getInt(dialog_temp, inp_caption, "")
            if ok_pressed:
                return new_value
            return None

        def _getFloatValue(inp_caption):
            """
            :param str inp_caption:
            :rtype: int or None
            """
            dialog_temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = dialog_temp.width()
            dh = dialog_temp.height()
            dialog_temp.setGeometry(200, 200, dw, dh)
            new_value, ok_pressed = QtWidgets.QInputDialog.getDouble(dialog_temp, inp_caption, "")
            if ok_pressed:
                return new_value
            return None

        def _getSelectValue(inp_caption, inp_options):

            selected_id = 0
            # if str() in items:
            #     selected_id = items.index(str(self.valueType))

            temp = QtWidgets.QInputDialog()
            px = self.workflow.widget.window.x()
            py = self.workflow.widget.window.x()
            dw = temp.width()
            dh = temp.height()
            temp.setGeometry(200, 200, dw, dh)
            item, ok = QtWidgets.QInputDialog.getItem(temp, inp_caption, "", inp_options, selected_id, False)
            if ok and item:
                return item
                # if item in items:
                #     selected_id = items.index(item)
                #     self.valueType = items_real[selected_id]
                #     self.updateLabel()
            return None

        def _menuItemClick(uid, keyword, value, inp_type="", inp_caption="", inp_options=[]):
            new_value = value
            if inp_type == "str":
                new_value = _getTextValue(inp_caption)
            elif inp_type == "int":
                new_value = _getIntValue(inp_caption)
            elif inp_type == "float":
                new_value = _getFloatValue(inp_caption)
            elif inp_type == "select":
                new_value = _getSelectValue(inp_caption, inp_options)

            if new_value is not None:
                _queryToWorkflowGenerator(uid, keyword, new_value)

        def _generateMenu(menu, wg_menu):
            """
            :param menu:
            :param workflowgenerator.VisualMenu.VisualMenu wg_menu:
            """
            for wg_submenu in wg_menu.getMenus():
                sub_menu = menu.addMenu(wg_submenu.getName())
                _generateMenu(sub_menu, wg_submenu)

            for wg_item in wg_menu.getItems():
                action = menu.addAction(wg_item.getText())
                action.triggered.connect(
                    lambda checked, uid=self.getUID(), keyword=wg_item.getKeyword(),
                           value=wg_item.getValue(), i_type=wg_item.getInputType(),
                           i_caption=wg_item.getInputCaption(), i_options=wg_item.getInputOptions():
                    _menuItemClick(uid, keyword, value, i_type, i_caption, i_options))

        _generateMenu(menu, self.getRealBlock().getMenu())

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

    def getScene(self):
        return self.widget.scene

