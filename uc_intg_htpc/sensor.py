"""
HTPC sensor entities for system monitoring.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any, Callable

from ucapi import sensor
from ucapi_framework import SensorEntity

from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)


class HTCPSensor(SensorEntity):
    """Generic sensor entity for HTPC monitoring values."""

    def __init__(
        self,
        entity_id: str,
        name: str,
        unit: str,
        device_class: str,
        device: Any,
        value_getter: Callable,
    ) -> None:
        self._device = device
        self._value_getter = value_getter
        super().__init__(
            entity_id,
            name,
            [],
            {
                sensor.Attributes.STATE: sensor.States.UNKNOWN,
                sensor.Attributes.VALUE: "N/A",
                sensor.Attributes.UNIT: unit,
            },
            device_class=device_class,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({sensor.Attributes.STATE: sensor.States.UNAVAILABLE})
            return
        value = self._value_getter(self._device)
        self.update({
            sensor.Attributes.STATE: sensor.States.ON,
            sensor.Attributes.VALUE: value if value is not None else "N/A",
        })


def create_sensors(config: HTCPConfig, device: Any) -> list[SensorEntity]:
    """Create sensor entities based on configuration."""
    ident = config.identifier
    temp_unit = config.temperature_symbol()

    def _temp(attr: str) -> Callable:
        def getter(dev: Any) -> str | None:
            val = getattr(dev.system_data, attr, None)
            if val is not None:
                return f"{config.convert_temperature(val):.1f}"
            return None
        return getter

    def _pct(attr: str) -> Callable:
        def getter(dev: Any) -> str | None:
            val = getattr(dev.system_data, attr, None)
            if val is not None:
                return f"{val:.1f}"
            return None
        return getter

    def _val(attr: str) -> Callable:
        def getter(dev: Any) -> str | None:
            val = getattr(dev.system_data, attr, None)
            if val is not None:
                return f"{val:.1f}"
            return None
        return getter

    def _mem_pct(dev: Any) -> str | None:
        d = dev.system_data
        if d.memory_used is not None and d.memory_total and d.memory_total > 0:
            return f"{(d.memory_used / d.memory_total) * 100:.1f}"
        return None

    def _fan_avg(dev: Any) -> str | None:
        d = dev.system_data
        if d.fan_speeds:
            return f"{sum(d.fan_speeds) / len(d.fan_speeds):.0f}"
        return None

    def _net_speed(attr: str) -> Callable:
        def getter(dev: Any) -> str | None:
            val = getattr(dev.system_data, attr, None)
            if val is not None:
                return f"{val:.1f}"
            return None
        return getter

    sensors: list[SensorEntity] = []

    sensors.append(HTCPSensor(
        f"sensor.{ident}.cpu_temp", f"{config.name} CPU Temperature",
        temp_unit, sensor.DeviceClasses.TEMPERATURE, device, _temp("cpu_temp"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.cpu_load", f"{config.name} CPU Load",
        "%", sensor.DeviceClasses.CUSTOM, device, _pct("cpu_load"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.cpu_power", f"{config.name} CPU Power",
        "W", sensor.DeviceClasses.CUSTOM, device, _val("cpu_power"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.gpu_temp", f"{config.name} GPU Temperature",
        temp_unit, sensor.DeviceClasses.TEMPERATURE, device, _temp("gpu_temp"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.gpu_load", f"{config.name} GPU Load",
        "%", sensor.DeviceClasses.CUSTOM, device, _pct("gpu_load"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.memory_usage", f"{config.name} Memory Usage",
        "%", sensor.DeviceClasses.CUSTOM, device, _mem_pct,
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.storage_usage", f"{config.name} Storage Usage",
        "%", sensor.DeviceClasses.CUSTOM, device, _pct("storage_used_percent"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.network_down", f"{config.name} Network Download",
        "Mbps", sensor.DeviceClasses.CUSTOM, device, _net_speed("network_down"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.network_up", f"{config.name} Network Upload",
        "Mbps", sensor.DeviceClasses.CUSTOM, device, _net_speed("network_up"),
    ))
    sensors.append(HTCPSensor(
        f"sensor.{ident}.fan_speed", f"{config.name} Fan Speed",
        "RPM", sensor.DeviceClasses.CUSTOM, device, _fan_avg,
    ))

    return sensors
