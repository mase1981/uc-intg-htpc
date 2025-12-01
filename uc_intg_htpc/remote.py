"""
HTCP Remote Entity - Optimized with reliable commands only.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""
import logging

from ucapi import IntegrationAPI, Remote, StatusCodes, entity
from ucapi.remote import Attributes, Commands, Features, States
from ucapi.ui import UiPage, create_ui_icon, create_ui_text, Size

from uc_intg_htpc.client import HTCPClient
from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)

COMMAND_MAP = {
    "POWER_ON": "power_on",
    "POWER_OFF": "power_shutdown",
}

class HTCPRemote(Remote): 

    def __init__(self, client: HTCPClient, config: HTCPConfig, api: IntegrationAPI):
        self._client = client
        self._config = config
        self._api = api
        
        simple_commands = [ 
            "POWER_OFF",
            "arrow_up", "arrow_down", "arrow_left", "arrow_right", "enter", "escape", 
            "back", "home", "end", "page_up", "page_down", "tab", "space", "delete", 
            "backspace",
            "play_pause", "play", "pause", "stop", "previous", "next", "fast_forward", 
            "rewind", "record", "volume_up", "volume_down", "mute",
            "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12",
            "windows_key", "alt_tab", "win_r", "win_d", "win_e", "win_i", 
            "ctrl_shift_esc",
            "custom_calc", "custom_notepad", "custom_cmd", "custom_powershell",
            "url_youtube", "url_netflix", "url_plex", "url_jellyfin",
            "power_sleep", "power_hibernate", "power_shutdown", "power_restart",
            "pair_bluetooth", "show_pairing_help"
        ]
        
        if config.wol_enabled:
            simple_commands.insert(0, "POWER_ON")
        
        nav_page = self._create_navigation_page()
        media_page = self._create_media_page()
        windows_page = self._create_windows_shortcuts_page()
        system_page = self._create_system_tools_page()
        function_page = self._create_function_keys_page()
        power_page = self._create_power_system_page()

        super().__init__(
            identifier="htpc_remote",
            name={"en": "HTPC Advanced Remote"},
            features=[Features.SEND_CMD],
            attributes={
                Attributes.STATE: States.ON
            },
            simple_commands=simple_commands,
            ui_pages=[nav_page, media_page, windows_page, system_page, function_page, power_page],
            cmd_handler=self.handle_command
        )

    def _create_navigation_page(self) -> UiPage:
        page = UiPage(page_id="navigation", name="Navigation")
        page.items.extend([
            create_ui_icon("uc:arrow-up", 1, 0, cmd="arrow_up"),
            create_ui_icon("uc:arrow-left", 0, 1, cmd="arrow_left"),
            create_ui_icon("uc:check-circle", 1, 1, cmd="enter"),
            create_ui_icon("uc:arrow-right", 2, 1, cmd="arrow_right"),
            create_ui_icon("uc:arrow-down", 1, 2, cmd="arrow_down"),
            
            create_ui_icon("uc:x-circle", 3, 1, cmd="escape"),
            create_ui_text("Back", 0, 3, cmd="back"),
            create_ui_text("Tab", 1, 3, cmd="tab"),
            create_ui_text("Space", 2, 3, cmd="space"),
            create_ui_text("Delete", 3, 3, cmd="delete"),
            
            create_ui_text("Home", 0, 4, cmd="home"),
            create_ui_text("End", 1, 4, cmd="end"),
            create_ui_text("PgUp", 2, 4, cmd="page_up"),
            create_ui_text("PgDn", 3, 4, cmd="page_down"),
        ])
        return page
        
    def _create_media_page(self) -> UiPage:
        page = UiPage(page_id="media", name="Media Controls")
        page.items.extend([
            create_ui_icon("uc:rewind", 0, 0, cmd="rewind"),
            create_ui_icon("uc:skip-back", 1, 0, cmd="previous"),
            create_ui_icon("uc:play", 2, 0, cmd="play"),
            create_ui_icon("uc:pause", 3, 0, cmd="pause"),
            
            create_ui_icon("uc:skip-forward", 0, 1, cmd="next"),
            create_ui_icon("uc:fast-forward", 1, 1, cmd="fast_forward"),
            create_ui_icon("uc:square", 2, 1, cmd="stop"),
            create_ui_icon("uc:circle", 3, 1, cmd="record"),
            
            create_ui_icon("uc:volume-1", 0, 2, cmd="volume_down"),
            create_ui_icon("uc:volume-x", 1, 2, cmd="mute"),
            create_ui_icon("uc:volume-2", 2, 2, cmd="volume_up"),
            create_ui_text("Play/Pause", 3, 2, cmd="play_pause"),
            
            create_ui_text("F11", 0, 3, cmd="f11"),
            create_ui_text("F5", 1, 3, cmd="f5"),
            create_ui_text("F9", 2, 3, cmd="f9"),
            create_ui_text("Alt+Tab", 3, 3, cmd="alt_tab"),
        ])
        return page

    def _create_windows_shortcuts_page(self) -> UiPage:
        page = UiPage(page_id="windows", name="Windows Shortcuts")
        page.items.extend([
            create_ui_icon("uc:home", 0, 0, cmd="windows_key"),
            create_ui_text("Alt+Tab", 1, 0, cmd="alt_tab"),
            create_ui_text("Run", 2, 0, cmd="win_r"),
            create_ui_text("Desktop", 3, 0, cmd="win_d"),
            
            create_ui_text("Explorer", 0, 1, cmd="win_e"),
            create_ui_text("Settings", 1, 1, cmd="win_i"),
            create_ui_text("Run Dialog", 2, 1, cmd="win_r"),
            create_ui_text("Task Mgr", 3, 1, cmd="ctrl_shift_esc"),
            
            create_ui_text("Bluetooth", 0, 2, cmd="pair_bluetooth"),
            create_ui_text("BT Help", 1, 2, cmd="show_pairing_help"),
            create_ui_text("Calculator", 2, 2, cmd="custom_calc"),
            create_ui_text("Notepad", 3, 2, cmd="custom_notepad"),
        ])
        return page

    def _create_system_tools_page(self) -> UiPage:
        page = UiPage(page_id="system_tools", name="System Tools")
        page.items.extend([
            create_ui_text("Calculator", 0, 0, cmd="custom_calc"),
            create_ui_text("Notepad", 1, 0, cmd="custom_notepad"),
            create_ui_text("Command", 2, 0, cmd="custom_cmd"),
            create_ui_text("PowerShell", 3, 0, cmd="custom_powershell"),
            
            create_ui_text("YouTube", 0, 1, cmd="url_youtube"),
            create_ui_text("Netflix", 1, 1, cmd="url_netflix"),
            create_ui_text("Plex Web", 2, 1, cmd="url_plex"),
            create_ui_text("Jellyfin", 3, 1, cmd="url_jellyfin"),
            
            create_ui_text("Task Mgr", 0, 2, cmd="ctrl_shift_esc"),
            create_ui_text("Settings", 1, 2, cmd="win_i"),
            create_ui_text("Explorer", 2, 2, cmd="win_e"),
            create_ui_text("Bluetooth", 3, 2, cmd="pair_bluetooth"),
        ])
        return page
        
    def _create_function_keys_page(self) -> UiPage:
        page = UiPage(page_id="function_keys", name="Function Keys")
        page.items.extend([
            create_ui_text("F1", 0, 0, cmd="f1"),
            create_ui_text("F2", 1, 0, cmd="f2"),
            create_ui_text("F3", 2, 0, cmd="f3"),
            create_ui_text("F4", 3, 0, cmd="f4"),
            
            create_ui_text("F5", 0, 1, cmd="f5"),
            create_ui_text("F6", 1, 1, cmd="f6"),
            create_ui_text("F7", 2, 1, cmd="f7"),
            create_ui_text("F8", 3, 1, cmd="f8"),
            
            create_ui_text("F9", 0, 2, cmd="f9"),
            create_ui_text("F10", 1, 2, cmd="f10"),
            create_ui_text("F11", 2, 2, cmd="f11"),
            create_ui_text("F12", 3, 2, cmd="f12"),
            
            create_ui_text("Task Mgr", 0, 3, cmd="ctrl_shift_esc"),
            create_ui_text("Lock", 1, 3, cmd="win_l"),
            create_ui_text("Settings", 2, 3, cmd="win_i"),
            create_ui_text("Explorer", 3, 3, cmd="win_e"),
        ])
        return page
        
    def _create_power_system_page(self) -> UiPage:
        page = UiPage(page_id="power", name="Power & System")
        
        items = []
        
        if self._config.wol_enabled:
            items.extend([
                create_ui_text("PowerOn", 0, 0, cmd="power_on"),
                create_ui_text("Sleep", 1, 0, cmd="power_sleep"),
                create_ui_text("Hibernate", 2, 0, cmd="power_hibernate"),
                create_ui_text("PowerOff", 3, 0, cmd="power_shutdown"),
            ])
        else:
            items.extend([
                create_ui_text("Sleep", 0, 0, cmd="power_sleep"),
                create_ui_text("Hibernate", 1, 0, cmd="power_hibernate"),
                create_ui_text("PowerOff", 2, 0, cmd="power_shutdown"),
                create_ui_text("Restart", 3, 0, cmd="power_restart"),
            ])
        
        items.extend([
            create_ui_text("Settings", 0, 1, cmd="win_i"),
            create_ui_text("Task Mgr", 1, 1, cmd="ctrl_shift_esc"),
            create_ui_text("Run Dialog", 2, 1, cmd="win_r"),
            create_ui_text("Desktop", 3, 1, cmd="win_d"),
        ])
        
        page.items.extend(items)
        return page

    async def handle_command(self, entity_arg: entity.Entity, cmd_id: str, params: dict | None) -> StatusCodes:
        _LOG.info(f"HTCPRemote received command: {cmd_id} with params: {params}")
        
        if cmd_id == Commands.SEND_CMD:
            command = params.get("command") if params else None
            if command:
                if command in COMMAND_MAP:
                    actual_command = COMMAND_MAP[command]
                    success = await self._execute_command(actual_command)
                else:
                    success = await self._execute_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
        
        elif cmd_id == Commands.SEND_CMD_SEQUENCE:
            if params and "sequence" in params:
                sequence = params["sequence"]
                _LOG.info(f"Executing command sequence: {sequence}")
                for command in sequence:
                    if command in COMMAND_MAP:
                        actual_command = COMMAND_MAP[command]
                        success = await self._execute_command(actual_command)
                    else:
                        success = await self._execute_command(command)
                    if not success:
                        return StatusCodes.SERVER_ERROR
                return StatusCodes.OK
            elif params and "command" in params:
                command = params["command"]
                if command in COMMAND_MAP:
                    actual_command = COMMAND_MAP[command]
                    success = await self._execute_command(actual_command)
                else:
                    success = await self._execute_command(command)
                return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
        
        else:
            success = await self._execute_command(cmd_id)
            return StatusCodes.OK if success else StatusCodes.SERVER_ERROR
        
        _LOG.warning(f"Unhandled command format: {cmd_id} with params: {params}")
        return StatusCodes.BAD_REQUEST

    async def _execute_command(self, command: str) -> bool:
        _LOG.info(f"Executing command: {command}")
        
        if command == "power_on":
            return await self._client.power_on_wol()
        elif command.startswith("launch_exe:"):
            return await self._client.send_remote_command(command)
        elif command.startswith("launch_url:"):
            return await self._client.send_remote_command(command)
        else:
            return await self._client.send_remote_command(command)

    async def push_update(self):
        if self._api.configured_entities.contains(self.id):
            attrs_to_update = {
                Attributes.STATE: States.ON
            }
            self._api.configured_entities.update_attributes(self.id, attrs_to_update)