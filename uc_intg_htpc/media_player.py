"""
HTPC media player entity for system monitoring display.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
from typing import Any

from ucapi import StatusCodes, media_player
from ucapi_framework import MediaPlayerEntity

from uc_intg_htpc.config import HTCPConfig
from uc_intg_htpc.const import MONITORING_VIEWS
from uc_intg_htpc.device import HTCPDevice

_LOG = logging.getLogger(__name__)

SOURCE_ICONS = {
    "System Overview": "system_overview.png",
    "CPU Performance": "cpu_monitor.png",
    "GPU Performance": "gpu_monitor.png",
    "Memory Usage": "memory_usage.png",
    "Storage Activity": "storage_monitor.png",
    "Network Activity": "network_activity.png",
    "Temperature Overview": "temperatures.png",
    "Fan Monitoring": "fan_monitoring.png",
    "Power Consumption": "power_consumption.png",
}

FEATURES = [
    media_player.Features.ON_OFF,
    media_player.Features.SELECT_SOURCE,
    media_player.Features.VOLUME,
    media_player.Features.MUTE_TOGGLE,
    media_player.Features.MEDIA_IMAGE_URL,
    media_player.Features.MEDIA_TITLE,
    media_player.Features.MEDIA_ARTIST,
    media_player.Features.MEDIA_ALBUM,
]


class HTCPMediaPlayer(MediaPlayerEntity):
    """Media player entity displaying HTPC monitoring views with base64 icons."""

    def __init__(self, device_config: HTCPConfig, device: HTCPDevice) -> None:
        self._device = device
        entity_id = f"media_player.{device_config.identifier}"
        super().__init__(
            entity_id,
            device_config.name,
            FEATURES,
            {
                media_player.Attributes.STATE: media_player.States.STANDBY,
                media_player.Attributes.SOURCE_LIST: MONITORING_VIEWS,
                media_player.Attributes.SOURCE: "",
                media_player.Attributes.MEDIA_IMAGE_URL: "",
                media_player.Attributes.MEDIA_TITLE: "",
                media_player.Attributes.MEDIA_ARTIST: "",
                media_player.Attributes.MEDIA_ALBUM: "",
                media_player.Attributes.VOLUME: 50,
                media_player.Attributes.MUTED: False,
            },
            cmd_handler=self._handle_command,
        )
        self.subscribe_to_device(device)

    async def sync_state(self) -> None:
        if self._device.state == "UNAVAILABLE":
            self.update({
                media_player.Attributes.STATE: media_player.States.UNAVAILABLE,
                media_player.Attributes.MEDIA_TITLE: "Connection Lost",
                media_player.Attributes.MEDIA_ARTIST: "Attempting reconnection...",
                media_player.Attributes.MEDIA_ALBUM: "",
            })
            return

        data = self._device.system_data
        view = self._device.current_view
        icon_file = SOURCE_ICONS.get(view, "system_overview.png")

        attrs: dict[str, Any] = {
            media_player.Attributes.STATE: media_player.States.ON,
            media_player.Attributes.SOURCE_LIST: MONITORING_VIEWS,
            media_player.Attributes.SOURCE: view,
            media_player.Attributes.MEDIA_IMAGE_URL: self._device.get_icon_base64(icon_file),
        }
        attrs.update(self._format_view_data(view, data))
        self.update(attrs)

    def _format_view_data(self, view: str, data: Any) -> dict[str, Any]:
        cfg = self._device.config

        def fmt_temp(val: float | None) -> str:
            if val is None:
                return "N/A"
            return f"{cfg.convert_temperature(val):.1f}{cfg.temperature_symbol()}"

        def fmt_pct(val: float | None) -> str:
            return f"{val:.1f}%" if val is not None else "N/A"

        def fmt_speed(val: float | None) -> str:
            if val is None:
                return "N/A"
            if val > 1000:
                return f"{val / 1000:.2f} Gbps"
            return f"{val:.1f} Mbps"

        match view:
            case "System Overview":
                power = f"Power: {data.cpu_power:.1f}W" if data.cpu_power else "Power: N/A"
                mem = "N/A"
                if data.memory_used is not None and data.memory_total:
                    pct = (data.memory_used / data.memory_total) * 100
                    mem = f"{data.memory_used:.1f}/{data.memory_total:.1f} GB ({pct:.1f}%)"
                return {
                    media_player.Attributes.MEDIA_TITLE: f"CPU: {fmt_temp(data.cpu_temp)} ({fmt_pct(data.cpu_load)})",
                    media_player.Attributes.MEDIA_ARTIST: power,
                    media_player.Attributes.MEDIA_ALBUM: mem,
                }
            case "CPU Performance":
                return {
                    media_player.Attributes.MEDIA_TITLE: f"Temperature: {fmt_temp(data.cpu_temp)}",
                    media_player.Attributes.MEDIA_ARTIST: f"Load: {fmt_pct(data.cpu_load)}",
                    media_player.Attributes.MEDIA_ALBUM: f"Clock: {data.cpu_clock or 0:.0f} MHz",
                }
            case "GPU Performance":
                if data.gpu_temp is not None or data.gpu_load is not None:
                    return {
                        media_player.Attributes.MEDIA_TITLE: f"Temperature: {fmt_temp(data.gpu_temp)}",
                        media_player.Attributes.MEDIA_ARTIST: f"Load: {fmt_pct(data.gpu_load)}",
                        media_player.Attributes.MEDIA_ALBUM: "Dedicated Graphics",
                    }
                return {
                    media_player.Attributes.MEDIA_TITLE: "No Dedicated GPU",
                    media_player.Attributes.MEDIA_ARTIST: "Using Integrated Graphics",
                    media_player.Attributes.MEDIA_ALBUM: "",
                }
            case "Memory Usage":
                pct = ((data.memory_used or 0) / (data.memory_total or 1)) * 100
                return {
                    media_player.Attributes.MEDIA_TITLE: f"Used: {data.memory_used or 0:.1f} GB",
                    media_player.Attributes.MEDIA_ARTIST: f"Total: {data.memory_total or 0:.1f} GB",
                    media_player.Attributes.MEDIA_ALBUM: f"Usage: {pct:.1f}%",
                }
            case "Storage Activity":
                if data.storage_total and data.storage_used:
                    return {
                        media_player.Attributes.MEDIA_TITLE: f"Used: {data.storage_used:.1f} GB",
                        media_player.Attributes.MEDIA_ARTIST: f"Total: {data.storage_total:.1f} GB",
                        media_player.Attributes.MEDIA_ALBUM: f"Usage: {data.storage_used_percent or 0:.1f}%",
                    }
                return {
                    media_player.Attributes.MEDIA_TITLE: f"Usage: {data.storage_used_percent or 0:.1f}%",
                    media_player.Attributes.MEDIA_ARTIST: "Primary Drive",
                    media_player.Attributes.MEDIA_ALBUM: "",
                }
            case "Network Activity":
                return {
                    media_player.Attributes.MEDIA_TITLE: f"Download: {fmt_speed(data.network_down)}",
                    media_player.Attributes.MEDIA_ARTIST: f"Upload: {fmt_speed(data.network_up)}",
                    media_player.Attributes.MEDIA_ALBUM: "Active Interface",
                }
            case "Temperature Overview":
                return {
                    media_player.Attributes.MEDIA_TITLE: f"CPU: {fmt_temp(data.cpu_temp)}",
                    media_player.Attributes.MEDIA_ARTIST: f"Storage: {fmt_temp(data.storage_temp)}",
                    media_player.Attributes.MEDIA_ALBUM: f"Motherboard: {fmt_temp(data.motherboard_temp_avg)}",
                }
            case "Fan Monitoring":
                if data.fan_speeds:
                    avg = sum(data.fan_speeds) / len(data.fan_speeds)
                    return {
                        media_player.Attributes.MEDIA_TITLE: f"Active Fans: {len(data.fan_speeds)}",
                        media_player.Attributes.MEDIA_ARTIST: f"Average: {avg:.0f} RPM",
                        media_player.Attributes.MEDIA_ALBUM: f"Maximum: {max(data.fan_speeds):.0f} RPM",
                    }
                return {
                    media_player.Attributes.MEDIA_TITLE: "No Fan Data",
                    media_player.Attributes.MEDIA_ARTIST: "Fans not detected",
                    media_player.Attributes.MEDIA_ALBUM: "",
                }
            case "Power Consumption":
                if data.cpu_power:
                    return {
                        media_player.Attributes.MEDIA_TITLE: f"CPU Package: {data.cpu_power:.1f}W",
                        media_player.Attributes.MEDIA_ARTIST: "Real-time Power Draw",
                        media_player.Attributes.MEDIA_ALBUM: "",
                    }
                return {
                    media_player.Attributes.MEDIA_TITLE: "Power Monitoring",
                    media_player.Attributes.MEDIA_ARTIST: "No power sensors detected",
                    media_player.Attributes.MEDIA_ALBUM: "",
                }
            case _:
                return {
                    media_player.Attributes.MEDIA_TITLE: view,
                    media_player.Attributes.MEDIA_ARTIST: "",
                    media_player.Attributes.MEDIA_ALBUM: "",
                }

    async def _handle_command(
        self, entity: Any, cmd_id: str, params: dict[str, Any] | None
    ) -> StatusCodes:
        match cmd_id:
            case media_player.Commands.ON:
                pass
            case media_player.Commands.OFF:
                await self._device.send_command("power_sleep")
            case media_player.Commands.SELECT_SOURCE:
                source = params.get("source", "") if params else ""
                if source in MONITORING_VIEWS:
                    self._device.set_current_view(source)
            case media_player.Commands.VOLUME:
                volume = params.get("volume", 50) if params else 50
                await self._device.send_command(f"set_volume:{volume}")
            case media_player.Commands.VOLUME_UP:
                await self._device.send_command("volume_up")
            case media_player.Commands.VOLUME_DOWN:
                await self._device.send_command("volume_down")
            case media_player.Commands.MUTE_TOGGLE:
                await self._device.send_command("mute")
            case (
                media_player.Commands.PLAY_PAUSE
                | media_player.Commands.STOP
                | media_player.Commands.NEXT
                | media_player.Commands.PREVIOUS
            ):
                return StatusCodes.OK
            case _:
                return StatusCodes.NOT_IMPLEMENTED

        self._device.push_update()
        return StatusCodes.OK
