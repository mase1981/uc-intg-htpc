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
    """Configuration manager for HTCP integration."""

    def __init__(self, config_dir: str = "./"):
        """
        Initialize configuration manager.
        
        :param config_dir: configuration directory path
        """
        self._config_dir = config_dir
        self._config_file = os.path.join(config_dir, "config.json")
        self._config: Dict[str, Any] = {}
        self._load_config()

    def _load_config(self) -> None:
        """Load configuration from file."""
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
        """
        Save configuration to file.
        
        :return: True if successful, False otherwise
        """
        try:
            os.makedirs(self._config_dir, exist_ok=True)
            with open(self._config_file, "w", encoding="utf-8") as file:
                json.dump(self._config, file, indent=2)
            _LOG.info("Configuration saved to %s", self._config_file)
            return True
        except Exception as ex:
            _LOG.error("Failed to save configuration: %s", ex)
            return False

    def _default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "host": "192.168.1.100",
            "port": 8085,
            "temperature_unit": "celsius"
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update configuration with new values.
        
        :param new_config: new configuration values
        """
        self._config.update(new_config)

    @property
    def host(self) -> str:
        """Get HTCP host IP address."""
        return self._config.get("host", "192.168.1.100")

    @property
    def port(self) -> int:
        """Get LibreHardwareMonitor port."""
        return self._config.get("port", 8085)

    @property
    def temperature_unit(self) -> str:
        """Get temperature unit (celsius or fahrenheit)."""
        return self._config.get("temperature_unit", "celsius")

    @property
    def base_url(self) -> str:
        """Get base URL for LibreHardwareMonitor."""
        return f"http://{self.host}:{self.port}"

    def convert_temperature(self, celsius: float) -> float:
        """
        Convert temperature based on configured unit.
        
        :param celsius: temperature in Celsius
        :return: temperature in configured unit
        """
        if self.temperature_unit == "fahrenheit":
            return (celsius * 9/5) + 32
        return celsius

    def temperature_symbol(self) -> str:
        """Get temperature symbol based on configured unit."""
        return "°F" if self.temperature_unit == "fahrenheit" else "°C"


# Backwards compatibility alias
Config = HTCPConfig