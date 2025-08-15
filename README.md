# HTPC System Monitor Integration for Unfolded Circle Remote Two/3

[![GitHub Release](https://img.shields.io/github/release/mase1981/uc-intg-htpc.svg)](https://github.com/mase1981/uc-intg-htpc/releases)
[![GitHub License](https://img.shields.io/github/license/mase1981/uc-intg-htpc.svg)](https://github.com/mase1981/uc-intg-htpc/blob/main/LICENSE)

Custom HTPC system monitoring and control integration for your Unfolded Circle Remote Two/3. Transform your remote into a powerful HTPC command center with real-time system monitoring and comprehensive Windows control.

**NOTE:** This integration requires two components: LibreHardwareMonitor (free) running on your HTPC and the HTPC Agent (provided).

## 🖥️ Features

### System Monitoring
- **Real-time Performance**: CPU temperature, load, and clock speed
- **Memory Usage**: RAM utilization with detailed breakdown
- **Storage Activity**: Disk usage, temperature, and activity monitoring
- **Network Activity**: Upload/download speeds and utilization
- **Temperature Overview**: CPU, storage, and motherboard temperatures
- **Fan Monitoring**: Active fan detection with RPM readings
- **Power Consumption**: CPU package power draw (when available)
- **GPU Performance**: Dedicated GPU monitoring (when available)

### Remote Control Interface
- **6-Page Layout**: Navigation, Media, Windows, System Tools, Function Keys, Power
- **Windows Shortcuts**: Complete Win+key combinations and system controls
- **Media Controls**: Full transport controls for any media application
- **System Tools**: Built-in Windows applications and web services
- **Function Keys**: F1-F12 with dedicated shortcuts
- **Power Management**: Sleep, hibernate, shutdown, restart controls

### Advanced Features
- **Custom App Launching**: Use "Send Command" to launch any Windows application
- **Dynamic Source Switching**: 8 monitoring views accessible via SOURCE selection
- **Base64 Icon Embedding**: Offline operation with embedded icons
- **Real-time Updates**: 5-second monitoring refresh with efficient state management

## 📋 Prerequisites

### Hardware Requirements
- **Windows PC/HTPC**: Windows 10/11 system to monitor and control
- **Remote Two/3**: Unfolded Circle Remote Two/3
- **Network**: Both devices on same local network
- **Hardware Sensors**: Compatible motherboard with sensor chips (for full monitoring)

### Software Requirements

#### Required Downloads
1. **LibreHardwareMonitor** (Free)
   - Download: [https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)
   - Version: Latest release
   - Purpose: System sensor data collection

2. **HTPC Agent** (Provided with integration)
   - File: `HTPC_Agent.exe`
   - Purpose: Windows command execution and control

#### Network Requirements
- **Port 8085**: LibreHardwareMonitor web server (HTTP)
- **Port 8086**: HTPC Agent communication (HTTP)
- **Same Network**: Both Remote and HTPC must be on same local network
- **Firewall**: Ensure ports 8085 and 8086 are not blocked

## 🚀 Quick Start

### Step 1: Prepare Your HTPC

#### Install LibreHardwareMonitor
1. **Download** LibreHardwareMonitor from official GitHub releases
2. **Extract** to a permanent location (e.g., `C:\Program Files\LibreHardwareMonitor\`)
3. **Run as Administrator** (required for sensor access)
4. **Enable Web Server**:
   - Go to: **Options** → **Web Server**
   - Check: **☑ Run web server**
   - Port: **8085** (default)
   - Click: **OK**
5. **Verify**: Open browser to `http://localhost:8085/data.json` - should show sensor data

#### Install HTPC Agent
1. **Download** `HTPC_Agent.exe` from integration package
2. **Place** in a permanent location (e.g., `C:\HTPC_Agent\`)
3. **Run** `HTPC_Agent.exe` - will appear in system tray
4. **Verify**: Check system tray for HTPC Agent icon
5. **Test**: Right-click tray icon → **Status & Control** → should open web interface

### Step 2: Configure Network
**NOTE**: It is best and ideal to give your PC a static IP via your router reservation, the below are instructions for users to find their PC IP, however it is best to simply give it a static IP.
#### Find Your HTPC IP Address
```bash
# Method 1: Command prompt
ipconfig

# Method 2: PowerShell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

#### Test Connectivity
```bash
# From any device on your network, test both services:
http://YOUR_HTPC_IP:8085/data.json    # LibreHardwareMonitor
http://YOUR_HTPC_IP:8086/status       # HTPC Agent
```

**Example**: If your HTPC IP is `192.168.1.100`:
- LibreHardwareMonitor: `http://192.168.1.100:8085/data.json`
- HTPC Agent: `http://192.168.1.100:8086/status`

### Step 3: Install Integration on Remote

#### Via Remote Two/3 Web Interface
1. **Access Web Configurator**
   ```
   http://YOUR_REMOTE_IP/configurator
   ```

2. **Install Integration**
   - Navigate to: **Integrations** → **Add New** / **Install Custom**
   - Upload: **uc-intg-htpc-***
   - Click: **Upload**

3. **Configure Device**
   - Enter your HTPC IP address (e.g., `192.168.1.100`)
   - Select temperature unit (Celsius/Fahrenheit)
   - Click: **Continue**
   - Wait for automatic connection testing
   - Complete setup

4. **Add Entities**
   - **HTPC System Monitor** (Media Player) - for system monitoring
   - **HTPC Advanced Remote** (Remote) - for system control
   - Add both to your desired activities

## 🎮 Using the Integration

### System Monitoring (Media Player Entity)

#### Source Selection
Use the **SELECT SOURCE** feature to switch between monitoring views:

| Source | Information Displayed |
|--------|----------------------|
| **System Overview** | CPU temp/load, CPU power, Memory usage |
| **CPU Performance** | Temperature, Load percentage, Clock speed |
| **GPU Performance** | GPU temperature and load (if dedicated GPU) |
| **Memory Usage** | Used/Total memory with percentage |
| **Storage Activity** | Used/Total storage with usage percentage |
| **Network Activity** | Upload/Download speeds |
| **Temperature Overview** | CPU, Storage, Motherboard temperatures |
| **Fan Monitoring** | Active fans count, Average/Maximum speeds |
| **Power Consumption** | CPU package power draw |

#### Real-time Updates
- **Refresh Rate**: 5 seconds
- **Temperature Units**: Configurable (°C/°F)
- **Connection Status**: Shows connection errors if HTPC unreachable
- **Data Persistence**: Maintains last known values during brief disconnections

### Remote Control (Remote Entity)

#### Page Overview
| Page | Purpose | Key Features |
|------|---------|--------------|
| **Navigation** | Directional controls | Arrow keys, Enter, Escape, Tab, Space |
| **Media Controls** | Media playback | Play/Pause, Stop, Volume, Transport controls |
| **Windows Shortcuts** | System navigation | Win+key combinations, Alt+Tab, Task Manager |
| **System Tools** | Applications | Calculator, Notepad, PowerShell, Web services |
| **Function Keys** | F1-F12 | Function keys with quick system shortcuts |
| **Power & System** | Power management | Sleep, Hibernate, Shutdown, Restart |

#### Custom Application Launching

Use the **Send Command** feature in the Remote web configurator to launch any Windows application:

**Format**: `launch_exe:FULL_PATH_TO_EXECUTABLE`

**Examples**:
```bash
# Launch Steam
launch_exe:"C:\Program Files (x86)\Steam\steam.exe"

# Launch VLC Media Player  
launch_exe:"C:\Program Files\VideoLAN\VLC\vlc.exe"

# Launch Plex Desktop
launch_exe:"C:\Users\%USERNAME%\AppData\Local\Plex\Plex.exe"

# Launch Chrome
launch_exe:"C:\Program Files\Google\Chrome\Application\chrome.exe"

# Launch Kodi
launch_exe:"C:\Program Files\Kodi\kodi.exe

# Launch OBS Studio
launch_exe:"C:\Program Files\obs-studio\bin\64bit\obs64.exe"
```

**URL Launching**:
```bash
# Launch websites
launch_url:https://www.netflix.com
launch_url:https://www.youtube.com
launch_url:https://app.plex.tv
launch_url:http://localhost:8096  # Jellyfin
```

#### Finding Application Paths
```bash
# Method 1: Search in Start Menu
# Right-click application → "Open file location" → Properties → Copy path

# Method 2: Command Prompt
where chrome
where vlc

# Method 3: PowerShell
Get-Command chrome | Select-Object Source
```

## 🔧 Configuration

### Environment Variables (Optional)

| Variable | Description | Default |
|----------|-------------|---------|
| `UC_INTEGRATION_HTTP_PORT` | Integration HTTP port | `9090` |
| `UC_INTEGRATION_INTERFACE` | Bind interface | `0.0.0.0` |
| `UC_CONFIG_HOME` | Configuration directory | `./` |

### Configuration File

Located at: `config.json` in integration directory

```json
{
  "host": "192.168.1.100",
  "port": 8085,
  "temperature_unit": "celsius"
}
```

### HTPC Agent Configuration

The HTPC Agent provides system tray management:

- **Right-click** system tray icon for options
- **Status & Control**: Opens web interface
- **Restart Service**: Restarts the agent
- **View Log**: Opens log file for troubleshooting
- **Quit**: Stops the agent

## 🛠️ Troubleshooting

### Setup Issues

**Problem**: Integration setup fails with connection error

**Solutions**:
1. **Verify HTPC IP address**:
   ```bash
   ping YOUR_HTPC_IP
   ```
2. **Test LibreHardwareMonitor**:
   ```bash
   curl http://YOUR_HTPC_IP:8085/data.json
   ```
3. **Test HTCP Agent**:
   ```bash
   curl http://YOUR_HTPC_IP:8086/health
   ```
4. **Check Windows Firewall**:
   - Allow ports 8085 and 8086
   - Or temporarily disable firewall for testing
5. **Verify same network**: Both devices must be on same subnet

**Problem**: LibreHardwareMonitor shows no sensors

**Solutions**:
1. **Run as Administrator**: Required for hardware sensor access
2. **Check motherboard compatibility**: Some systems have limited sensor support
3. **Update motherboard drivers**: Ensure chipset drivers are current
4. **Enable sensors in BIOS**: Some sensors may be disabled in BIOS

**Problem**: HTPC Agent not starting

**Solutions**:
1. **Check antivirus**: Some antivirus may block the executable
2. **Run as Administrator**: May require elevated privileges
3. **Check dependencies**: Ensure Python runtime dependencies are met
4. **Firewall exceptions**: Add HTPC_Agent.exe to firewall exceptions

### Runtime Issues

**Problem**: System monitoring shows "Connection Error"

**Solutions**:
1. **Check network connectivity**: Ping test between devices
2. **Verify services running**: Both LibreHardwareMonitor and HTCP Agent
3. **Check IP address changes**: HTPC may have received new IP via DHCP
4. **Restart services**: Restart both LibreHardwareMonitor and HTCP Agent

**Problem**: Remote commands not working

**Solutions**:
1. **Test HTCP Agent**: Check `http://HTPC_IP:8086/status`
2. **Check command syntax**: Verify proper `launch_exe:` format
3. **Path validation**: Ensure executable paths are correct and accessible
4. **Permissions**: Some applications may require administrator privileges

**Problem**: Missing temperature or fan data

**Solutions**:
1. **Hardware compatibility**: Not all systems support all sensors
2. **Sensor availability**: Check LibreHardwareMonitor directly for available sensors
3. **Administrative privileges**: Ensure LibreHardwareMonitor runs as administrator
4. **Motherboard support**: Some sensors require specific motherboard chipsets

### Debug Information

**Enable detailed logging in HTCP Agent**:
- Check log file: `%USERPROFILE%\htpc_agent.log`
- System tray → Right-click → **View Log**

**Check integration status**:
```bash
# Via web configurator
http://YOUR_REMOTE_IP/configurator → Integrations → HTPC → Status
```

**Test LibreHardwareMonitor API**:
```bash
# Device information
curl "http://HTPC_IP:8085/data.json"

# Web interface
http://HTPC_IP:8085
```

**Test HTCP Agent API**:
```bash
# Health check
curl "http://HTPC_IP:8086/health"

# Status page
http://HTPC_IP:8086/status

# Send test command
curl -X POST "http://HTPC_IP:8086/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "custom_calc"}'
```

## 🏗️ Advanced Setup

### Static IP Configuration

For reliable operation, configure static IP for your HTPC:

**Windows Network Settings**:
1. **Control Panel** → **Network and Internet** → **Network Connections**
2. **Right-click** your network connection → **Properties**
3. **Select** "Internet Protocol Version 4 (TCP/IPv4)" → **Properties**
4. **Choose** "Use the following IP address"
5. **Configure** IP, Subnet, Gateway, DNS

### Startup Configuration

**Auto-start LibreHardwareMonitor**:
1. **Create shortcut** to LibreHardwareMonitor.exe
2. **Place in** Startup folder: `Win+R` → `shell:startup`
3. **Right-click shortcut** → **Properties** → **Advanced** → **Run as administrator**

**Auto-start HTPC Agent**:
1. **Create shortcut** to HTPC_Agent.exe  
2. **Place in** Startup folder: `Win+R` → `shell:startup`
3. **Properties** → **Run**: **Minimized**

### Security Considerations

**Firewall Rules**:
```bash
# Windows Firewall - Allow incoming connections
netsh advfirewall firewall add rule name="LibreHardwareMonitor" dir=in action=allow protocol=TCP localport=8085
netsh advfirewall firewall add rule name="HTCP Agent" dir=in action=allow protocol=TCP localport=8086
```

**Network Security**:
- Use only on trusted local networks
- Consider VPN access for remote monitoring
- Regularly update Windows and applications

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-htpc.git
cd uc-intg-htpc

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Building HTPC Agent

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller --onefile --windowed --name "HTPC_Agent" --version-file="version_info.txt" htcp_agent.py
```

### Testing

```bash
# Run integration directly
python -m uc_intg_htpc.driver

# Test with debug logging
UC_INTEGRATION_HTTP_PORT=9090 python uc_intg_htpc/driver.py
```

## 📄 License

This project is licensed under the MPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Community Resources

- **GitHub Issues**: [Report bugs and request features](https://github.com/mase1981/uc-intg-htpc/issues)
- **UC Community Forum**: [General discussion and support](https://unfolded.community/)
- **LibreHardwareMonitor**: [Official sensor monitoring support](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor)

### Professional Support

For enterprise deployments or professional integration services, contact the development team through GitHub.

---

**Made with ❤️ for the Unfolded Circle Community**

*Transform your HTPC into a smart, monitored, and fully controllable entertainment center with your Remote Two/3!*

**Author**: Meir Miyara