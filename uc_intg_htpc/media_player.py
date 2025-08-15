"""
HTPC Media Player entity implementation.

:copyright: (c) 2024 by Your Name.
:license: MPL-2.0, see LICENSE for more details.
"""

import logging
import os
import base64
from typing import Any

from ucapi.api_definitions import StatusCodes
from ucapi.media_player import Attributes, Commands, Features, MediaPlayer, States

_LOG = logging.getLogger(__name__)


class HTCPMediaPlayer(MediaPlayer):
    """HTPC system monitor as media player entity."""

    def __init__(self, client, api):
        """Initialize HTCP media player."""
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
            identifier="htpc_monitor",
            name="HTPC System Monitor",
            features=features,
            attributes=attributes,
            cmd_handler=self._handle_command,
        )
        
        self._client = client
        self._api = api
        self._current_source = "System Overview"
        self._icon_cache = {}

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
            return StatusCodes.OK
            
        elif cmd_id == Commands.VOLUME:
            if params and "volume" in params:
                volume = max(0, min(100, params["volume"]))
                self.attributes[Attributes.VOLUME] = volume
                # Could control system volume here via client
                return StatusCodes.OK
                
        elif cmd_id == Commands.MUTE_TOGGLE:
            current_muted = self.attributes.get(Attributes.MUTED, False)
            self.attributes[Attributes.MUTED] = not current_muted
            # Could control system mute here via client
            return StatusCodes.OK

        return StatusCodes.NOT_IMPLEMENTED

    async def _update_display_for_source(self, source: str):
        """Update display data based on selected source."""
        try:
            # Get latest system data
            data = await self._client.get_system_data()
            if not data:
                return

            # Format display based on source
            if source == "System Overview":
                title = f"CPU: {data.get('cpu_temp', 'N/A')}°C ({data.get('cpu_load', 'N/A')}%)"
                artist = f"Power: {data.get('cpu_power', 'N/A')}W"
                album = f"{data.get('memory_used', 'N/A')}/{data.get('memory_total', 'N/A')} GB ({data.get('memory_percent', 'N/A')}%)"
                
            elif source == "CPU Performance":
                title = f"Temperature: {data.get('cpu_temp', 'N/A')}°C"
                artist = f"Load: {data.get('cpu_load', 'N/A')}%"
                album = f"Clock: {data.get('cpu_clock', 'N/A')} MHz"
                
            elif source == "Memory Usage":
                title = f"Used: {data.get('memory_used', 'N/A')} GB"
                artist = f"Total: {data.get('memory_total', 'N/A')} GB"
                album = f"Usage: {data.get('memory_percent', 'N/A')}%"
                
            elif source == "Storage Activity":
                title = f"Used: {data.get('storage_used', 'N/A')} GB"
                artist = f"Total: {data.get('storage_total', 'N/A')} GB"
                album = f"Usage: {data.get('storage_percent', 'N/A')}%"
                
            elif source == "Network Activity":
                title = f"Down: {data.get('network_download', 'N/A')} MB/s"
                artist = f"Up: {data.get('network_upload', 'N/A')} MB/s"
                album = "Real-time Network Usage"
                
            elif source == "Temperature Overview":
                title = f"CPU: {data.get('cpu_temp', 'N/A')}°C"
                artist = f"GPU: {data.get('gpu_temp', 'N/A')}°C"
                album = f"System: {data.get('system_temp', 'N/A')}°C"
                
            elif source == "Fan Monitoring":
                title = f"CPU Fan: {data.get('cpu_fan', 'N/A')} RPM"
                artist = f"System Fan: {data.get('system_fan', 'N/A')} RPM"
                album = "Fan Speed Monitoring"
                
            elif source == "Power Consumption":
                title = f"CPU Package: {data.get('cpu_power', 'N/A')}W"
                artist = "Real-time Power Draw"
                album = "LibreHardwareMonitor"
                
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
                        Attributes.MEDIA_IMAGE_URL: self.attributes[Attributes.MEDIA_IMAGE_URL]
                    }
                )
                _LOG.debug(f"Pushed display update for source: {source}")

        except Exception as e:
            _LOG.error(f"Failed to update display for {source}: {e}")

    async def update_data(self):
        """Update data for current source."""
        await self._update_display_for_source(self._current_source)