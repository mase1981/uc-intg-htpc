"""
HTPC setup flow for device configuration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import RequestUserInput
from ucapi_framework import BaseSetupFlow

from uc_intg_htpc.client import HTCPClient
from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)


class HTCPSetupFlow(BaseSetupFlow[HTCPConfig]):
    """Setup flow for HTPC System Monitor integration."""

    def get_manual_entry_form(self) -> RequestUserInput:
        return RequestUserInput(
            {"en": "HTPC System Monitor Setup"},
            [
                {
                    "id": "name",
                    "label": {"en": "Device Name"},
                    "field": {"text": {"value": "HTPC"}},
                },
                {
                    "id": "host",
                    "label": {"en": "HTPC IP Address"},
                    "field": {"text": {"value": ""}},
                },
                {
                    "id": "enable_hardware_monitoring",
                    "label": {"en": "Hardware Monitoring"},
                    "field": {
                        "dropdown": {
                            "value": "enabled",
                            "items": [
                                {
                                    "id": "enabled",
                                    "label": {"en": "Enabled (Requires LibreHardwareMonitor)"},
                                },
                                {
                                    "id": "disabled",
                                    "label": {"en": "Disabled (Remote Control Only)"},
                                },
                            ],
                        }
                    },
                },
                {
                    "id": "temperature_unit",
                    "label": {"en": "Temperature Unit"},
                    "field": {
                        "dropdown": {
                            "value": "celsius",
                            "items": [
                                {"id": "celsius", "label": {"en": "Celsius"}},
                                {"id": "fahrenheit", "label": {"en": "Fahrenheit"}},
                            ],
                        }
                    },
                },
                {
                    "id": "mac_address",
                    "label": {"en": "MAC Address (Optional - for Wake-on-LAN)"},
                    "field": {"text": {"value": ""}},
                },
            ],
        )

    async def query_device(
        self, input_values: dict[str, Any]
    ) -> HTCPConfig | RequestUserInput:
        host = input_values.get("host", "").strip()
        if not host:
            raise ValueError("HTPC IP address is required")

        name = input_values.get("name", "HTPC").strip()
        enable_hw = input_values.get("enable_hardware_monitoring", "enabled") == "enabled"
        temp_unit = input_values.get("temperature_unit", "celsius")
        mac = input_values.get("mac_address", "").strip()

        config = HTCPConfig(
            identifier=f"htpc_{host.replace('.', '_')}",
            name=name,
            host=host,
            enable_hardware_monitoring=enable_hw,
            temperature_unit=temp_unit,
            mac_address=mac,
        )

        client = HTCPClient(config)
        try:
            if enable_hw:
                result = await client.test_lhm()
                if not result["success"]:
                    raise ValueError(
                        f"Cannot connect to LibreHardwareMonitor at {host}:{config.port}: "
                        f"{result.get('error', 'Unknown error')}"
                    )
                _LOG.info("LHM connection test passed with %d sensors", result.get("sensor_count", 0))

            agent_ok = await client.test_agent()
            if agent_ok:
                _LOG.info("HTPC Agent is reachable")
            else:
                _LOG.warning("HTPC Agent not detected (remote commands may not work)")
        finally:
            await client.close()

        _LOG.info("Setup complete: %s at %s (hw_monitoring=%s)", name, host, enable_hw)
        return config
