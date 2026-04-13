"""
Configuration dataclass for HTPC System Monitor integration.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

from dataclasses import dataclass, field

from uc_intg_htpc.const import LHM_DEFAULT_PORT


@dataclass
class HTCPConfig:
    identifier: str = ""
    name: str = ""
    host: str = ""
    port: int = LHM_DEFAULT_PORT
    enable_hardware_monitoring: bool = True
    temperature_unit: str = "celsius"
    mac_address: str = ""

    @property
    def wol_enabled(self) -> bool:
        return bool(self.mac_address)

    def convert_temperature(self, celsius: float) -> float:
        if self.temperature_unit == "fahrenheit":
            return (celsius * 9 / 5) + 32
        return celsius

    def temperature_symbol(self) -> str:
        return "°F" if self.temperature_unit == "fahrenheit" else "°C"
