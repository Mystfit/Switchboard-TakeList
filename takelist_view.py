from PySide2.QtWidgets import QWidget, QTableView, QTreeView, QSizePolicy, QHeaderView, QComboBox, QItemDelegate, QStyleOptionViewItem
from PySide2.QtCore import QModelIndex, QAbstractItemModel, Qt, Slot
from .takelist_model import TakeListModel

class TakeListView(QTreeView):
    def __init__(self, parent: QWidget, model: TakeListModel):
        QTreeView.__init__(self, parent)

        self.model = model
        self.model.dataChanged.connect(self.refresh)
        self.setModel(self.model)

        status_col_idx = [self.model.headerData(col, Qt.Horizontal) for col in range(self.model.columnCount())].index("Status")
        self.setItemDelegateForColumn(status_col_idx, TakeListStatusItemDelegate(self, self.model))

        size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        size.setHorizontalStretch(1)
        self.setSizePolicy(size)
        self.setSortingEnabled(True)

        # configure resize modes on headers
        #self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.horizontalHeader().setStretchLastSection(True)
        #self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        #self.verticalHeader().setVisible(False)

    @Slot()
    def refresh(self):
        self.resizeColumnsToContents()
            

class TakeListStatusItemDelegate(QItemDelegate):
    def __init__(self, parent: QWidget, model: TakeListModel):
        QItemDelegate.__init__(self, parent)
        self.model = model

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        dropdown = QComboBox(parent)
        dropdown.addItem("S")
        dropdown.model().item(0).setBackground(TakeListModel.COLOR_BEST)
        dropdown.addItem("G")
        dropdown.model().item(1).setBackground(TakeListModel.COLOR_GOOD)
        dropdown.addItem("NG")
        dropdown.model().item(2).setBackground(TakeListModel.COLOR_BAD)
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