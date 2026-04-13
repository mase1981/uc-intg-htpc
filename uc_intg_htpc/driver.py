"""
HTPC integration driver.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging

from ucapi_framework import BaseIntegrationDriver

from uc_intg_htpc.config import HTCPConfig
from uc_intg_htpc.device import HTCPDevice
from uc_intg_htpc.media_player import HTCPMediaPlayer
from uc_intg_htpc.remote import HTCPRemote
from uc_intg_htpc.sensor import create_sensors

_LOG = logging.getLogger(__name__)


class HTCPDriver(BaseIntegrationDriver[HTCPDevice, HTCPConfig]):
    """HTPC System Monitor integration driver."""

    def __init__(self):
        super().__init__(
            device_class=HTCPDevice,
            entity_classes=[
                lambda cfg, dev: [HTCPMediaPlayer(cfg, dev)] if cfg.enable_hardware_monitoring else [],
                HTCPRemote,
                lambda cfg, dev: create_sensors(cfg, dev) if cfg.enable_hardware_monitoring else [],
            ],
            driver_id="uc-intg-htpc",
        )
