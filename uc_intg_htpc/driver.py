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

api: ucapi.IntegrationAPI | None = None
_config: HTCPConfig | None = None
_client: HTCPClient | None = None
_media_player: HTCPMediaPlayer | None = None
_remote: HTCPRemote | None = None
_setup_manager: HTCPSetup | None = None
_monitoring_task: asyncio.Task | None = None
_entities_ready: bool = False
_initialization_lock: asyncio.Lock = asyncio.Lock()


async def setup_handler(msg: SetupAction) -> SetupAction:
    global _config, _client, _media_player, _remote, _setup_manager, _entities_ready
    
    if not _config:
        _config = HTCPConfig()
    if _setup_manager is None:
        _setup_manager = HTCPSetup(_config, api)
    
    action = await _setup_manager.handle_setup(msg)
    
    if isinstance(action, (SetupComplete, AbortDriverSetup, SetupError)):
        _setup_manager = None
        
    if isinstance(action, SetupComplete):
        _LOG.info("Setup confirmed. Reloading configuration and initializing entities...")
        
        _config._load_config()
        _LOG.debug("Config reloaded - enable_hardware_monitoring: %s", _config.enable_hardware_monitoring)
        
        _entities_ready = False
        _LOG.info("Reset entities_ready flag for reconfiguration")
        
        await _initialize_entities()
    
    return action


async def _initialize_entities():
    global _config, _client, _media_player, _remote, api, _entities_ready
    
    async with _initialization_lock:
        if _entities_ready:
            _LOG.debug("Entities already initialized, skipping")
            return
            
        if not _config or not _config.host:
            _LOG.info("HTCP not configured, skipping entity initialization")
            return
        
        _LOG.info("Initializing HTCP entities...")
        _LOG.debug("Config loaded - enable_hardware_monitoring: %s", _config.enable_hardware_monitoring)
        
        try:
            _client = HTCPClient(_config)
            _LOG.info("HTPC Client created")
            
            _media_player = None
            _remote = None
            
            if _config.enable_hardware_monitoring:
                _LOG.info("Hardware monitoring is ENABLED - creating media player entity")
                _media_player = HTCPMediaPlayer(_client, _config, api)
                _LOG.info("Media player entity created: %s", _media_player.id)
            else:
                _LOG.info("Hardware monitoring is DISABLED - skipping media player entity")
            
            _remote = HTCPRemote(_client, _config, api)
            _LOG.info("Remote entity created: %s", _remote.id)
            
            api.available_entities.clear()
            _LOG.info("Cleared existing available entities")
            
            if _media_player:
                api.available_entities.add(_media_player)
                _LOG.info("Added media player to available entities")
            else:
                _LOG.info("Media player not created - not added to available entities")
            
            api.available_entities.add(_remote)
            _LOG.info("Added remote to available entities")
            
            _entities_ready = True
            
            _LOG.info("HTPC entities initialized successfully")
            _LOG.info("Media player created: %s", _media_player is not None)
            _LOG.info("Remote created: %s", _remote is not None)
            
        except Exception as e:
            _LOG.error("Failed to initialize entities: %s", e, exc_info=True)
            _entities_ready = False
            raise


async def start_monitoring_loop():
    global _monitoring_task
    if _media_player is None:
        _LOG.info("Media player not available - monitoring disabled")
        return
        
    if _monitoring_task is None or _monitoring_task.done():
        if _client and _client.is_connected:
            _monitoring_task = asyncio.create_task(_media_player.run_monitoring())
            _LOG.info("HTCP monitoring task started.")


async def on_connect() -> None:
    global _config, _entities_ready
    
    _LOG.info("Remote connected. Checking configuration state...")
    
    if not _config:
        _config = HTCPConfig()
    
    _config._load_config()
    _LOG.debug("Config reloaded - enable_hardware_monitoring: %s", _config.enable_hardware_monitoring)
    
    if _config.host and not _entities_ready:
        _LOG.info("Configuration found but entities missing, reinitializing...")
        try:
            await _initialize_entities()
        except Exception as e:
            _LOG.error("Failed to reinitialize entities: %s", e)
            await api.set_device_state(DeviceStates.ERROR)
            return
    
    if _config.host and _entities_ready:
        if _config.enable_hardware_monitoring and _client:
            if not _client.is_connected:
                if await _client.connect():
                    _LOG.info("Successfully connected to LibreHardwareMonitor.")
                    await api.set_device_state(DeviceStates.CONNECTED)
                else:
                    _LOG.error("Failed to connect to LibreHardwareMonitor.")
                    await api.set_device_state(DeviceStates.ERROR)
            else:
                await api.set_device_state(DeviceStates.CONNECTED)
        else:
            _LOG.info("Hardware monitoring disabled - remote control only mode.")
            await api.set_device_state(DeviceStates.CONNECTED)
    elif not _config.host:
        _LOG.info("No configuration found, awaiting setup")
        await api.set_device_state(DeviceStates.DISCONNECTED)
    else:
        _LOG.error("Entities not ready despite configuration")
        await api.set_device_state(DeviceStates.ERROR)


async def on_subscribe_entities(entity_ids: list[str]):
    _LOG.info(f"Entities subscription requested: {entity_ids}")
    
    if not _entities_ready:
        _LOG.error("RACE CONDITION: Subscription before entities ready! Attempting recovery...")
        if _config and _config.host:
            await _initialize_entities()
        else:
            _LOG.error("Cannot recover - no configuration available")
            return
    
    _LOG.info(f"Media player available: {_media_player is not None}")
    _LOG.info(f"Remote available: {_remote is not None}")
    
    for entity_id in entity_ids:
        if _media_player and entity_id == _media_player.id:
            _LOG.info("Subscribing to media player entity")
            await _media_player.push_update()
            await start_monitoring_loop()
        if _remote and entity_id == _remote.id:
            _LOG.info("Subscribing to remote entity")
            await _remote.push_update()


async def on_disconnect() -> None:
    global _monitoring_task
    _LOG.info("Remote disconnected. Setting device state to DISCONNECTED.")
    await api.set_device_state(DeviceStates.DISCONNECTED)
    
    if _monitoring_task:
        _monitoring_task.cancel()
        _monitoring_task = None
        
    if _client and _client.is_connected:
        await _client.disconnect()


async def main():
    global api, _config
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    _LOG.info(f"Starting HTPC Integration Driver v{ucapi.__version__}")
    
    try:
        loop = asyncio.get_running_loop()
        api = ucapi.IntegrationAPI(loop)
        
        _config = HTCPConfig()
        if _config.host:
            _LOG.info("Found existing configuration, pre-initializing entities for reboot survival")
            _LOG.debug("Existing config - enable_hardware_monitoring: %s", _config.enable_hardware_monitoring)
            loop.create_task(_initialize_entities())
        
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