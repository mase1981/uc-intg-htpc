"""
Setup flow for HTPC System Monitor Integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import ssl
from typing import Any, Dict

import aiohttp
import certifi
from ucapi import (
    AbortDriverSetup,
    DriverSetupRequest,
    IntegrationSetupError,
    RequestUserConfirmation,
    SetupAction,
    SetupComplete,
    SetupError,
    UserConfirmationResponse,
)

from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)


class HTCPSetup:

    def __init__(self, config: HTCPConfig, api):
        self._config = config
        self._api = api

    async def handle_setup(self, msg_data: Any) -> SetupAction:
        try:
            if isinstance(msg_data, DriverSetupRequest):
                return await self._handle_driver_setup_request(msg_data)
            elif isinstance(msg_data, UserConfirmationResponse):
                return await self._handle_user_confirmation_response(msg_data)
            elif isinstance(msg_data, AbortDriverSetup):
                _LOG.info("Setup aborted by user or system.")
                return SetupError(msg_data.error)
            else:
                _LOG.error("Unknown setup message type: %s", type(msg_data))
                return SetupError(IntegrationSetupError.OTHER)
                
        except Exception as ex:
            _LOG.error("An unexpected error occurred during setup: %s", ex, exc_info=True)
            return SetupError(IntegrationSetupError.OTHER)

    async def _handle_driver_setup_request(self, request: DriverSetupRequest) -> SetupAction:
        _LOG.info("Starting HTCP integration setup (reconfigure: %s)", request.reconfigure)
        _LOG.debug("Received setup_data: %s", request.setup_data)
        
        host = request.setup_data.get("host", "192.168.1.100")
        port = 8085
        
        enable_hardware_monitoring_raw = request.setup_data.get("enable_hardware_monitoring", "enabled")
        _LOG.debug("Raw enable_hardware_monitoring value: %s (type: %s)", enable_hardware_monitoring_raw, type(enable_hardware_monitoring_raw))
        
        enable_hardware_monitoring = enable_hardware_monitoring_raw == "enabled"
        _LOG.info("Hardware monitoring set to: %s (from value: '%s')", enable_hardware_monitoring, enable_hardware_monitoring_raw)
        
        connection_result = {"success": True, "sensor_count": 0}
        
        if enable_hardware_monitoring:
            _LOG.info("Hardware monitoring ENABLED - testing LibreHardwareMonitor connection")
            connection_result = await self._test_connection(host, port)
            
            if not connection_result["success"]:
                error_msg = connection_result.get("error", "Unknown connection error.")
                _LOG.error("Connection test to HTCP failed: %s", error_msg)
                if "refused" in error_msg.lower():
                    return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
                elif "timeout" in error_msg.lower():
                    return SetupError(IntegrationSetupError.TIMEOUT)
                elif "not found" in error_msg.lower():
                    return SetupError(IntegrationSetupError.NOT_FOUND)
                return SetupError(IntegrationSetupError.OTHER)
            
            _LOG.info("HTCP connection test successful.")
        else:
            _LOG.info("Hardware monitoring DISABLED - skipping LibreHardwareMonitor connection test")
        
        mac_address = request.setup_data.get("mac_address", "").strip()
        
        self._temp_config = {
            "host": host,
            "port": port,
            "enable_hardware_monitoring": enable_hardware_monitoring,
            "temperature_unit": request.setup_data.get("temperature_unit", "celsius"),
            "mac_address": mac_address
        }
        
        _LOG.debug("Temp config created: %s", self._temp_config)
        
        agent_status = await self._test_agent_connection()
        summary_text = self._generate_setup_summary(self._temp_config, connection_result, agent_status)
        
        return RequestUserConfirmation(
            title={"en": "Confirm HTCP Setup"},
            header={"en": "Connection Successful!"},
            footer={"en": summary_text}
        )

    async def _handle_user_confirmation_response(self, response: UserConfirmationResponse) -> SetupAction:
        if response.confirm:
            _LOG.info("User confirmed setup. Saving configuration.")
            _LOG.debug("Configuration to save: %s", self._temp_config)
            
            self._config.update_config(self._temp_config)
            if not self._config.save_config():
                _LOG.error("Failed to save configuration.")
                return SetupError(IntegrationSetupError.OTHER)
            
            _LOG.info("Configuration saved successfully with enable_hardware_monitoring=%s", self._temp_config.get("enable_hardware_monitoring"))
            return SetupComplete()
        else:
            _LOG.info("User cancelled setup.")
            return AbortDriverSetup(IntegrationSetupError.OTHER)

    async def _test_connection(self, host: str, port: int) -> Dict[str, Any]:
        url = f"http://{host}:{port}/data.json"
        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout, connector=aiohttp.TCPConnector(ssl=ssl_context)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        sensor_count = self._count_sensors(data)
                        return {"success": True, "sensor_count": sensor_count}
                    else:
                        return {"success": False, "error": f"HTTP Error {response.status}"}
                        
        except aiohttp.ClientConnectorError as e:
            return {"success": False, "error": f"Connection refused at {host}:{port}. Ensure LibreHardwareMonitor web server is running."}
        except asyncio.TimeoutError:
            return {"success": False, "error": f"Connection to {host}:{port} timed out."}
        except Exception as e:
            return {"success": False, "error": f"Connection error: {e}"}

    async def _test_agent_connection(self) -> bool:
        try:
            agent_url = f"http://{self._temp_config['host']}:8086/health"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(agent_url) as response:
                    return response.status == 200
        except:
            return False

    def _count_sensors(self, data: Dict[str, Any]) -> int:
        count = 0
        if isinstance(data, dict):
            if "Value" in data and data.get("Value", "").strip():
                count += 1
            for child in data.get("Children", []):
                count += self._count_sensors(child)
        return count

    def _generate_setup_summary(self, config: Dict[str, Any], result: Dict[str, Any], agent_status: bool) -> str:
        temp_unit = "Celsius" if config.get('temperature_unit') == "celsius" else "Fahrenheit"
        agent_text = "Connected" if agent_status else "Not detected (optional)"
        wol_text = "Enabled" if config.get('mac_address') else "Disabled"
        hardware_monitoring = "Enabled" if config.get('enable_hardware_monitoring') else "Disabled"
        
        summary = f"🖥️ HTPC: {config['host']}:{config['port']}\n"
        summary += f"📊 Hardware Monitoring: {hardware_monitoring}\n"
        
        if config.get('enable_hardware_monitoring'):
            summary += f"🌡️ Temperature: {temp_unit}\n"
            summary += f"📈 Sensors: {result.get('sensor_count', 'N/A')}\n"
        
        summary += f"🎮 Windows Agent: {agent_text}\n"
        summary += f"⚡ Wake-on-LAN: {wol_text}\n\n"
        
        if not config.get('enable_hardware_monitoring'):
            summary += "⚠️ Remote control only mode\n"
        
        summary += "✅ Ready to create entities!"
        
        return summary