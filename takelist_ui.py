from PySide2.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QPushButton
from PySide2.QtCore import Slot, QSortFilterProxyModel, QCoreApplication
from .takelist_model import TakeListModel
from .takelist_view import TakeListView 
from switchboard.switchboard_logging import ConsoleStream, LOGGER
from switchboard import switchboard_dialog as sb_dialog

class TakeListUI(QWidget):
    def __init__(self, parent: QWidget, model: TakeListModel):
        QWidget.__init__(self, parent)

        self.model = model
        self.proxymodel = QSortFilterProxyModel()
        self.proxymodel.setSourceModel(self.model)

        layout = QVBoxLayout(self)
        layout.addLayout(self.create_button_row_layout())
        layout.addWidget(TakeListView(self, self.proxymodel))

        LOGGER.info(f"Top level widget: {QCoreApplication.instance().findChild(sb_dialog.SwitchboardDialog)}")

    def create_button_row_layout(self) -> QHBoxLayout:
        layout_buttons = QHBoxLayout()

        save_take_btn = QPushButton('Save take list')
        save_take_btn.setToolTip(
            'Save the current take list to a csv file')
        save_take_btn.clicked.connect(self.on_save_take_btn_clicked)

        layout_buttons.addWidget(save_take_btn)

        load_take_btn = QPushButton('Open take list')
        save_take_btn.setToolTip(
            'Loads a take list from a csv file')
        save_take_btn.clicked.connect(self.on_load_take_btn_clicked)

        layout_buttons.addWidget(save_take_btn)
        layout_buttons.addWidget(load_take_btn)

        return layout_buttons

    @Slot()
    def on_save_take_btn_clicked(self):
        print("Save  Clicked")
        self.model.save_data()

    @Slot()
    def on_load_take_btn_clicked(self):
        print("Load Clicked")
