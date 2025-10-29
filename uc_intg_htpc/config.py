"""
Configuration management for HTPC System Monitor Integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import json
import logging
import os
from typing import Any, Dict

_LOG = logging.getLogger(__name__)


class HTCPConfig:

    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = (
                os.getenv("UC_CONFIG_HOME") or 
                os.getenv("HOME") or 
                "/tmp"
            )
        
        self._config_dir = config_dir
        self._config_file = os.path.join(config_dir, "config.json")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        try:
            if os.path.exists(self._config_file):
                with open(self._config_file, "r", encoding="utf-8") as file:
                    self._config = json.load(file)
                    _LOG.info("Configuration loaded from %s", self._config_file)
            else:
                _LOG.info("No configuration file found, using defaults")
                self._config = self._default_config()
        except Exception as ex:
            _LOG.error("Failed to load configuration: %s", ex)
            self._config = self._default_config()

    def save_config(self) -> bool:
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            
            test_file = os.path.join(self._config_dir, ".write_test")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
            except (OSError, IOError) as e:
                _LOG.error("Config directory not writable (%s): %s", self._config_dir, e)
                return False
            
            with open(self._config_file, "w", encoding="utf-8") as file:
                json.dump(self._config, file, indent=2)
            _LOG.info("Configuration saved to %s", self._config_file)
            return True
        except Exception as ex:
            _LOG.error("Failed to save configuration to %s: %s", self._config_file, ex)
            return False

    def _default_config(self) -> Dict[str, Any]:
        return {
            "host": "",
            "port": 8085,
            "temperature_unit": "celsius",
            "mac_address": ""
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        self._config.update(new_config)

    @property
    def host(self) -> str:
        return self._config.get("host", "192.168.1.100")

    @property
    def port(self) -> int:
        return self._config.get("port", 8085)

    @property
    def temperature_unit(self) -> str:
        return self._config.get("temperature_unit", "celsius")

    @property
    def mac_address(self) -> str:
        return self._config.get("mac_address", "").strip()

    @property
    def wol_enabled(self) -> bool:
        return bool(self.mac_address)

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def convert_temperature(self, celsius: float) -> float:
        if self.temperature_unit == "fahrenheit":
            return (celsius * 9/5) + 32
        return celsius

    def temperature_symbol(self) -> str:
        return "°F" if self.temperature_unit == "fahrenheit" else "°C"


Config = HTCPConfig