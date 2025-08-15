# HTCP Agent - Windows Command Execution Service

The HTCP Agent is a lightweight Windows service that enables remote command execution for the HTPC System Monitor Integration. It provides secure, local network communication between your Unfolded Circle Remote and Windows PC.

## 📋 Overview

### What It Does
- **Command Execution**: Processes remote commands from the HTPC integration
- **System Control**: Manages Windows shortcuts, applications, and power states
- **Web Interface**: Provides HTTP API for integration communication
- **System Tray**: Runs quietly in background with status monitoring

### Security Model
- **Local Network Only**: Binds to all interfaces but intended for LAN use
- **No Authentication**: Designed for trusted home networks
- **Limited Scope**: Only executes predefined safe commands
- **Process Isolation**: Runs in user context, not system level

## 🚀 Installation

### Quick Install
1. **Download**: `HTCP_Agent.exe` from this repository
2. **Place**: In permanent location (e.g., `C:\HTCP_Agent\`)
3. **Run**: Double-click `HTCP_Agent.exe`
4. **Verify**: Check system tray for HTCP Agent icon

### Detailed Installation

#### Step 1: Download and Place
```bash
# Create directory
mkdir C:\HTCP_Agent

# Copy executable
copy HTCP_Agent.exe C:\HTCP_Agent\
```

#### Step 2: First Run
- **Double-click** `C:\HTCP_Agent\HTCP_Agent.exe`
- **Allow** Windows Firewall access if prompted
- **Check** system tray for HTCP Agent icon
- **Test** by right-clicking tray icon → **Status & Control**

#### Step 3: Auto-Start (Optional)
```bash
# Method 1: Startup folder
# Win+R → shell:startup
# Create shortcut to HTCP_Agent.exe

# Method 2: Task Scheduler (more reliable)
# Windows → Task Scheduler → Create Basic Task
# Trigger: At startup
# Action: Start program → C:\HTCP_Agent\HTCP_Agent.exe
```

## 🔧 Configuration

### Network Settings
- **Port**: 8086 (default, not configurable)
- **Interface**: 0.0.0.0 (all interfaces)
- **Protocol**: HTTP (local network only)

### Firewall Configuration
The agent requires inbound connections on port 8086:

**Automatic** (prompted on first run):
- Windows will ask to allow firewall access
- Click **Allow access** for both Private and Public networks

**Manual**:
```bash
# Windows Firewall command
netsh advfirewall firewall add rule name="HTCP Agent" dir=in action=allow protocol=TCP localport=8086

# Or via GUI:
# Control Panel → Windows Defender Firewall → Allow an app
# Browse → Select HTCP_Agent.exe → Add
```

## 🎮 System Tray Interface

### Right-Click Menu Options

| Option | Description |
|--------|-------------|
| **Status & Control** | Opens web interface in browser |
| **View Log** | Opens log file for troubleshooting |
| **Restart Service** | Restarts the agent service |
| **About** | Shows version and build information |
| **Quit** | Stops the agent completely |

### Status Indicators
- **Green Icon**: Service running normally
- **Yellow Icon**: Service starting or restarting
- **Red Icon**: Service error or stopped
- **No Icon**: Service not running

## 🌐 Web Interface

Access the web interface at: `http://localhost:8086/status`

### Available Endpoints

| Endpoint | Method | Purpose | Example |
|----------|--------|---------|---------|
| `/status` | GET | Service status page | Browser access |
| `/health` | GET | Health check | Integration testing |
| `/command` | POST | Execute command | Remote control |

### Command Execution
```bash
# Example: Launch Calculator
curl -X POST "http://localhost:8086/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "custom_calc"}'

# Example: Launch application
curl -X POST "http://localhost:8086/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "launch_exe:C:\\Program Files\\VLC\\vlc.exe"}'
```

## 📝 Supported Commands

### Navigation Commands
```
arrow_up, arrow_down, arrow_left, arrow_right, enter, escape
back, home, end, page_up, page_down, tab, space, delete, backspace
```

### Media Controls
```
play_pause, play, pause, stop, previous, next, fast_forward
rewind, record, volume_up, volume_down, mute
```

### Windows Shortcuts
```
windows_key, alt_tab, win_r, win_d, win_e, win_i, ctrl_shift_esc
win_l (lock), ctrl_alt_del
```

### System Applications
```
custom_calc          # Calculator
custom_notepad       # Notepad
custom_cmd           # Command Prompt
custom_powershell    # PowerShell
```

### Web URLs
```
url_youtube          # Opens YouTube in default browser
url_netflix          # Opens Netflix
url_plex             # Opens Plex Web
url_jellyfin         # Opens Jellyfin
```

### Power Management
```
power_sleep          # Sleep mode
power_hibernate      # Hibernate
power_shutdown       # Shutdown
power_restart        # Restart
```

### System Utilities
```
pair_bluetooth       # Open Bluetooth settings
show_pairing_help    # Show Bluetooth help
```

### Custom Commands
```
launch_exe:FULL_PATH     # Launch any executable
launch_url:URL           # Open any URL
set_volume:0-100         # Set system volume
mute_toggle             # Toggle system mute
```

## 🔍 Troubleshooting

### Agent Won't Start

**Problem**: Double-clicking does nothing or shows error

**Solutions**:
1. **Check dependencies**: Ensure all required DLLs are present
2. **Run as Administrator**: Right-click → "Run as administrator"
3. **Check antivirus**: Add HTCP_Agent.exe to antivirus exclusions
4. **Windows compatibility**: Ensure Windows 10/11 compatibility

**Check log file**:
```
%USERPROFILE%\htcp_agent.log
```

### Port 8086 In Use

**Problem**: Agent fails to start due to port conflict

**Solutions**:
1. **Find conflicting process**:
   ```bash
   netstat -ano | findstr :8086
   tasklist | findstr PID_NUMBER
   ```
2. **Stop conflicting service**
3. **Check for multiple agent instances**

### Commands Not Working

**Problem**: Remote commands fail to execute

**Solutions**:
1. **Test locally**:
   ```bash
   curl -X POST "http://localhost:8086/command" -H "Content-Type: application/json" -d '{"command": "custom_calc"}'
   ```
2. **Check log file** for error messages
3. **Verify command syntax** (case-sensitive)
4. **Test with simple commands** first (like `custom_calc`)

### Network Connectivity

**Problem**: Integration can't reach agent

**Solutions**:
1. **Test from integration host**:
   ```bash
   curl http://HTCP_IP:8086/health
   ```
2. **Check firewall settings**
3. **Verify agent is running** (system tray icon)
4. **Test with browser**: `http://HTCP_IP:8086/status`

## 📊 Log Files

### Log Location
```
%USERPROFILE%\htcp_agent.log
```

### Log Levels
- **INFO**: Normal operation events
- **WARNING**: Non-critical issues
- **ERROR**: Command failures and errors
- **DEBUG**: Detailed execution information

### Example Log Entries
```
2025-01-16 10:30:15 - INFO - HTCP Agent started on port 8086
2025-01-16 10:30:16 - INFO - Web interface available at http://localhost:8086/status
2025-01-16 10:35:22 - INFO - Command executed: custom_calc
2025-01-16 10:35:25 - ERROR - Failed to execute: launch_exe:invalid_path.exe
```

## 🔒 Security Considerations

### Network Security
- **Use only on trusted networks**: Agent has no authentication
- **Firewall protection**: Ensure only local network access
- **Regular updates**: Keep Windows and agent updated

### Command Limitations
- **No system-level commands**: Agent runs in user context
- **No file system access**: Cannot read/write arbitrary files
- **Predefined commands only**: Cannot execute arbitrary code
- **Process isolation**: Commands run in separate processes

### Best Practices
1. **Dedicated user account**: Run agent under limited user account
2. **Network segmentation**: Use VLAN isolation if possible
3. **Regular monitoring**: Check log files for suspicious activity
4. **Firewall rules**: Restrict access to specific IP ranges

## 🛠️ Advanced Configuration

### Custom Command Extension

To add custom commands, modify the agent source code (`htcp_agent.py`):

```python
def handle_custom_command(self, command):
    """Add your custom command handling here"""
    if command == "my_custom_app":
        subprocess.run(["C:\\Path\\To\\MyApp.exe"])
        return True
    return False
```

### Service Installation

For production environments, consider installing as Windows service:

```bash
# Using NSSM (Non-Sucking Service Manager)
nssm install HTCPAgent "C:\HTCP_Agent\HTCP_Agent.exe"
nssm set HTCPAgent DisplayName "HTCP Agent Service"
nssm set HTCPAgent Description "HTPC Integration Command Agent"
nssm start HTCPAgent
```

## 📈 Performance

### Resource Usage
- **Memory**: ~10-15 MB typical usage
- **CPU**: Minimal (event-driven)
- **Network**: HTTP requests only
- **Disk**: Log file growth minimal

### Scaling Considerations
- **Single instance**: One agent per Windows machine
- **Concurrent commands**: Queued execution
- **Response time**: Sub-second for most commands

## 🔄 Updates

### Update Process
1. **Stop current agent**: Right-click tray → Quit
2. **Replace executable**: Overwrite HTCP_Agent.exe
3. **Restart agent**: Double-click new executable
4. **Verify operation**: Check system tray and test commands

### Version Checking
- **System tray**: Right-click → About
- **Web interface**: `http://localhost:8086/status`
- **Log file**: Version logged on startup

## 📞 Support

### Troubleshooting Steps
1. **Check system tray** for agent icon
2. **Review log file** for errors
3. **Test web interface** locally
4. **Verify firewall settings**
5. **Test simple commands** first

### Getting Help
- **GitHub Issues**: Report bugs and issues
- **Log files**: Include relevant log entries
- **System information**: Windows version, antivirus software
- **Network details**: Firewall configuration, network topology

---

**HTCP Agent v1.0** - Part of the HTPC System Monitor Integration  
**Compatibility**: Windows 10/11  
**License**: MPL-2.0  

*Secure, lightweight command execution for your HTPC remote control needs.*