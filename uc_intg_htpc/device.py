"""
HTPC device implementation using PollingDevice.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import base64
import logging
import os
from typing import Any

from ucapi_framework import PollingDevice

from uc_intg_htpc.client import HTCPClient, SystemData, is_reachable
from uc_intg_htpc.config import HTCPConfig
from uc_intg_htpc.const import AGENT_PORT, POLL_INTERVAL, STATE_OFF, STATE_ON

_LOG = logging.getLogger(__name__)

_CLOSE_TIMEOUT = 3


class HTCPDevice(PollingDevice):
    """HTPC system monitor device using polling for data refresh."""

    def __init__(self, device_config: HTCPConfig, **kwargs: Any) -> None:
        super().__init__(device_config, poll_interval=POLL_INTERVAL, **kwargs)
        self._config = device_config
        self._client: HTCPClient | None = None
        self._connect_lock: asyncio.Lock = asyncio.Lock()
        self._state: str = STATE_OFF
        self._system_data = SystemData()
        self._current_view: str = "System Overview"
        self._icon_cache: dict[str, str] = {}

    @property
    def _probe_port(self) -> int:
        return self._config.port if self._config.enable_hardware_monitoring else AGENT_PORT

    @property
    def identifier(self) -> str:
        return self._config.identifier

    @property
    def name(self) -> str:
        return self._config.name

    @property
    def address(self) -> str:
        return self._config.host

    @property
    def log_id(self) -> str:
        return f"[{self.name}]"

    @property
    def state(self) -> str:
        return self._state

    @property
    def config(self) -> HTCPConfig:
        return self._config

    @property
    def system_data(self) -> SystemData:
        return self._system_data

    @property
    def current_view(self) -> str:
        return self._current_view

    def set_current_view(self, view: str) -> None:
        self._current_view = view

    def get_icon_base64(self, icon_filename: str) -> str:
        if icon_filename in self._icon_cache:
            return self._icon_cache[icon_filename]

        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", icon_filename)

        if not os.path.exists(icon_path):
            fallback = os.path.join(script_dir, "icons", "system_overview.png")
            if os.path.exists(fallback):
                icon_path = fallback
            else:
                return ""

        try:
            with open(icon_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("utf-8")
                result = f"data:image/png;base64,{data}"
                self._icon_cache[icon_filename] = result
                return result
        except Exception:
            return ""

    async def connect(self) -> bool:
        async with self._connect_lock:
            return await super().connect()

    async def establish_connection(self) -> HTCPClient:
        if self._client is None:
            self._client = HTCPClient(self._config)
        await self._refresh_state()
        return self._client

    async def poll_device(self) -> None:
        await self._refresh_state()

    async def _refresh_state(self) -> None:
        if self._client is None:
            self._state = STATE_OFF
            self.push_update()
            return

        if await is_reachable(self._config.host, self._probe_port):
            self._client.ensure_session()
            if self._config.enable_hardware_monitoring and await self._client.update_system_data():
                self._system_data = self._client.system_data
            self._state = STATE_ON
        else:
            self._state = STATE_OFF
        self.push_update()

    async def send_command(self, command: str) -> bool:
        if self._client is None:
            self._client = HTCPClient(self._config)
        self._client.ensure_session()
        return await self._client.send_command(command)

    async def power_on_wol(self) -> bool:
        client = self._client or HTCPClient(self._config)
        return await client.power_on_wol()

    async def disconnect(self) -> None:
        async with self._connect_lock:
            if self._client is not None:
                try:
                    await asyncio.wait_for(self._client.close(), timeout=_CLOSE_TIMEOUT)
                except Exception:
                    pass
                self._client = None
            self._state = STATE_OFF
            await super().disconnect()
