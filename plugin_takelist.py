from switchboard.devices.device_base import Device, DeviceStatus
from switchboard.devices.device_widget_base import DeviceWidget
from switchboard.config import SETTINGS

from .takelist_ui import TakeListUI
from .takelist_model import TakeListModel

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
        DeviceTakeList.takelist_model.add_take(SETTINGS.CURRENT_SEQUENCE, self._slate, self._take, "" if self._description == "description" else self._description, timecode)
        self.record_stop_confirm(timecode)


class DeviceWidgetTakeList(DeviceWidget):
    def __init__(self, name, device_hash, address, icons, parent=None):
        super().__init__(name, device_hash, address, icons, parent=parent)

    def _add_control_buttons(self):
        pass
        #super()._add_control_buttons()
