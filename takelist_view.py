from PySide2.QtWidgets import QWidget, QTableView, QTreeView, QSizePolicy, QHeaderView, QComboBox, QItemDelegate, QStyleOptionViewItem
from PySide2.QtCore import QModelIndex, QAbstractItemModel, Qt, Slot
from .takelist_model import TakeListModel
from switchboard.switchboard_logging import ConsoleStream, LOGGER

class TakeListView(QTreeView):
    def __init__(self, parent: QWidget, model: TakeListModel):
        QTreeView.__init__(self, parent)
        
        self.expanded_items = set()

        self.model = model
        self.model.dataChanged.connect(self.refresh)
        self.model.layoutChanged.connect(self.refresh)
        self.setModel(self.model)

        status_col_idx = [self.model.headerData(col, Qt.Horizontal) for col in range(self.model.columnCount())].index("Status")
        self.setItemDelegateForColumn(status_col_idx, TakeListStatusItemDelegate(self, self.model))

        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size.setHorizontalStretch(1)
        self.setSizePolicy(size)
        self.setSortingEnabled(True)
        self.resizeColumnToContents(0)


        # configure resize modes on headers
        #self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.horizontalHeader().setStretchLastSection(True)
        #self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.verticalHeader().setVisible(False)

    @Slot()
    def refresh(self):
        LOGGER.info("Refreshing take list view")
        # Restore the expanded state after layout change
        #self.restoreExpandedState()
        #self.resizeColumnsToContents()
        #self.expandRecursively(QModelIndex())

    def layoutAboutToBeChanged(self):
        # Save the expanded state before layout change
        self.saveExpandedState()
        super(TakeListView, self).layoutAboutToBeChanged()

    def layoutChanged(self):
        super(TakeListView, self).layoutChanged()
        self.restoreExpandedState()

    #def dataChanged(self, topLeft, bottomRight, roles=None):
        #LOGGER.info("Data changed")
        #super(TakeListView, self).dataChanged(topLeft, bottomRight, roles)
        #self.saveExpandedState()

    def rowsInserted(self, parent, start, end):
        super(TakeListView, self).rowsInserted(parent, start, end)
        self.saveExpandedState()

    def saveExpandedState(self):
        # Save the expanded state of items
        self.expanded_items.clear()
        root = self.model.index(0, 0)
        self.saveExpandedStateRecursive(root)

    def saveExpandedStateRecursive(self, index):
        if not index.isValid():
            return

        if self.isExpanded(index):
            LOGGER.info(f"Saving expanded state for {index}")
            self.expanded_items.add(index)

        for row in range(self.model.rowCount(index)):
            child_index = self.model.index(row, 0, index)
            self.saveExpandedStateRecursive(child_index)

    def restoreExpandedState(self):
        # Restore the expanded state of items
        for index in self.expanded_items:
            LOGGER.info(f"Restoring expanded state for {index}")
            self.setExpanded(index, True)
            

class TakeListStatusItemDelegate(QItemDelegate):
    def __init__(self, parent: QWidget, model: TakeListModel):
        QItemDelegate.__init__(self, parent)
        self.model = model

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        dropdown = QComboBox(parent)
        dropdown.addItem("⭐")
        # dropdown.model().item(0).setBackground(TakeListModel.COLOR_BEST)
        dropdown.addItem("✔️")
        # dropdown.model().item(1).setBackground(TakeListModel.COLOR_GOOD)
        dropdown.addItem("❌")
        # dropdown.model().item(2).setBackground(TakeListModel.COLOR_BAD)
        return dropdown
        # return super().createEditor(parent, option, index)

    def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
        value = self.model.data(index, Qt.DisplayRole)
        print(f"Setting editor value to {value}")
        editor.setCurrentText(value)
        #return super().setEditorData(editor, index)

    def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
        value = None
        try:
            value = editor.currentData()
            print(f"Setting model value to {value}")
        except Exception as e:
            print(e)
        if value:
            self.model.setData(index, value)
        else:
            return super().setModelData(editor, model, index)