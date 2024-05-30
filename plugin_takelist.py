from switchboard.devices.device_base import Device, DeviceStatus
from switchboard.devices.device_widget_base import DeviceWidget
from switchboard.config import SETTINGS
from switchboard.switchboard_logging import ConsoleStream, LOGGER

from .takelist_ui import TakeListUI
from .takelist_model import TakeListModel

from PySide2 import QtCore
from PySide2 import QtWidgets

class DeviceTakeList(Device):
    takelist_ui = None
    takelist_model = None

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, **kwargs)
        self.status = DeviceStatus.READY
        self.autojoin_mu_server = False

    @staticmethod
    def plugin_settings():
        return Device.plugin_settings()

    @property
    def is_recording_device(self):
        return True

    @property
    def is_connected(self):
        return True

    @classmethod
    def create_takelist_model_if_necessary(cls):
        ''' Creates the Takelist model if it doesn't exist yet.
        '''
        if not cls.takelist_model:
            cls.takelist_model = TakeListModel(None)

        return cls.takelist_model

    @classmethod
    def plug_into_ui(cls, menubar, tabs):
        '''
        Implementation of base class function that allows plugin to inject
        UI elements.
        '''
        cls.create_takelist_model_if_necessary()

        # Create Monitor UI if it doesn't exist
        if not cls.takelist_ui:
            cls.takelist_ui = TakeListUI(parent=tabs, model=cls.takelist_model)

        # Add our monitor UI to the main tabs in the UI
        tabs.addTab(cls.takelist_ui, 'Take &List')

    def record_start(self, slate, take, description):
        """
        Called by switchboard_dialog when recording was started
        """
        self._slate = slate
        self._take = take
        self._description = description
        self.record_start_confirm("00:00:00:00")

    def record_stop(self):
        """
        Called by switchboard_dialog when recording was stopped.
        """
        timecode = "00:00:00:00"

        take_info_dialog = TakeInfoDialog()
        try:
            take_info_dialog.ui.exec()
        finally:
            DeviceTakeList.takelist_model.add_take(SETTINGS.CURRENT_SEQUENCE, self._slate, self._take, take_info_dialog.get_description(), take_info_dialog.get_quality(), timecode)
        self.record_stop_confirm(timecode)

    def load_takes_from_json(self):
        """
        Load takes from json file
        """
        DeviceTakeList.takelist_model.load_takes_from_json()


class DeviceWidgetTakeList(DeviceWidget):
    def __init__(self, name, device_hash, address, icons, parent=None):
        super().__init__(name, device_hash, address, icons, parent=parent)

    def _add_control_buttons(self):
        pass
        #super()._add_control_buttons()


class TakeInfoDialog(QtCore.QObject):
    def __init__(self):
        super().__init__()

        # Set the UI object
        self.ui = QtWidgets.QDialog()
        self.ui.resize(400, 50)
        dialog_layout = QtWidgets.QVBoxLayout(self.ui)
        dialog_layout.setContentsMargins(4, 4, 4, 4)
        self.ui.setWindowTitle("Take Info")

        self.ui.take_info_layout = QtWidgets.QWidget()
        
        # Take description
        desc_layout = QtWidgets.QHBoxLayout(self.ui.take_info_layout)
        self.ui.description_label = QtWidgets.QLabel()
        self.ui.description_label.setText("Description")
        self.ui.description_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.ui.description_line_edit = QtWidgets.QLineEdit()
        # self.ui.description_line_edit.textChanged.connect(
        #     self.config_path_text_changed)
        desc_layout.addWidget(self.ui.description_label)
        desc_layout.addWidget(self.ui.description_line_edit)
        dialog_layout.addLayout(desc_layout)
        
        # Take quality
        quality_layout = QtWidgets.QHBoxLayout(self.ui.take_info_layout)
        self.ui.quality_label = QtWidgets.QLabel()
        self.ui.quality_label.setText("Quality")
        self.ui.quality_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.ui.quality_combo_box = QtWidgets.QComboBox()
        self.ui.quality_combo_box.addItem("⭐", "S")
        self.ui.quality_combo_box.addItem("✔️", "G")
        self.ui.quality_combo_box.addItem("❌", "NG")

        # self.ui.quality_combo_box.currentIndexChanged.connect(
        #     self.config_path_text_changed)
        quality_layout.addWidget(self.ui.quality_label)
        quality_layout.addWidget(self.ui.quality_combo_box)
        dialog_layout.addLayout(quality_layout)

        dialog_layout.addWidget(self.ui.take_info_layout)

    def get_quality(self):
        return self.ui.quality_combo_box.itemData(self.ui.quality_combo_box.currentIndex())
    
    def get_description(self):
        return self.ui.description_line_edit.text()
