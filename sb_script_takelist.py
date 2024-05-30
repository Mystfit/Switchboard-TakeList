# Copyright Epic Games, Inc. All Rights Reserved.

import json
import os
from pathlib import Path
import uuid

from switchboard.switchboard_scripting import SwitchboardScriptBase
from switchboard.switchboard_logging import LOGGER
from switchboard.config import CONFIG, SETTINGS, ROOT_CONFIGS_PATH, CONFIG_SUFFIX
from switchboard.devices.ndisplay.plugin_ndisplay import DevicenDisplay
from switchboard.switchboard_logging import LOGGER

class TakeListScript(SwitchboardScriptBase):
    params = {}

    def __init__(self, scriptargs):
        super().__init__(scriptargs)

        # if this causes an exception then the script won't run
        try:
            self.params = json.load(open(scriptargs))
        except:
            self.params = {}
            LOGGER.error(f"Could not load script arguments file '{scriptargs}'")
            return

    def on_preinit(self):
        super().on_preinit()

    def on_postinit(self, app):
        super().on_postinit(app)
        LOGGER.info(f"Inside takelist script: {app}")
 
    def on_exit(self):
        super().on_exit()
