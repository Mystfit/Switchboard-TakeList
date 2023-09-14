from PySide2.QtCore import QAbstractTableModel, QAbstractItemModel, QModelIndex, Qt, Slot
from PySide2.QtGui import QColor, QStandardItem
from switchboard.config import CONFIG
import os, pathlib, csv

TEST_DATA = [
    {
        'Sequence': 'Shot1',
        'Slate': 'Run in place',
        'Take': 1,
        'Timecode': '00:00:00:00',
        'Duration': 0.0,
        'Status': 'G',
        'Notes': 'Good take',
    },
    {
        'Sequence': 'Shot1',
        'Slate': 'Run in place',
        'Take': 2,
        'Timecode': '00:00:00:00',
        'Duration': 0.0,
        'Status': 'NG',
        'Notes': 'Bad take',
    },
    {
        'Sequence': 'Shot1',
        'Slate': 'Run in place',
        'Take': 3,
        'Timecode': '00:00:00:00',
        'Duration': 0.0,
        'Status': 'S',
        'Notes': 'Best take',
    }
]

TAKELIST_FILE_NAME = "takelist.csv"


class SequenceItem(QStandardItem):
    pass


class SlateItem(QStandardItem):
    pass


class TakeItem(QStandardItem):
    def __init__(self, take, timecode, duration, status, notes):
        super().__init__(take)
        self.timecode = timecode
        self.duration = duration
        self.status = status
        self.notes = notes


class TakeListModel(QAbstractItemModel):
    COLOR_BEST = QColor(0x0d,0x81,0x0d)
    COLOR_GOOD = QColor(0x27,0x66,0xb8)
    COLOR_NORMAL = QColor(0x3d, 0x3d, 0x3d)
    COLOR_BAD = QColor(0xb8,0x27,0x27)

    def __init__(self, parent):
        QAbstractItemModel.__init__(self, parent)

        HEADER_DATA = {
            'Sequence': 'Sequence for this take',
            'Slate': 'Slate for this take',
            'Take': 'Take number',
            'Timecode': 'Timecode at the start of this take',
            'Duration': 'Duration of this take',
            'Status': 'Status flags for this take',
            'Notes': 'Notes for this take',
        }
        self.rootItem = QStandardItem("Root")
        self._data = []#TEST_DATA
        self.colnames = list(HEADER_DATA.keys())
        self.tooltips = list(HEADER_DATA.values())

        self.dataChanged.connect(self.save_data)

    # ~ QAbstractTableModel interface begin

    def rowCount(self, parent=QModelIndex()):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        return parentItem.rowCount()

        return len(self._data)
        # return len(self.devicedatas)

    def columnCount(self, parent=QModelIndex()):
        return len(self.colnames)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.colnames[section]
            else:
                return "{}".format(section)

        if role == Qt.ToolTipRole:
            return self.tooltips[section]

        return None

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def flags(self, index: QModelIndex):
        column = index.column()
        row = index.row()
        colname = self.colnames[column]
        if colname == "Notes" or colname == "Status":
            return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsEnabled

    def add_take(self, sequence: str, slate:str, take: int, description: str, timecode: str):
        self.beginInsertRows(QModelIndex(), len(self._data), len(self._data))
        # self._data.append({
        #     'Sequence': sequence,
        #     'Slate': slate,   
        #     'Take': take,
        #     'Timecode': timecode,
        #     'Duration': 0.0,
        #     'Status': 'G',
        #     'Notes': description
        # })
        sequence_item = None
        if sequence not in [self.rootItem.child(row).data() for row in range(self.rootItem.rowCount())]:
            sequence_item = SequenceItem(sequence)
            print(sequence_item)
            self.rootItem.appendRow(sequence_item)
        else:
            sequence_item = self._data[sequence]
        print([self.rootItem.child(row).data() for row in range(self.rootItem.rowCount())])

        if slate not in [sequence_item.child(row).data() for row in range(sequence_item.rowCount())]:
            slate_item = SlateItem(slate)
            sequence_item.appendRow(slate_item)
        else:
            slate_item = sequence_item[slate]

        if take not in [slate_item.child(row).data() for row in range(slate_item.rowCount())]:
            take_item = TakeItem(take, timecode, 0, "G", description)
            slate_item.appendRow(take_item)
            self.dataChanged.emit(QModelIndex(), QModelIndex())
        else:
            print("Take already exists in slate")
            take_item = slate_item[take]

        self.endInsertRows()

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            item = index.internalPointer()
            print(f"Setting item data for {item}")

            if isinstance(item, SequenceItem):
                item.setData(value)
            elif isinstance(item, SlateItem):
                item.setData(value)
            elif isinstance(item, TakeItem):

                if column == 0:  # Edit the "Take" value
                    pass
                elif column == 1:  # Edit the "Status" value
                    item.child(0, column).setData(value)
                elif column == 2:  # Edit the "Notes" value
                    item.child(0, column).setData(value)

            colname = self.colnames[column]
            if colname == "Notes" or colname == "Status":
                self._data[row][colname] = value
                self.dataChanged.emit(index, index)
                return True
        return False

    def get_root_dir(self) -> pathlib.Path:
        return pathlib.Path(CONFIG.SWITCHBOARD_DIR)

    def project_takelist_path(self) -> pathlib.Path:
        project_dir = self.get_root_dir() / 'projects' / CONFIG.PROJECT_NAME.get_value()
        os.makedirs(project_dir, exist_ok=True)
        return project_dir /TAKELIST_FILE_NAME

    @Slot()
    def save_data(self):
        with open(self.project_takelist_path(), 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.colnames)
            writer.writeheader()
            for row in self._data:
                writer.writerow(row)

    def data(self, index: QModelIndex, role:Qt.ItemDataRole=Qt.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.DisplayRole:
            return item.text()
        return None
        # elif role == Qt.ForegroundRole:
        #     return self.foreground_color_for_column(colname=colname, value=value,
        #                                  data=data)
        '''
        elif role == Qt.BackgroundRole:
            return self.background_color_for_column(colname=colname, value=value,
                                         data=data)

        elif role == Qt.TextAlignmentRole:
            # if colname in ('CpuUtilization', 'GpuUtilization'):
            #     return Qt.AlignLeft
            return Qt.AlignRight

        return None
        '''

    # ~ QAbstractTableModel interface end

    def foreground_color_for_column(self, colname, value, data):
        ''' Returns the foreground color for the given cell '''
        if colname == 'Status':
            if value == 'NG':
                return TakeListModel.COLOR_BAD
            elif value == 'S':
                return TakeListModel.COLOR_BEST
            elif value == 'G':
                return TakeListModel.COLOR_GOOD
            
        return TakeListModel.COLOR_NORMAL

    def background_color_for_column(self, colname, value, data):
        ''' Returns the background color for the given cell '''
        if colname == 'Status':
            if value == 'NG':
                return TakeListModel.COLOR_BAD
            elif value == 'S':
                return TakeListModel.COLOR_BEST
            elif value == 'G':
                return TakeListModel.COLOR_GOOD
            
        return TakeListModel.COLOR_NORMAL
