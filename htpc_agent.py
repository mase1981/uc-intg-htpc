#!/usr/bin/env python3
"""
HTPC Windows Agent - Enhanced Version with Complete Command Support
Professional Windows application with system tray integration.
"""

import json
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse
import pystray
from PIL import Image, ImageDraw

# Enhanced imports for functionality
try:
    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    print("ERROR: pyautogui not available. Install with: pip install pyautogui")
    sys.exit(1)

# Configure logging to file only
log_file = os.path.join(os.path.expanduser("~"), "htpc_agent.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
    ]
)
logger = logging.getLogger(__name__)

class HTCPAgentTray:
    """System tray application for HTCP Agent."""
    
    def __init__(self):
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.icon = None
        
    def create_icon_image(self):
        """Create a simple icon image programmatically."""
        width = 64
        height = 64
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple monitor icon
        draw.rectangle([10, 15, 54, 40], fill=(100, 150, 255), outline=(50, 50, 50), width=2)
        draw.rectangle([25, 40, 39, 45], fill=(80, 80, 80))
        draw.rectangle([20, 45, 44, 50], fill=(60, 60, 60))
        draw.text((18, 22), "PC", fill=(255, 255, 255))
        
        return image
    
    def start_server(self):
        """Start the HTTP server in a separate thread."""
        try:
            self.server = HTCPServer()
            self.server_thread = threading.Thread(target=self.server.run, daemon=True)
            self.server_thread.start()
            self.is_running = True
            logger.info("HTPC Agent server started successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to start server: {e}")
            return False
    
    def stop_server(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.stop()
            self.is_running = False
            logger.info("HTPC Agent server stopped")
    
    def open_status_page(self, icon=None, item=None):
        """Open the web status page directly."""
        webbrowser.open("http://localhost:8086/status")
    
    def open_log(self, icon=None, item=None):
        """Open log file."""
        try:
            os.startfile(log_file)
        except Exception as e:
            logger.error(f"Failed to open log file: {e}")
    
    def restart_service(self, icon=None, item=None):
        """Restart the agent service."""
        self.stop_server()
        time.sleep(1)
        if self.start_server():
            self.show_notification("HTPC Agent restarted successfully")
        else:
            self.show_notification("Failed to restart HTPC Agent")
    
    def show_notification(self, message):
        """Show system tray notification."""
        if self.icon:
            self.icon.notify(message, "HTPC Agent")
    
    def quit_application(self, icon=None, item=None):
        """Quit the application safely."""
        try:
            self.stop_server()
            if self.icon:
                self.icon.stop()
            logger.info("HTPC Agent stopped by user")
        except Exception as e:
            logger.error(f"Error during quit: {e}")
        finally:
            os._exit(0)
    
    def run(self):
        """Run the system tray application."""
        icon_image = self.create_icon_image()
        
        # Clean, simple menu - Status opens web interface directly
        menu = pystray.Menu(
            pystray.MenuItem("Status & Control", self.open_status_page, default=True),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Restart Service", self.restart_service),
            pystray.MenuItem("View Log", self.open_log),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self.quit_application)
        )
        
        self.icon = pystray.Icon("htpc_agent", icon_image, "HTPC Agent", menu)
        
        if self.start_server():
            self.show_notification("HTPC Agent started - Ready for Unfolded Circle Remote!")
        else:
            self.show_notification("Failed to start HTPC Agent")
        
        self.icon.run()


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Thread-based HTTP Server for handling multiple concurrent requests."""
    daemon_threads = True
    allow_reuse_address = True


class HTCPServer:
    """HTTP server for HTCP agent commands."""
    
    def __init__(self, port=8086):
        self.port = port
        self.server = None
        self.start_time = time.time()
    
    def run(self):
        """Run the HTTP server."""
        try:
            self.server = ThreadedHTTPServer(('', self.port), HTCPAgentHandler)
            self.server.start_time = self.start_time
            logger.info(f"HTPC HTTP server listening on port {self.port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"HTTP server error: {e}")
    
    def stop(self):
        """Stop the HTTP server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()


class HTCPAgentHandler(BaseHTTPRequestHandler):
    """HTTP request handler for HTCP agent commands."""

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logger.info("%s - - %s" % (self.address_string(), format % args))

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == '/health':
            self._send_json_response(200, {
                "status": "healthy",
                "agent_version": "2.1.0",
                "timestamp": time.time()
            })
        elif parsed_path.path == '/status':
            self._send_html_status()
        elif parsed_path.path == '/favicon.ico':
            self._send_json_response(404, {"error": "Not found"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _send_html_status(self):
        """Send enhanced HTML status page."""
        uptime = time.time() - self.server.start_time
        hours = int(uptime // 3600)
        minutes = int((uptime % 3600) // 60)
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>HTPC Agent Control Panel</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ 
            font-family: 'Segoe UI', Arial, sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{ 
            background: white; 
            padding: 30px; 
            border-radius: 12px; 
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            max-width: 700px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 2px solid #eee;
            padding-bottom: 20px;
        }}
        .status {{ 
            color: #28a745; 
            font-weight: bold; 
            font-size: 20px;
            display: inline-block;
            padding: 5px 15px;
            background: #d4edda;
            border-radius: 20px;
            border: 1px solid #c3e6cb;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin: 20px 0;
        }}
        .info {{ 
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }}
        .info strong {{ color: #495057; }}
        .feature-list {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            list-style: none;
            padding: 0;
            margin: 20px 0;
        }}
        .feature-list li {{
            padding: 10px;
            background: #e8f5e8;
            border-radius: 6px;
            border-left: 3px solid #28a745;
        }}
        .feature-list li:before {{
            content: "✓ ";
            color: #28a745;
            font-weight: bold;
            margin-right: 8px;
        }}
        .footer {{
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            background: #e3f2fd;
            border-radius: 8px;
            border: 1px solid #bbdefb;
        }}
        .highlight {{ 
            color: #1976d2; 
            font-weight: bold; 
        }}
        .version {{ 
            position: absolute; 
            top: 10px; 
            right: 15px; 
            background: #6c757d; 
            color: white; 
            padding: 5px 10px; 
            border-radius: 15px; 
            font-size: 12px; 
        }}
        @media (max-width: 600px) {{
            .info-grid, .feature-list {{ grid-template-columns: 1fr; }}
            .container {{ padding: 20px; margin: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="version">v2.1.0</div>
    <div class="container">
        <div class="header">
            <h1>HTPC Agent Control Panel</h1>
            <div class="status">● RUNNING</div>
        </div>
        
        <div class="info-grid">
            <div class="info">
                <strong>Service Status:</strong><br>
                Active and ready
            </div>
            <div class="info">
                <strong>Network Port:</strong><br>
                8086 (HTTP)
            </div>
            <div class="info">
                <strong>Uptime:</strong><br>
                {hours}h {minutes}m
            </div>
            <div class="info">
                <strong>Audio Control:</strong><br>
                {'Available' if AUDIO_AVAILABLE else 'Limited'}
            </div>
        </div>
        
        <h3>Available Features</h3>
        <ul class="feature-list">
            <li>Windows shortcuts (Win+L, Win+D, etc.)</li>
            <li>Task Manager & System controls</li>
            <li>Function keys (F1-F12)</li>
            <li>Navigation & media keys</li>
            <li>Volume management</li>
            <li>Power management</li>
            <li>Custom app launching</li>
            <li>System tray integration</li>
        </ul>
        
        <div class="footer">
            <h3>🎮 Ready for Unfolded Circle Remote!</h3>
            <p>Configure your Remote with this PC's IP address to start controlling your HTPC.</p>
            <p class="highlight">Enhanced command support for complete Windows control.</p>
        </div>
    </div>
</body>
</html>"""
        
        response = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def do_POST(self):
        """Handle POST requests."""
        if self.path == '/command':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                command_data = json.loads(post_data.decode('utf-8'))
                result = self._handle_command(command_data)
                self._send_json_response(200, result)
            except json.JSONDecodeError:
                self._send_json_response(400, {"error": "Invalid JSON"})
            except Exception as e:
                logger.error(f"Error processing command: {e}", exc_info=True)
                self._send_json_response(500, {"error": f"Internal error: {str(e)}"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _send_json_response(self, status_code, data):
        """Send JSON response."""
        response = json.dumps(data)
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(response)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(response.encode('utf-8'))

    def _handle_command(self, command_data):
        """Handle incoming command with comprehensive Windows support."""
        command = command_data.get('command', '')
        logger.info(f"Command: {command}")
        
        try:
            # Navigation keys
            if command == "arrow_up":
                pyautogui.press('up')
                return {"status": "success", "message": "Sent key: up"}
            elif command == "arrow_down":
                pyautogui.press('down')
                return {"status": "success", "message": "Sent key: down"}
            elif command == "arrow_left":
                pyautogui.press('left')
                return {"status": "success", "message": "Sent key: left"}
            elif command == "arrow_right":
                pyautogui.press('right')
                return {"status": "success", "message": "Sent key: right"}
            elif command == "enter":
                pyautogui.press('enter')
                return {"status": "success", "message": "Sent key: enter"}
            elif command == "escape":
                pyautogui.press('esc')
                return {"status": "success", "message": "Sent key: escape"}
            elif command == "back":
                pyautogui.press('backspace')
                return {"status": "success", "message": "Sent key: backspace"}
            elif command == "tab":
                pyautogui.press('tab')
                return {"status": "success", "message": "Sent key: tab"}
            elif command == "space":
                pyautogui.press('space')
                return {"status": "success", "message": "Sent key: space"}
            elif command == "delete":
                pyautogui.press('delete')
                return {"status": "success", "message": "Sent key: delete"}
            elif command == "backspace":
                pyautogui.press('backspace')
                return {"status": "success", "message": "Sent key: backspace"}
            elif command == "home":
                pyautogui.press('home')
                return {"status": "success", "message": "Sent key: home"}
            elif command == "end":
                pyautogui.press('end')
                return {"status": "success", "message": "Sent key: end"}
            elif command == "page_up":
                pyautogui.press('pageup')
                return {"status": "success", "message": "Sent key: page up"}
            elif command == "page_down":
                pyautogui.press('pagedown')
                return {"status": "success", "message": "Sent key: page down"}

            # Windows shortcuts (ENHANCED SUPPORT)
            elif command == "windows_key":
                pyautogui.press('win')
                return {"status": "success", "message": "Sent Windows key"}
            elif command == "win_l":
                pyautogui.hotkey('win', 'l')
                return {"status": "success", "message": "Locked Windows"}
            elif command == "win_d":
                pyautogui.hotkey('win', 'd')
                return {"status": "success", "message": "Show desktop"}
            elif command == "win_e":
                pyautogui.hotkey('win', 'e')
                return {"status": "success", "message": "Opened File Explorer"}
            elif command == "win_r":
                pyautogui.hotkey('win', 'r')
                return {"status": "success", "message": "Opened Run dialog"}
            elif command == "win_i":
                pyautogui.hotkey('win', 'i')
                return {"status": "success", "message": "Opened Windows Settings"}
            elif command == "alt_tab":
                pyautogui.hotkey('alt', 'tab')
                return {"status": "success", "message": "Alt+Tab window switcher"}
            elif command == "ctrl_alt_del":
                pyautogui.hotkey('ctrl', 'alt', 'del')
                return {"status": "success", "message": "Ctrl+Alt+Del sent"}
            elif command == "ctrl_shift_esc":
                pyautogui.hotkey('ctrl', 'shift', 'esc')
                return {"status": "success", "message": "Opened Task Manager"}

            # Function keys (F1-F12)
            elif command.startswith('f') and len(command) <= 3 and command[1:].isdigit():
                key_num = command[1:]
                if 1 <= int(key_num) <= 12:
                    pyautogui.press(f'f{key_num}')
                    return {"status": "success", "message": f"Sent function key: {command}"}
                else:
                    return {"status": "error", "message": f"Invalid function key: {command}"}

            # Media controls
            elif command == "play_pause":
                pyautogui.press('playpause')
                return {"status": "success", "message": "Sent media key: play/pause"}
            elif command == "play":
                pyautogui.press('playpause')
                return {"status": "success", "message": "Sent media key: play"}
            elif command == "pause":
                pyautogui.press('playpause')
                return {"status": "success", "message": "Sent media key: pause"}
            elif command == "stop":
                pyautogui.press('stop')
                return {"status": "success", "message": "Sent media key: stop"}
            elif command == "previous":
                pyautogui.press('prevtrack')
                return {"status": "success", "message": "Sent media key: previous"}
            elif command == "next":
                pyautogui.press('nexttrack')
                return {"status": "success", "message": "Sent media key: next"}
            elif command == "fast_forward":
                pyautogui.press('fastforward')
                return {"status": "success", "message": "Sent media key: fast forward"}
            elif command == "rewind":
                pyautogui.press('rewind')
                return {"status": "success", "message": "Sent media key: rewind"}
            elif command == "record":
                pyautogui.press('f9')  # Common record key
                return {"status": "success", "message": "Sent record key"}
            elif command == "volume_up":
                pyautogui.press('volumeup')
                return {"status": "success", "message": "Sent media key: volume up"}
            elif command == "volume_down":
                pyautogui.press('volumedown')
                return {"status": "success", "message": "Sent media key: volume down"}
            elif command == "mute" or command == "mute_toggle":
                pyautogui.press('volumemute')
                return {"status": "success", "message": "Sent media key: mute"}

            # Volume control with level
            elif command.startswith("set_volume:"):
                try:
                    volume_level = int(command.split(":", 1)[1])
                    volume_level = max(0, min(100, volume_level))  # Clamp to 0-100
                    
                    if AUDIO_AVAILABLE:
                        # Use pycaw for precise volume control
                        devices = AudioUtilities.GetSpeakers()
                        interface = devices.Activate(IAudioEndpointVolume._iid_, None, None)
                        volume = interface.QueryInterface(IAudioEndpointVolume)
                        volume.SetMasterScalarVolume(volume_level / 100.0, None)
                        return {"status": "success", "message": f"Set volume to {volume_level}%"}
                    else:
                        # Fallback to keyboard volume keys
                        current_volume = 50  # Assume 50% as baseline
                        diff = volume_level - current_volume
                        if diff > 0:
                            for _ in range(abs(diff) // 2):
                                pyautogui.press('volumeup')
                        elif diff < 0:
                            for _ in range(abs(diff) // 2):
                                pyautogui.press('volumedown')
                        return {"status": "success", "message": f"Adjusted volume towards {volume_level}%"}
                except ValueError:
                    return {"status": "error", "message": "Invalid volume level"}

            # Power management
            elif command == "power_sleep":
                subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], shell=True)
                return {"status": "success", "message": "System going to sleep"}
            elif command == "power_hibernate":
                subprocess.run(['shutdown', '/h'], shell=True)
                return {"status": "success", "message": "System hibernating"}
            elif command == "power_shutdown":
                subprocess.run(['shutdown', '/s', '/t', '0'], shell=True)
                return {"status": "success", "message": "System shutting down"}
            elif command == "power_restart":
                subprocess.run(['shutdown', '/r', '/t', '0'], shell=True)
                return {"status": "success", "message": "System restarting"}
            elif command == "power_wake":
                # Wake is typically handled by WOL, but we can simulate user activity
                pyautogui.move(1, 1)
                pyautogui.move(-1, -1)
                return {"status": "success", "message": "Wake signal sent"}

            # System utilities  
            elif command == "pair_bluetooth":
                try:
                    # Use start command to open ms-settings
                    subprocess.run(['start', 'ms-settings:bluetooth'], shell=True, check=False)
                    return {"status": "success", "message": "Opened Bluetooth settings"}
                except:
                    # Fallback to control panel
                    subprocess.run(['control', 'bthprops.cpl'], shell=True, check=False)
                    return {"status": "success", "message": "Opened Bluetooth control panel"}
            elif command == "show_pairing_help":
                webbrowser.open("https://support.microsoft.com/en-us/windows/pair-a-bluetooth-device-in-windows-2be7b51f-6ae9-b757-a3b9-95ee40c3e242")
                return {"status": "success", "message": "Opened Bluetooth pairing help"}

            # Executable launch commands
            elif command.startswith('launch_exe:'):
                exe_path = command.split(':', 1)[1]
                return self._launch_executable(exe_path)
            
            # URL launch commands
            elif command.startswith('launch_url:'):
                url = command.split(':', 1)[1]
                return self._launch_url(url)

            # Default web applications (using URLs - always work)
            elif command == "app_plex":
                webbrowser.open("https://app.plex.tv/desktop")
                return {"status": "success", "message": "Launched Plex Web"}
            elif command == "app_jellyfin":
                webbrowser.open("http://localhost:8096")
                return {"status": "success", "message": "Launched Jellyfin Web"}
            elif command == "app_kodi":
                webbrowser.open("https://kodi.tv/download")
                return {"status": "success", "message": "Opened Kodi download page"}
            elif command == "app_netflix":
                webbrowser.open("https://www.netflix.com")
                return {"status": "success", "message": "Launched Netflix"}
            elif command == "app_youtube":
                webbrowser.open("https://www.youtube.com")
                return {"status": "success", "message": "Launched YouTube"}
            elif command == "app_spotify":
                webbrowser.open("https://open.spotify.com")
                return {"status": "success", "message": "Launched Spotify Web"}
            elif command == "app_vlc":
                # Try to launch VLC, fallback to download page
                try:
                    subprocess.Popen(['vlc'], shell=False)
                    return {"status": "success", "message": "Launched VLC"}
                except:
                    webbrowser.open("https://www.videolan.org/vlc/")
                    return {"status": "success", "message": "VLC not found - opened download page"}
            elif command == "app_chrome":
                webbrowser.open("https://www.google.com")
                return {"status": "success", "message": "Opened Google in default browser"}
            elif command == "app_firefox":
                webbrowser.open("https://www.mozilla.org/firefox/")
                return {"status": "success", "message": "Opened Firefox download page"}
            elif command == "app_steam":
                webbrowser.open("https://store.steampowered.com")
                return {"status": "success", "message": "Opened Steam Store"}

            # System applications that always exist
            elif command == "custom_calc":
                subprocess.Popen(['calc.exe'], shell=False)
                return {"status": "success", "message": "Launched Calculator"}
            elif command == "custom_notepad":
                subprocess.Popen(['notepad.exe'], shell=False)
                return {"status": "success", "message": "Launched Notepad"}
            elif command == "custom_cmd":
                subprocess.Popen(['cmd.exe'], shell=False)
                return {"status": "success", "message": "Launched Command Prompt"}
            elif command == "custom_powershell":
                subprocess.Popen(['powershell.exe'], shell=False)
                return {"status": "success", "message": "Launched PowerShell"}

            # URL shortcuts
            elif command == "url_youtube":
                webbrowser.open("https://www.youtube.com")
                return {"status": "success", "message": "Opened YouTube"}
            elif command == "url_netflix":
                webbrowser.open("https://www.netflix.com")
                return {"status": "success", "message": "Opened Netflix"}
            elif command == "url_plex":
                webbrowser.open("https://app.plex.tv")
                return {"status": "success", "message": "Opened Plex Web"}
            elif command == "url_jellyfin":
                webbrowser.open("http://localhost:8096")
                return {"status": "success", "message": "Opened Jellyfin Web"}

            else:
                return {"status": "error", "message": f"Unknown command: {command}"}
                
        except Exception as e:
            logger.error(f"Command failed: {e}", exc_info=True)
            return {"status": "error", "message": f"Command failed: {str(e)}"}

    def _launch_executable(self, exe_path):
        """Launch an executable with proper path handling."""
        try:
            if exe_path.startswith('"') and exe_path.endswith('"'):
                exe_path = exe_path[1:-1]
            
            expanded_path = os.path.expandvars(exe_path)
            
            if not os.path.exists(expanded_path):
                return {"status": "error", "message": f"Executable not found: {expanded_path}"}
            
            subprocess.Popen([expanded_path], shell=False)
            return {"status": "success", "message": f"Launched {os.path.basename(expanded_path)}"}
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to launch: {str(e)}"}

    def _launch_url(self, url):
        """Launch URL in default browser."""
        try:
            webbrowser.open(url)
            return {"status": "success", "message": f"Opened URL in browser"}
        except Exception as e:
            return {"status": "error", "message": f"Failed to open URL: {str(e)}"}


def main():
    """Main entry point."""
    # Hide console window on Windows
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    app = HTCPAgentTray()
    app.run()


if __name__ == "__main__":
    main()