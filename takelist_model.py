from PySide2.QtCore import QAbstractTableModel, QAbstractItemModel, QModelIndex, Qt, Slot
from PySide2.QtGui import QColor, QStandardItem
from switchboard.config import CONFIG
from switchboard.switchboard_logging import ConsoleStream, LOGGER
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

# def flatten_dict(d, parent_key='', sep='_'):
#     """
#     Flatten a nested dictionary and concatenate keys with separators.
#     """
#     items = []
#     LOGGER.info(d)
#     for k, v in d.items():
#         new_key = f"{parent_key}{sep}{k}" if parent_key else k
#         if isinstance(v, dict):
#             items.extend(flatten_dict(v, new_key, sep=sep).items())
#         else:
#             items.append((new_key, v))
#     return dict(items)

# def flatten_dict_list(dict_list):
#     """
#     Flatten a list of dictionaries and create headers for each nested dictionary.
#     """
#     flat_list = [flatten_dict(val) for key,val in dict_list.items()]
#     headers = set(key for item in flat_list for key in item.keys())
#     return headers, [[item.get(header, '') for header in headers] for item in flat_list]

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                item_key = f"{new_key}{sep}{i}"
                items.extend(flatten_dict({item_key: item}, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class TreeItem(object):
    def __init__(self, data, column_names=[], parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.column_names = column_names

    def appendRow(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def rowCount(self):
        return len(self.childItems)

    def columnCount(self):
        if self.parent():
            return self.parent().columnCount()
        return len(self.column_names)

    def data(self, column):
        if column == "Name":
            return self.displayName()
        
        if column == "Type":
            return self.type()

        try:
            return self.itemData[column]
        except KeyError:
            if self.parent():
                return self.parent().data(column)
        return None

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)
        LOGGER.info(f"{self} hasa no parent. Returning 0 for row")
        return 0
    
    def displayName(self):
        return ""
    
    def type(self):
        return "Root"
    
    def toDict(self):
        return {
            "Children": [child.toDict() for child in self.childItems]    
        }
    
    def flatten(self):
        flattened_children = []
        for child in self.childItems:
            flattened_children += child.flatten()
        return flattened_children



class TakeItem(TreeItem):
    def __init__(self, slate_parent, take, timecode, duration, status, notes):
        take_data = {
            'Take': take,
            'Timecode': timecode,
            'Duration': duration,
            'Status': status,
            'Notes': notes
        }
        super().__init__(data=take_data, parent=slate_parent)
    
    def displayName(self):
        return self.data("Take")
    
    def type(self):
        return "🎞️ Take"
    
    def setNotes(self, notes):
        self.itemData["Notes"] = notes

    def setStatus(self, status):
        self.itemData["Status"] = status

    def toDict(self):
        return self.itemData
    
    def flatten(self):
        return self.itemData


class SlateItem(TreeItem):
    def __init__(self, sequence_parent, slate):
        slate_data = {
            'Slate': slate
        }
        super().__init__(data=slate_data, parent=sequence_parent)
        # self.slate = slate
        # self.takes = []

    def displayName(self):
        return self.data("Slate")
    
    def type(self):
        return "🎬 Slate"

    def add_take(self, take: TakeItem):
        self.appendRow(take)

    def get_take(self, take: int):
        for row in range(self.rowCount()):
            if take == self.child(row).data("Take"):
                return self.child(row)
        return None
    
    def toDict(self):
        return  {
            "Slate": self.displayName(),
            "Takes": [take.toDict() for take in self.childItems]
        }
    
    def flatten(self):
        flattened_children = []
        for child in self.childItems:
            flattened = child.flatten()
            flattened["Slate"] = self.displayName()
            flattened_children.append(flattened)
        return flattened_children


class SequenceItem(TreeItem):
    def __init__(self, sequence, parent=None):
        sequence_data = {
            'Sequence': sequence
        }
        super().__init__(data=sequence_data, parent=parent)

    def add_slate(self, slate: SlateItem):
        self.appendRow(slate)

    def displayName(self):
        return self.data("Sequence")
        
    def type(self):
        return "🎥 Sequence"
    
    def get_slate(self, slate: str):
        for row in range(self.rowCount()):
            if slate == self.child(row).data("Slate"):
                return self.child(row)
        return None
    
    def toDict(self):
        return  {
            "Sequence": self.displayName(),
            "Slates": [slate.toDict() for slate in self.childItems]
        }
    
    def flatten(self):
        flattened_children = []
        for child in self.childItems:
            flattened = child.flatten()
            LOGGER.info(f"Flattened slate row: {flattened}")
  
            for flattened_child in flattened:
                flattened_child["Sequence"] = self.displayName()
                LOGGER.info(f"Current flattened child is {flattened_child}")
                flattened_children.append(flattened_child)
        LOGGER.info(f"Flattened sequence row: {flattened_children}")
        return flattened_children



HEADER_DATA = {
    # 'Sequence': 'Sequence for this take',
    # 'Slate': 'Slate for this take',
    # 'Take': 'Take number',
    'Name': 'Name of this item',
    'Type': 'Type of this item (sequence, slate, take)',
    'Timecode': 'Timecode at the start of this take',
    'Duration': 'Duration of this take',
    'Status': 'Status flags for this take',
    'Notes': 'Notes for this take',
}

CSV_HEADER_DATA = {
    'Sequence': 'Sequence for this take',
    'Slate': 'Slate for this take',
    'Take': 'Take number',
    'Timecode': 'Timecode at the start of this take',
    'Duration': 'Duration of this take',
    'Status': 'Status flags for this take',
    'Notes': 'Notes for this take',
}

class TakeListModel(QAbstractItemModel):
    COLOR_BEST = QColor(0x0d,0x81,0x0d)
    COLOR_GOOD = QColor(0x27,0x66,0xb8)
    COLOR_NORMAL = QColor(0x3d, 0x3d, 0x3d)
    COLOR_BAD = QColor(0xb8,0x27,0x27)

    def __init__(self, parent):
        QAbstractItemModel.__init__(self, parent)
       
        #self._data = []#TEST_DATA
        self.colnames = list(HEADER_DATA.keys())
        self.tooltips = list(HEADER_DATA.values())
        self.rootItem = TreeItem({}, column_names=HEADER_DATA.keys())

        self.dataChanged.connect(self.save_data)

    # ~ QAbstractTableModel interface begin

    def get_sequence(self, sequence: str):
        for row in range(self.rootItem.rowCount()):
            if sequence == self.rootItem.child(row).data("Sequence"):
                return self.rootItem.child(row)
        return None

    def rowCount(self, parent=QModelIndex()):
        # if parent.column() > 0:
        #     return 0
        
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        # LOGGER.info(f"Requesting row count for parent {parentItem}. Row count is {parentItem.rowCount}")
        return parentItem.rowCount()

        return len(self._data)
        # return len(self.devicedatas)

    def hasChildren(self, parent=QModelIndex()):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()
        
        # LOGGER.info(f"Requesting hasChildren for parent {parentItem}. Row count is {parentItem.rowCount()}")
        return parentItem.rowCount() > 0

    def columnCount(self, parent=QModelIndex()):
        if parent and parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return len(self.colnames)

    def headerData(self, column, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                # if column < 0:
                #     return None
                return self.colnames[column]
            else:
                return "{}".format(column)

        if role == Qt.ToolTipRole:
            return self.tooltips[column]

        return None
    
    def findChildRowIndex(self, sequence: str, slate: str, take: int):
        sequence_item = self.get_sequence(sequence)
        if not sequence_item:
            return None
        slate_item = sequence_item.get_slate(slate)
        if not slate_item:
            return None
        for row in range(slate_item.rowCount()):
            if take == slate_item.child(row).data("Take"):
                self.createIndex(row, 0, row)
        return None

    def index(self, row, column, parent):            
        #LOGGER.info(f"Requesting tree index for row  {row}, col {self.colnames[column]}")                
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            #LOGGER.info(f"Child item is {childItem}")           
            return self.createIndex(childItem.row(), column, childItem)
        else:
            return QModelIndex()

    def parent(self, index):
        # LOGGER.info(f"Requesting parent index for index{index}")                

        if not index.isValid():
            return QModelIndex()

        childItem = index.internalPointer()
        # LOGGER.info(f"Childitem for parent index lookup is {childItem}")         
        if not childItem:
            return QModelIndex()
        
        parentItem = childItem.parent()
        # LOGGER.info(f"Parent item for parent index lookup is {parentItem}")

        if parentItem == self.rootItem or not parentItem:
            # LOGGER.info(f"Parent item is root")
            return QModelIndex()

        parent_index = self.createIndex(parentItem.row(), 0, parentItem)
        #LOGGER.info(f"Parent index is {parent_index}. Internal pointer is {parent_index.internalPointer()}. Row is {parent_index.row()}")
       
        return parent_index

    def flags(self, index: QModelIndex):
        column = index.column()
        row = index.row()
        colname = self.colnames[column]
        if colname == "Notes" or colname == "Status":
            return Qt.ItemIsEditable | Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsEnabled

    def add_take(self, sequence: str, slate:str, take: int, description: str, quality: str, timecode: str):
        # self._data.append({
        #     'Sequence': sequence,
        #     'Slate': slate,   
        #     'Take': take,
        #     'Timecode': timecode,
        #     'Duration': 0.0,
        #     'Status': 'G',
        #     'Notes': description
        # })
        root_index = self.createIndex(0, 0, self.rootItem)
        sequence_item = self.get_sequence(sequence)

        if not sequence_item:
            sequence_item = SequenceItem(sequence, self.rootItem)
            sequence_index = self.createIndex(self.rootItem.row(), 0, self.rootItem)
            self.beginInsertRows(sequence_index, self.rootItem.rowCount(), self.rootItem.rowCount()+1)
            self.rootItem.appendRow(sequence_item)
            self.endInsertRows()
            #self.dataChanged.emit(sequence_index, sequence_index, sequence_item)
            LOGGER.info(f"Adding sequence {sequence}")                

        slate_item = sequence_item.get_slate(slate)
        if not slate_item:
            slate_item = SlateItem(sequence_item, slate)
            slate_index = self.createIndex(sequence_item.row(), 0, slate_item)
            self.beginInsertRows(slate_index, sequence_item.rowCount(), sequence_item.rowCount()+1)
            sequence_item.appendRow(slate_item)
            self.endInsertRows()
            #self.dataChanged.emit(slate_index, slate_index, slate_item)
            LOGGER.info(f"Adding slate {slate}")                

        take_item = slate_item.get_take(take)
        if not take_item:
            self.layoutAboutToBeChanged.emit()
            take_item = TakeItem(slate_item, take, timecode, 0, "", description)
            slate_index = self.createIndex(slate_item.row(), 0, slate_item)
            # LOGGER.info(f"Slate index {slate_index}. RowCount {slate_item.rowCount()}")
            self.beginInsertRows(slate_index, slate_item.rowCount(), slate_item.rowCount()+1)
            slate_item.appendRow(take_item)
            take_index = self.createIndex(take_item.row(), 0, take_item)
            self.endInsertRows()
            LOGGER.info(f"Adding take {take}. Take index is {take_index}")
            #self.dataChanged.emit(sequence_item.row(), sequence_index, [Qt.DisplayRole])
            #self.dataChanged.emit(QModelIndex(), QModelIndex(), [Qt.DisplayRole])
            self.layoutChanged.emit()
        else:
            print("Take already exists in slate")
            #take_item = slate_item[take]
            
        #self.endInsertRows()

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if role == Qt.EditRole:
            column = index.column()
            item = index.internalPointer()
            print(f"Setting item data for {item}")

            if isinstance(item, SequenceItem):
                #item.setData(value)
                pass
            elif isinstance(item, SlateItem):
                #item.setData(value)
                pass
            elif isinstance(item, TakeItem):
                LOGGER.info(f"Modifying take data. Col is {self.colnames[column]}")

                # if column == 0:  # Edit the "Take" value
                #     pass
                # elif column == 1:  # Edit the "Status" value
                #     item.child(0, column).setData(value)
                # elif column == 2:  # Edit the "Notes" value
                #     item.child(0, column).setData(value)

                colname = self.colnames[column]
                if colname == "Notes":
                    item.setNotes(value)
                elif colname == "Status":
                    item.setStatus(value)
            
            self.dataChanged.emit(index, item)
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
        result = self.rootItem.flatten()
        LOGGER.info(result)

        with open(self.project_takelist_path(), 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=CSV_HEADER_DATA)
            writer.writeheader()
            for row in result:
                writer.writerow(row)
            #for row in self._data:
            #    writer.writerow(row)

    def data(self, index: QModelIndex, role:Qt.ItemDataRole=Qt.DisplayRole):
        # LOGGER.info(f"Getting data for index {index}")    
        if not index.isValid():
            # LOGGER.info(f"Index {index} not valid")    
            return None

        item = index.internalPointer()
        #LOGGER.info(f"Getting data for item {item}")    

        colname = self.colnames[index.column()]
        #LOGGER.info(f"Getting data for colname {colname}")

        if role == Qt.DisplayRole:
            item_data = None
            try:
                item_data = item.data(colname)
            except KeyError as e:
                LOGGER.error(f"KeyError: {e}. Item is {item}")
                return ""
                return LOGGER.error(f"KeyError: {e}. Item is {item}")
            finally:
                if item_data:
                    return item_data
                else:
                    return ""

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
