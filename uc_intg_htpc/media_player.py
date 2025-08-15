"""
HTPC Media Player Entity with Base64 Image Embedding.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import base64
import logging
import os
from typing import Callable

from ucapi import IntegrationAPI, MediaPlayer, StatusCodes, entity
from ucapi.media_player import Attributes, Commands, Features, States

from uc_intg_htpc.client import HTCPClient
from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)

class HTCPMediaPlayer(MediaPlayer):
    """A MediaPlayer entity representing the HTPC's system status with base64 image embedding."""

    def __init__(self, client: HTCPClient, config: HTCPConfig, api: IntegrationAPI):
        self._client = client
        self._config = config
        self._api = api
        self._icon_cache = {}
        
        features = [
            Features.ON_OFF,
            Features.SELECT_SOURCE,
            Features.VOLUME,
            Features.MUTE_TOGGLE,
        ]

        source_list = [
            "System Overview",
            "CPU Performance", 
            "Memory Usage",
            "Storage Activity",
            "Network Activity",
            "Temperature Overview",
            "Fan Monitoring",
            "Power Consumption"
        ]
        
        if hasattr(client._system_data, 'has_dedicated_gpu') and client._system_data.has_dedicated_gpu:
            source_list.insert(2, "GPU Performance")

        super().__init__(
            identifier="htpc_monitor",
            name={"en": "HTPC System Monitor"},
            features=features,
            attributes={
                Attributes.STATE: States.ON,
                Attributes.SOURCE_LIST: source_list,
                Attributes.SOURCE: "System Overview",
                Attributes.MEDIA_TITLE: "Initializing...",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("system_overview.png"),
                Attributes.VOLUME: 50,
                Attributes.MUTED: False,
            },
            cmd_handler=self.handle_command
        )

    def _get_icon_base64(self, icon_filename: str) -> str:
        """Get the base64 encoded icon data - EXACT weather integration method."""
        if icon_filename in self._icon_cache:
            return self._icon_cache[icon_filename]

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_dir = os.path.join(script_dir, "icons")
        icon_path = os.path.join(icon_dir, icon_filename)
        fallback_icons = ["system_overview.png", "cpu_monitor.png"]

        if not os.path.exists(icon_path):
            _LOG.warning(f"Icon not found: {icon_filename}")
            for fallback in fallback_icons:
                icon_path = os.path.join(icon_dir, fallback)
                if os.path.exists(icon_path):
                    _LOG.info(f"Using fallback icon: {fallback}")
                    break
            else:
                _LOG.error("No fallback icons found")
                return ""

        try:
            with open(icon_path, 'rb') as f:
                icon_data = f.read()
                base64_data = base64.b64encode(icon_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_data}"
                self._icon_cache[icon_filename] = data_url
                return data_url
        except Exception as e:
            _LOG.error(f"Failed to read icon {icon_path}: {e}")
            return ""

    def _get_source_image(self, source: str) -> str:
        """Get the proper base64 image data for a given source."""
        source_images = {
            "System Overview": "system_overview.png",
            "CPU Performance": "cpu_monitor.png",
            "GPU Performance": "gpu_monitor.png", 
            "Memory Usage": "memory_usage.png",
            "Storage Activity": "storage_monitor.png",
            "Network Activity": "network_activity.png",
            "Temperature Overview": "temperatures.png",
            "Fan Monitoring": "fan_monitoring.png",
            "Power Consumption": "power_consumption.png"
        }
        
        image_filename = source_images.get(source, "system_overview.png")
        return self._get_icon_base64(image_filename)

    async def handle_command(self, entity_arg: entity.Entity, cmd_id: str, params: dict | None) -> StatusCodes:
        """Handle commands for the media player entity."""
        _LOG.debug(f"HTCPMediaPlayer received command: {cmd_id}")
        
        if cmd_id == Commands.OFF:
            await self._client.power_sleep()
            self.attributes[Attributes.STATE] = States.STANDBY
        elif cmd_id == Commands.ON:
            await self._client.power_wake()
            self.attributes[Attributes.STATE] = States.ON
        elif cmd_id == Commands.SELECT_SOURCE:
            source = params.get("source")
            self.attributes[Attributes.SOURCE] = source
            self.attributes[Attributes.MEDIA_IMAGE_URL] = self._get_source_image(source)
            _LOG.info(f"Switched monitoring view to: {source}")
        elif cmd_id == Commands.VOLUME:
            volume = params.get("volume", 50)
            await self._client.set_volume(volume)
            self.attributes[Attributes.VOLUME] = volume
        elif cmd_id == Commands.VOLUME_UP:
            current_volume = self.attributes.get(Attributes.VOLUME, 50)
            new_volume = min(100, current_volume + 5)
            await self._client.set_volume(new_volume)
            self.attributes[Attributes.VOLUME] = new_volume
        elif cmd_id == Commands.VOLUME_DOWN:
            current_volume = self.attributes.get(Attributes.VOLUME, 50)
            new_volume = max(0, current_volume - 5)
            await self._client.set_volume(new_volume)
            self.attributes[Attributes.VOLUME] = new_volume
        elif cmd_id == Commands.MUTE_TOGGLE:
            await self._client.mute_toggle()
            self.attributes[Attributes.MUTED] = not self.attributes.get(Attributes.MUTED, False)
        elif cmd_id in [Commands.PLAY_PAUSE, Commands.SHUFFLE, Commands.REPEAT, Commands.STOP, Commands.NEXT, Commands.PREVIOUS]:
            _LOG.debug(f"Ignoring unsupported media command '{cmd_id}' to prevent UI error.")
            return StatusCodes.OK
        else:
            _LOG.warning(f"Unhandled command: {cmd_id}")
            return StatusCodes.NOT_IMPLEMENTED
        
        await self.push_update()
        return StatusCodes.OK

    async def run_monitoring(self):
        """Periodically fetch data and update the entity."""
        while True:
            try:
                await self.push_update()
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                _LOG.info("Monitoring task cancelled")
                break
            except Exception as e:
                _LOG.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(30)

    async def push_update(self):
        """Fetches the latest data and pushes it to the API."""
        if not self._api.configured_entities.contains(self.id):
            return

        if not await self._client.update_system_data():
            self.attributes.update({
                Attributes.STATE: States.OFF,
                Attributes.MEDIA_TITLE: "Connection Error",
                Attributes.MEDIA_ARTIST: "Unable to reach HTPC",
                Attributes.MEDIA_ALBUM: "Check LibreHardwareMonitor",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("system_overview.png")
            })
            self._api.configured_entities.update_attributes(self.id, self.attributes)
            return

        data = self._client.system_data
        current_source = self.attributes.get(Attributes.SOURCE, "System Overview")
        
        attrs_to_update = {
            Attributes.STATE: States.ON,
            Attributes.SOURCE_LIST: self.attributes[Attributes.SOURCE_LIST],
            Attributes.SOURCE: current_source,
            Attributes.VOLUME: self.attributes.get(Attributes.VOLUME, 50),
            Attributes.MUTED: self.attributes.get(Attributes.MUTED, False),
        }
        
        def format_temp(temp_c):
            if temp_c is None:
                return "N/A"
            converted = self._config.convert_temperature(temp_c)
            symbol = self._config.temperature_symbol()
            return f"{converted:.1f}{symbol}"

        def format_percent(value):
            return f"{value:.1f}%" if value is not None else "N/A"

        def format_memory(used, total):
            if used is None or total is None:
                return "N/A"
            return f"{used:.1f}/{total:.1f} GB ({(used/total)*100:.1f}%)"

        def format_speed(speed):
            if speed is None:
                return "N/A"
            if speed > 1000:
                return f"{speed/1000:.2f} Gbps"
            return f"{speed:.1f} Mbps"

        if current_source == "System Overview":
            cpu_power_info = f"Power: {data.cpu_power or 0:.1f}W" if data.cpu_power else "Power: N/A"
                
            attrs_to_update.update({
                Attributes.MEDIA_TITLE: f"CPU: {format_temp(data.cpu_temp)} ({format_percent(data.cpu_load)})",
                Attributes.MEDIA_ARTIST: cpu_power_info,
                Attributes.MEDIA_ALBUM: format_memory(data.memory_used, data.memory_total),
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("system_overview.png")
            })
        
        elif current_source == "CPU Performance":
            attrs_to_update.update({
                Attributes.MEDIA_TITLE: f"Temperature: {format_temp(data.cpu_temp)}",
                Attributes.MEDIA_ARTIST: f"Load: {format_percent(data.cpu_load)}",
                Attributes.MEDIA_ALBUM: f"Clock: {data.cpu_clock or 0:.0f} MHz",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("cpu_monitor.png")
            })
        
        elif current_source == "GPU Performance":
            if data.gpu_temp is not None or data.gpu_load is not None:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: f"Temperature: {format_temp(data.gpu_temp)}",
                    Attributes.MEDIA_ARTIST: f"Load: {format_percent(data.gpu_load)}",
                    Attributes.MEDIA_ALBUM: "Dedicated Graphics",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("gpu_monitor.png")
                })
            else:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: "No Dedicated GPU",
                    Attributes.MEDIA_ARTIST: "Using Integrated Graphics",
                    Attributes.MEDIA_ALBUM: "Intel/AMD Integrated",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("gpu_monitor.png")
                })
        
        elif current_source == "Memory Usage":
            memory_percent = ((data.memory_used or 0) / (data.memory_total or 1)) * 100
            attrs_to_update.update({
                Attributes.MEDIA_TITLE: f"Used: {data.memory_used or 0:.1f} GB",
                Attributes.MEDIA_ARTIST: f"Total: {data.memory_total or 0:.1f} GB",
                Attributes.MEDIA_ALBUM: f"Usage: {memory_percent:.1f}%",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("memory_usage.png")
            })
        
        elif current_source == "Storage Activity":
            if data.storage_total and data.storage_used:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: f"Used: {data.storage_used:.1f} GB",
                    Attributes.MEDIA_ARTIST: f"Total: {data.storage_total:.1f} GB", 
                    Attributes.MEDIA_ALBUM: f"Usage: {data.storage_used_percent or 0:.1f}%",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("storage_monitor.png")
                })
            else:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: f"Usage: {data.storage_used_percent or 0:.1f}%",
                    Attributes.MEDIA_ARTIST: "Primary Drive",
                    Attributes.MEDIA_ALBUM: "Size calculation unavailable",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("storage_monitor.png")
                })
        
        elif current_source == "Network Activity":
            attrs_to_update.update({
                Attributes.MEDIA_TITLE: f"Download: {format_speed(data.network_down)}",
                Attributes.MEDIA_ARTIST: f"Upload: {format_speed(data.network_up)}",
                Attributes.MEDIA_ALBUM: "Active Interface",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("network_activity.png")
            })
        
        elif current_source == "Temperature Overview":
            cpu_temp_str = format_temp(data.cpu_temp)
            storage_temp_str = format_temp(data.storage_temp) if data.storage_temp else "N/A"
            motherboard_temp_str = format_temp(data.motherboard_temp_avg) if data.motherboard_temp_avg else "N/A"
                
            attrs_to_update.update({
                Attributes.MEDIA_TITLE: f"CPU: {cpu_temp_str}",
                Attributes.MEDIA_ARTIST: f"Storage: {storage_temp_str}",
                Attributes.MEDIA_ALBUM: f"Motherboard: {motherboard_temp_str}",
                Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("temperatures.png")
            })
        
        elif current_source == "Fan Monitoring":
            if data.fan_speeds:
                active_fans = len(data.fan_speeds)
                avg_speed = sum(data.fan_speeds) / len(data.fan_speeds)
                max_speed = max(data.fan_speeds)
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: f"Active Fans: {active_fans}",
                    Attributes.MEDIA_ARTIST: f"Average: {avg_speed:.0f} RPM",
                    Attributes.MEDIA_ALBUM: f"Maximum: {max_speed:.0f} RPM",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("fan_monitoring.png")
                })
            else:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: "No Fan Data",
                    Attributes.MEDIA_ARTIST: "Fans not detected",
                    Attributes.MEDIA_ALBUM: "Check LibreHardwareMonitor",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("fan_monitoring.png")
                })
        
        elif current_source == "Power Consumption":
            if data.cpu_power:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: f"CPU Package: {data.cpu_power:.1f}W",
                    Attributes.MEDIA_ARTIST: "Real-time Power Draw",
                    Attributes.MEDIA_ALBUM: "LibreHardwareMonitor",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("power_consumption.png")
                })
            else:
                attrs_to_update.update({
                    Attributes.MEDIA_TITLE: "Power Monitoring",
                    Attributes.MEDIA_ARTIST: "No power sensors detected",
                    Attributes.MEDIA_ALBUM: "Requires compatible hardware",
                    Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("power_consumption.png")
                })
        
        self.attributes.update(attrs_to_update)
        self._api.configured_entities.update_attributes(self.id, attrs_to_update)
        _LOG.debug(f"Pushed display update for source: {current_source}")