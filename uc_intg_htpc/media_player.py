"""
HTPC Media Player entity implementation.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import os
import base64
from typing import Any

from ucapi.api_definitions import StatusCodes
from ucapi.media_player import Attributes, Commands, Features, MediaPlayer, States

from uc_intg_htpc.client import HTCPClient
from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)


class HTCPMediaPlayer(MediaPlayer):
    """HTCP system monitor as media player entity."""

    def __init__(self, client: HTCPClient, config: HTCPConfig, api):
        """Initialize HTCP media player."""
        # Initialize icon cache FIRST - before any method calls
        self._icon_cache = {}
        
        features = [
            Features.ON_OFF,
            Features.SELECT_SOURCE,
            Features.VOLUME,
            Features.MUTE_TOGGLE,
        ]

        attributes = {
            Attributes.STATE: States.ON,
            Attributes.SOURCE_LIST: [
                "System Overview",
                "CPU Performance", 
                "Memory Usage",
                "Storage Activity",
                "Network Activity",
                "Temperature Overview",
                "Fan Monitoring",
                "Power Consumption"
            ],
            Attributes.SOURCE: "System Overview",
            Attributes.VOLUME: 50,
            Attributes.MUTED: False,
            Attributes.MEDIA_TITLE: "Initializing...",
            Attributes.MEDIA_ARTIST: "HTPC Monitor",
            Attributes.MEDIA_ALBUM: "Loading system data...",
            Attributes.MEDIA_IMAGE_URL: self._get_icon_base64("system_overview.png"),
        }

        super().__init__(
            identifier="htcp_monitor",
            name="HTPC System Monitor",
            features=features,
            attributes=attributes,
            cmd_handler=self._handle_command,
        )
        
        self._client = client
        self._config = config
        self._api = api
        self._current_source = "System Overview"
        self._monitoring_task = None

    def _get_icon_base64(self, icon_filename: str) -> str:
        """Get the base64 encoded icon data - same approach as weather integration."""
        if icon_filename in self._icon_cache:
            return self._icon_cache[icon_filename]

        # Get the directory where this Python file is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_dir = os.path.join(script_dir, "icons")
        icon_path = os.path.join(icon_dir, icon_filename)
        
        # Fallback icons if requested icon not found
        fallback_icons = ["system_overview.png", "cpu_monitor.png", "memory_usage.png"]

        if not os.path.exists(icon_path):
            _LOG.warning(f"Icon not found: {icon_filename}")
            for fallback in fallback_icons:
                fallback_path = os.path.join(icon_dir, fallback)
                if os.path.exists(fallback_path):
                    _LOG.info(f"Using fallback icon: {fallback}")
                    icon_path = fallback_path
                    break
            else:
                _LOG.error(f"No fallback icons found in {icon_dir}")
                return ""

        try:
            with open(icon_path, 'rb') as f:
                icon_data = f.read()
                base64_data = base64.b64encode(icon_data).decode('utf-8')
                data_url = f"data:image/png;base64,{base64_data}"
                self._icon_cache[icon_filename] = data_url
                _LOG.debug(f"Successfully loaded icon: {icon_filename}")
                return data_url
        except Exception as e:
            _LOG.error(f"Failed to read icon {icon_path}: {e}")
            return ""

    async def _handle_command(self, entity, cmd_id: str, params: dict[str, Any] | None = None) -> StatusCodes:
        """Handle media player commands."""
        _LOG.debug(f"HTCPMediaPlayer received command: {cmd_id}")
        
        if cmd_id == Commands.SELECT_SOURCE:
            if params and "source" in params:
                new_source = params["source"]
                _LOG.info(f"Switched monitoring view to: {new_source}")
                self._current_source = new_source
                
                # Update icon based on source
                icon_mapping = {
                    "System Overview": "system_overview.png",
                    "CPU Performance": "cpu_monitor.png",
                    "Memory Usage": "memory_usage.png", 
                    "Storage Activity": "storage_monitor.png",
                    "Network Activity": "network_monitor.png",
                    "Temperature Overview": "temperature_monitor.png",
                    "Fan Monitoring": "fan_monitor.png",
                    "Power Consumption": "power_consumption.png"
                }
                
                icon_file = icon_mapping.get(new_source, "system_overview.png")
                icon_url = self._get_icon_base64(icon_file)
                
                # Update attributes
                self.attributes[Attributes.SOURCE] = new_source
                self.attributes[Attributes.MEDIA_IMAGE_URL] = icon_url
                
                # Trigger immediate data update for new source
                await self._update_display_for_source(new_source)
                
                return StatusCodes.OK
                
        elif cmd_id == Commands.ON:
            self.attributes[Attributes.STATE] = States.ON
            await self._update_display_for_source(self._current_source)
            return StatusCodes.OK
            
        elif cmd_id == Commands.OFF:
            self.attributes[Attributes.STATE] = States.STANDBY
            await self._client.power_sleep()
            return StatusCodes.OK
            
        elif cmd_id == Commands.VOLUME:
            if params and "volume" in params:
                volume = max(0, min(100, params["volume"]))
                self.attributes[Attributes.VOLUME] = volume
                await self._client.set_volume(volume)
                return StatusCodes.OK
                
        elif cmd_id == Commands.MUTE_TOGGLE:
            current_muted = self.attributes.get(Attributes.MUTED, False)
            self.attributes[Attributes.MUTED] = not current_muted
            await self._client.mute_toggle()
            return StatusCodes.OK

        return StatusCodes.NOT_IMPLEMENTED

    async def _update_display_for_source(self, source: str):
        """Update display data based on selected source."""
        try:
            # Get latest system data
            if not self._client.is_connected:
                await self._client.connect()
            
            await self._client.update_system_data()
            data = self._client.system_data

            # Format display based on source
            if source == "System Overview":
                temp_str = f"{self._config.convert_temperature(data.cpu_temp):.1f}{self._config.temperature_symbol()}" if data.cpu_temp else "N/A"
                title = f"CPU: {temp_str} ({data.cpu_load:.1f}%)" if data.cpu_load else f"CPU: {temp_str}"
                artist = f"Memory: {data.memory_used:.1f}/{data.memory_total:.1f} GB" if data.memory_used and data.memory_total else "Memory: N/A"
                album = f"Power: {data.cpu_power:.1f}W" if data.cpu_power else "HTPC System Monitor"
                
            elif source == "CPU Performance":
                temp_str = f"{self._config.convert_temperature(data.cpu_temp):.1f}{self._config.temperature_symbol()}" if data.cpu_temp else "N/A"
                title = f"Temperature: {temp_str}"
                artist = f"Load: {data.cpu_load:.1f}%" if data.cpu_load else "Load: N/A"
                album = f"Clock: {data.cpu_clock:.0f} MHz" if data.cpu_clock else "Clock: N/A"
                
            elif source == "Memory Usage":
                if data.memory_used and data.memory_total:
                    usage_percent = (data.memory_used / data.memory_total) * 100
                    title = f"Used: {data.memory_used:.1f} GB"
                    artist = f"Total: {data.memory_total:.1f} GB"
                    album = f"Usage: {usage_percent:.1f}%"
                else:
                    title = "Used: N/A"
                    artist = "Total: N/A" 
                    album = "Usage: N/A"
                
            elif source == "Storage Activity":
                if data.storage_used_percent:
                    title = f"Usage: {data.storage_used_percent:.1f}%"
                    artist = f"Used: {data.storage_used:.1f} GB" if data.storage_used else "Used: N/A"
                    album = f"Total: {data.storage_total:.1f} GB" if data.storage_total else f"Device: {data.detected_storage_name}"
                else:
                    title = "Storage: N/A"
                    artist = f"Device: {data.detected_storage_name}"
                    album = "No storage data available"
                
            elif source == "Network Activity":
                if data.network_up is not None and data.network_down is not None:
                    title = f"↓ {data.network_down:.1f} Mbps"
                    artist = f"↑ {data.network_up:.1f} Mbps" 
                    album = f"Interface: {data.detected_network_name}"
                else:
                    title = "Network: N/A"
                    artist = f"Interface: {data.detected_network_name}"
                    album = "No network activity"
                
            elif source == "Temperature Overview":
                cpu_temp = f"{self._config.convert_temperature(data.cpu_temp):.1f}{self._config.temperature_symbol()}" if data.cpu_temp else "N/A"
                gpu_temp = f"{self._config.convert_temperature(data.gpu_temp):.1f}{self._config.temperature_symbol()}" if data.gpu_temp else "N/A"
                mb_temp = f"{self._config.convert_temperature(data.motherboard_temp_avg):.1f}{self._config.temperature_symbol()}" if data.motherboard_temp_avg else "N/A"
                title = f"CPU: {cpu_temp}"
                artist = f"GPU: {gpu_temp}" if data.has_dedicated_gpu else f"Motherboard: {mb_temp}"
                album = f"System Average: {mb_temp}" if data.motherboard_temp_avg else "Temperature Monitoring"
                
            elif source == "Fan Monitoring":
                if data.fan_speeds:
                    avg_speed = sum(data.fan_speeds) / len(data.fan_speeds)
                    max_speed = max(data.fan_speeds)
                    title = f"Average: {avg_speed:.0f} RPM"
                    artist = f"Max: {max_speed:.0f} RPM"
                    album = f"Fans detected: {len(data.fan_speeds)}"
                else:
                    title = "Fan data: N/A"
                    artist = "No fan sensors detected"
                    album = "Fan Monitoring"
                
            elif source == "Power Consumption":
                title = f"CPU: {data.cpu_power:.1f}W" if data.cpu_power else "CPU: N/A"
                artist = f"Processor: {data.detected_cpu_name}"
                album = "Real-time Power Draw"
                
            else:
                title = "Unknown Source"
                artist = "HTPC Monitor"
                album = "No data available"

            # Update attributes
            self.attributes[Attributes.MEDIA_TITLE] = title
            self.attributes[Attributes.MEDIA_ARTIST] = artist
            self.attributes[Attributes.MEDIA_ALBUM] = album

            # Notify the API of attribute changes
            if self._api and self._api.configured_entities.contains(self.id):
                self._api.configured_entities.update_attributes(
                    self.id, {
                        Attributes.MEDIA_TITLE: title,
                        Attributes.MEDIA_ARTIST: artist,
                        Attributes.MEDIA_ALBUM: album,
                        Attributes.SOURCE: self._current_source,
                        Attributes.MEDIA_IMAGE_URL: self.attributes[Attributes.MEDIA_IMAGE_URL]
                    }
                )
                _LOG.debug(f"Pushed display update for source: {source}")

        except Exception as e:
            _LOG.error(f"Failed to update display for {source}: {e}")

    async def run_monitoring(self):
        """Run continuous monitoring loop."""
        _LOG.info("Starting HTCP monitoring loop")
        while True:
            try:
                if self._client.is_connected:
                    await self._update_display_for_source(self._current_source)
                    await asyncio.sleep(5)  # Update every 5 seconds
                else:
                    _LOG.warning("Client not connected, attempting reconnection...")
                    if await self._client.connect():
                        _LOG.info("Reconnected to LibreHardwareMonitor")
                    else:
                        await asyncio.sleep(10)  # Wait longer if connection failed
            except asyncio.CancelledError:
                _LOG.info("Monitoring loop cancelled")
                break
            except Exception as e:
                _LOG.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)

    async def push_update(self):
        """Push the current state of the media player entity."""
        if self._api.configured_entities.contains(self.id):
            await self._update_display_for_source(self._current_source)