"""
HTPC System Monitor Integration Driver.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import asyncio
import logging

import ucapi
from ucapi import AbortDriverSetup, DeviceStates, SetupAction, SetupComplete, SetupError
from ucapi.api_definitions import Events

from uc_intg_htpc.media_player import HTCPMediaPlayer
from uc_intg_htpc.remote import HTCPRemote
from uc_intg_htpc.client import HTCPClient
from uc_intg_htpc.config import HTCPConfig
from uc_intg_htpc.setup import HTCPSetup

_LOG = logging.getLogger(__name__)

# Global integration components
api: ucapi.IntegrationAPI | None = None
_config: HTCPConfig | None = None
_client: HTCPClient | None = None
_media_player: HTCPMediaPlayer | None = None
_remote: HTCPRemote | None = None
_setup_manager: HTCPSetup | None = None
_monitoring_task: asyncio.Task | None = None


async def setup_handler(msg: SetupAction) -> SetupAction:
    """Handle integration setup flow and create entities."""
    global _config, _client, _media_player, _remote, _setup_manager
    
    if not _config:
        _config = HTCPConfig()
    if _setup_manager is None:
        _setup_manager = HTCPSetup(_config, api)
    
    action = await _setup_manager.handle_setup(msg)
    
    if isinstance(action, (SetupComplete, AbortDriverSetup, SetupError)):
        _setup_manager = None
        
    if isinstance(action, SetupComplete):
        _LOG.info("Setup confirmed. Initializing integration components...")
        await _initialize_entities()
    
    return action


async def _initialize_entities():
    """Initialize entities after successful setup or connection."""
    global _config, _client, _media_player, _remote, api
    
    if not _config.host:
        _LOG.info("HTCP not configured, skipping entity initialization")
        return
        
    _LOG.info("Initializing HTCP entities...")
    
    try:
        _client = HTCPClient(_config)
        
        _media_player = HTCPMediaPlayer(_client, _config, api)
        _remote = HTCPRemote(_client, _config, api)
        
        # Clear existing entities and add new ones
        api.available_entities.clear()
        api.available_entities.add(_media_player)
        api.available_entities.add(_remote)
        
        _LOG.info("HTPC entities are created and available.")
        
    except Exception as e:
        _LOG.error("Failed to initialize entities: %s", e)


async def start_monitoring_loop():
    """Start the monitoring task if not already running."""
    global _monitoring_task
    if _monitoring_task is None or _monitoring_task.done():
        if _client and _client.is_connected:
            _monitoring_task = asyncio.create_task(_media_player.run_monitoring())
            _LOG.info("HTCP monitoring task started.")


async def on_connect() -> None:
    """Handle Remote Two connection with reboot survival."""
    global _config
    
    _LOG.info("Remote Two connected. Setting device state to CONNECTED.")
    
    # CRITICAL FIX: Reload configuration from disk for reboot survival
    if not _config:
        _config = HTCPConfig()
    _config.load()  # This was missing!
    
    # Check if entities exist, recreate if missing
    if _config.host and (not api.available_entities or len(list(api.available_entities)) == 0):
        _LOG.info("Configuration found but entities missing, reinitializing...")
        await _initialize_entities()
    
    await api.set_device_state(DeviceStates.CONNECTED)
    
    # Try to connect to HTCP if not already connected
    if _client and not _client.is_connected:
        if await _client.connect():
            _LOG.info("Successfully connected to LibreHardwareMonitor.")
        else:
            _LOG.error("Failed to connect to LibreHardwareMonitor on reconnect.")
            await api.set_device_state(DeviceStates.ERROR)


async def on_subscribe_entities(entity_ids: list[str]):
    """Handle entity subscriptions and start monitoring."""
    _LOG.info(f"Entities subscribed: {entity_ids}. Pushing initial state.")
    
    for entity_id in entity_ids:
        if _media_player and entity_id == _media_player.id:
            await _media_player.push_update()
            await start_monitoring_loop()
        if _remote and entity_id == _remote.id:
            await _remote.push_update()


async def on_disconnect() -> None:
    """Handle Remote Two disconnection."""
    global _monitoring_task
    _LOG.info("Remote Two disconnected. Setting device state to DISCONNECTED.")
    await api.set_device_state(DeviceStates.DISCONNECTED)
    
    if _monitoring_task:
        _monitoring_task.cancel()
        _monitoring_task = None
        
    if _client and _client.is_connected:
        await _client.disconnect()


async def main():
    """Main integration entry point."""
    global api
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    _LOG.info(f"Starting HTPC Integration Driver v{ucapi.__version__}")
    
    try:
        loop = asyncio.get_running_loop()
        api = ucapi.IntegrationAPI(loop)
        
        api.add_listener(Events.CONNECT, on_connect)
        api.add_listener(Events.DISCONNECT, on_disconnect)
        api.add_listener(Events.SUBSCRIBE_ENTITIES, on_subscribe_entities)
        
        await api.init("driver.json", setup_handler)
        await api.set_device_state(DeviceStates.DISCONNECTED)
        
        _LOG.info("Driver initialized. Waiting for remote connection and setup.")
        await asyncio.Future()
        
    except asyncio.CancelledError:
        _LOG.info("Driver task cancelled.")
    finally:
        if _monitoring_task:
            _monitoring_task.cancel()
        if _client:
            await _client.disconnect()
        _LOG.info("HTPC Integration Driver has stopped.")


if __name__ == "__main__":
    asyncio.run(main())