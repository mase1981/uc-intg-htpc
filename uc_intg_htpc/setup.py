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
    """Setup flow handler for HTCP integration."""

    def __init__(self, config: HTCPConfig, api):
        """
        Initialize setup handler.
        
        :param config: configuration instance
        :param api: IntegrationAPI instance
        """
        self._config = config
        self._api = api

    async def handle_setup(self, msg_data: Any) -> SetupAction:
        """
        Handle setup request.
        
        :param msg_data: setup message data
        :return: setup action response
        """
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
        """Handle initial driver setup request."""
        _LOG.info("Starting HTCP integration setup (reconfigure: %s)", request.reconfigure)
        
        host = request.setup_data.get("host", "192.168.1.100")
        port = 8085
        enable_hardware_monitoring = request.setup_data.get("enable_hardware_monitoring", True)
        
        # ALWAYS test Windows Agent (required for remote control)
        agent_status = await self._test_agent_connection(host)
        if not agent_status:
            _LOG.error("Windows Agent connection failed - Agent is required!")
            return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
        
        _LOG.info("Windows Agent connection successful.")
        
        # Conditionally test LibreHardwareMonitor only if enabled
        hardware_result = {"success": True, "sensor_count": 0}
        if enable_hardware_monitoring:
            hardware_result = await self._test_connection(host, port)
            
            if not hardware_result["success"]:
                error_msg = hardware_result.get("error", "Unknown connection error.")
                _LOG.error("LibreHardwareMonitor connection test failed: %s", error_msg)
                if "refused" in error_msg.lower():
                    return SetupError(IntegrationSetupError.CONNECTION_REFUSED)
                elif "timeout" in error_msg.lower():
                    return SetupError(IntegrationSetupError.TIMEOUT)
                elif "not found" in error_msg.lower():
                    return SetupError(IntegrationSetupError.NOT_FOUND)
                return SetupError(IntegrationSetupError.OTHER)
            
            _LOG.info("LibreHardwareMonitor connection test successful.")
        else:
            _LOG.info("Hardware monitoring disabled - skipping LibreHardwareMonitor test.")
        
        self._temp_config = {
            "host": host,
            "port": port,
            "temperature_unit": request.setup_data.get("temperature_unit", "celsius"),
            "enable_hardware_monitoring": enable_hardware_monitoring
        }
        
        summary_text = self._generate_setup_summary(self._temp_config, hardware_result, agent_status)
        
        return RequestUserConfirmation(
            title={"en": "Confirm HTCP Setup"},
            header={"en": "Connection Successful!"},
            footer={"en": summary_text}
        )

    async def _handle_user_confirmation_response(self, response: UserConfirmationResponse) -> SetupAction:
        """Handle user confirmation."""
        if response.confirm:
            _LOG.info("User confirmed setup. Saving configuration.")
            
            self._config.update_config(self._temp_config)
            if not self._config.save_config():
                _LOG.error("Failed to save configuration.")
                return SetupError(IntegrationSetupError.OTHER)
            
            return SetupComplete()
        else:
            _LOG.info("User cancelled setup.")
            return AbortDriverSetup(IntegrationSetupError.OTHER)

    async def _test_connection(self, host: str, port: int) -> Dict[str, Any]:
        """Test connection to LibreHardwareMonitor."""
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

    async def _test_agent_connection(self, host: str) -> bool:
        """Test connection to Windows agent - REQUIRED."""
        try:
            agent_url = f"http://{host}:8086/health"
            timeout = aiohttp.ClientTimeout(total=5)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(agent_url) as response:
                    return response.status == 200
        except:
            return False

    def _count_sensors(self, data: Dict[str, Any]) -> int:
        """Recursively count sensors in LibreHardwareMonitor data."""
        count = 0
        if isinstance(data, dict):
            if "Value" in data and data.get("Value", "").strip():
                count += 1
            for child in data.get("Children", []):
                count += self._count_sensors(child)
        return count

    def _generate_setup_summary(self, config: Dict[str, Any], hardware_result: Dict[str, Any], agent_status: bool) -> str:
        """Generate a user-friendly setup summary."""
        temp_unit = "Celsius" if config.get('temperature_unit') == "celsius" else "Fahrenheit"
        agent_text = "✅ Connected" if agent_status else "❌ Not detected (REQUIRED)"
        
        hardware_monitoring_enabled = config.get('enable_hardware_monitoring', True)
        
        if hardware_monitoring_enabled:
            hardware_text = f"✅ Enabled ({hardware_result.get('sensor_count', 'N/A')} sensors)"
        else:
            hardware_text = "⚠️ Disabled (Remote control only)"
        
        return (
            f"🖥️ HTPC: {config['host']}:{config['port']}\n"
            f"🎮 Windows Agent: {agent_text}\n"
            f"📊 Hardware Monitoring: {hardware_text}\n"
            f"🌡️ Temperature Unit: {temp_unit}\n\n"
            "✅ Ready to create entities!\n\n"
            "📝 Entities to be created:\n"
            f"{'  • HTPC System Monitor (Media Player)\n' if hardware_monitoring_enabled else ''}"
            "  • HTPC Advanced Remote (Remote)\n\n"
            "🔧 Custom Apps:\n"
            "Use 'Send Command' in the Remote\n"
            "to launch apps with:\n"
            "launch_exe:\"C:\\\\Path\\\\To\\\\App.exe\""
        )