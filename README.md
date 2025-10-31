# HTPC System Monitor Integration for Unfolded Circle Remote

![htpc](https://img.shields.io/badge/htpc-monitor-blue)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-htpc)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-htpc/total)
![License](https://img.shields.io/badge/license-MPL--2.0-blue)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA)](https://github.com/sponsors/mase1981/button)


> **Transform your Unfolded Circle Remote into a powerful HTPC command center with real-time system monitoring and comprehensive Windows control**

Monitor CPU, GPU, memory, storage, network, temperatures, and fan speeds while controlling your Windows HTPC through remote control, media playback, and system management—all from your Unfolded Circle Remote Two/3.

---

## ✨ Features

### 🎛️ Flexible Operation Modes

Choose your setup based on your needs:

- **Full Monitoring + Control** - Complete system monitoring with media player entity + remote control
- **Remote Control Only** - Lightweight Windows control without hardware monitoring requirements

### System Monitoring (Media Player Entity - Optional)
- ✅ **Real-time Performance** - CPU temperature, load, and clock speed
- ✅ **GPU Monitoring** - Dedicated GPU detection with temperature and load tracking
- ✅ **Memory Usage** - RAM utilization with detailed breakdown
- ✅ **Storage Activity** - Disk usage, temperature, and activity monitoring
- ✅ **Network Activity** - Upload/download speeds and utilization
- ✅ **Temperature Overview** - CPU, storage, and motherboard temperatures
- ✅ **Fan Monitoring** - Active fan detection with RPM readings
- ✅ **Power Consumption** - CPU package power draw (when available)
- ✅ **8 Monitoring Views** - Switch between views using SOURCE selection

### Remote Control (Remote Entity - Always Available)
- ✅ **6-Page Layout** - Navigation, Media, Windows, System Tools, Function Keys, Power
- ✅ **Windows Shortcuts** - Complete Win+key combinations and system controls
- ✅ **Media Controls** - Full transport controls for any media application
- ✅ **System Tools** - Built-in Windows applications and web services
- ✅ **Function Keys** - F1-F12 with dedicated shortcuts
- ✅ **Power Management** - Wake-on-LAN, Sleep, Hibernate, Shutdown, Restart
- ✅ **Custom App Launching** - Launch any Windows application via "Send Command"

### Advanced Features
- ✅ **Optional Hardware Monitoring** - Choose between full monitoring or remote control only
- ✅ **Wake-on-LAN Support** - Power on your HTPC remotely
- ✅ **Dynamic Source Switching** - 8 monitoring views accessible via SOURCE selection
- ✅ **Base64 Icon Embedding** - Offline operation with embedded icons
- ✅ **Real-time Updates** - 5-second monitoring refresh with efficient state management
- ✅ **Automatic Hardware Detection** - CPU, GPU, memory, storage, and network interfaces

---

## 📋 Requirements

### Hardware
- **Windows PC/HTPC** - Windows 10/11 system to control
- **Unfolded Circle Remote Two** or **Remote 3** (firmware 1.6.0+)
- **Network** - Both devices on same local network
- **Hardware Sensors** - Compatible motherboard with sensor chips (only if using hardware monitoring)

### Software (Required on Windows PC)

#### Always Required:
- **HTPC Agent** (Included) - [Download HTCP_Agent.exe](https://github.com/mase1981/uc-intg-htpc/blob/main/agents/HTCP_Agent.exe)

#### Optional (Only for Hardware Monitoring):
- **LibreHardwareMonitor** (Free) - [Download Latest Release](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases)

### Network Ports
- **Port 8086** - HTPC Agent communication (HTTP) - **Required**
- **Port 8085** - LibreHardwareMonitor web server (HTTP) - **Optional (only if hardware monitoring enabled)**
- **Port 9 (UDP)** - Wake-on-LAN (optional, if using WoL)

---

## 🚀 Installation

### Method 1: Remote Web Configurator (Recommended)

1. Download the latest `uc-intg-htpc-X.X.X-aarch64.tar.gz` from [Releases](https://github.com/mase1981/uc-intg-htpc/releases)
2. Open your Unfolded Circle **Web Configurator** (http://remote-ip/)
3. Navigate to **Integrations** → **Add Integration**
4. Click **Upload Driver**
5. Select the downloaded `.tar.gz` file
6. Follow the on-screen setup wizard

### Method 2: Docker Run (One-Line Command)
```bash
docker run -d --name uc-intg-htpc --restart unless-stopped --network host -v $(pwd)/data:/config -e UC_CONFIG_HOME=/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e UC_DISABLE_MDNS_PUBLISH=false ghcr.io/mase1981/uc-intg-htpc:latest
```

### Method 3: Docker Compose

Create a `docker-compose.yml` file:
```yaml
version: '3.8'

services:
  htpc-integration:
    image: ghcr.io/mase1981/uc-intg-htpc:latest
    container_name: uc-intg-htpc
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/config
    environment:
      - UC_CONFIG_HOME=/config
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_DISABLE_MDNS_PUBLISH=false
```

Then run:
```bash
docker-compose up -d
```

### Method 4: Python (Development)
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-htpc.git
cd uc-intg-htpc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run integration
python uc_intg_htpc/driver.py
```

---

## ⚙️ Configuration

### Step 1: Install HTPC Agent on Windows (Required)

1. **Download** [HTCP_Agent.exe](https://github.com/mase1981/uc-intg-htpc/blob/main/agents/HTCP_Agent.exe) from GitHub
2. **Right-click** → **Save As** → Place in permanent location (e.g., `C:\HTCP_Agent\`)
3. **Run** `HTCP_Agent.exe` - will appear in system tray
4. **Verify**: Check system tray for HTCP Agent icon
5. **Test**: Right-click tray icon → **Status & Control** → should open web interface

> 📖 **For detailed agent setup and troubleshooting**, see: [`agents/README_Agent.md`](agents/README_Agent.md)

### Step 2: Install LibreHardwareMonitor (Optional - Only if Using Hardware Monitoring)

**Skip this step if you only want remote control functionality.**

1. **Download** [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) from official GitHub releases
2. **Extract** to a permanent location (e.g., `C:\Program Files\LibreHardwareMonitor\`)
3. **Run as Administrator** (required for sensor access)
4. **Enable Web Server**:
   - Go to: **Options** → **Web Server**
   - Check: **☑ Run web server**
   - Port: **8085** (default)
   - Click: **OK**
5. **Verify**: Open browser to `http://localhost:8085/data.json` - should show sensor data

### Step 3: Configure Static IP (Recommended)

It's best to give your PC a static IP via your router DHCP reservation:

**Find Your HTCP IP Address:**
```bash
# Method 1: Command prompt
ipconfig

# Method 2: PowerShell
Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.IPAddress -like "192.168.*"}
```

**Test Connectivity:**
```bash
# Always test HTCP Agent:
http://YOUR_HTCP_IP:8086/status       # HTCP Agent (Required)

# Only if using hardware monitoring:
http://YOUR_HTCP_IP:8085/data.json    # LibreHardwareMonitor (Optional)
```

**Example**: If your HTCP IP is `192.168.1.100`:
- HTCP Agent: `http://192.168.1.100:8086/status`
- LibreHardwareMonitor: `http://192.168.1.100:8085/data.json` (only if monitoring enabled)

### Step 4: Integration Setup

During the integration setup wizard, you'll be presented with these options:

#### Required Settings:
- **HTPC IP Address** - Your Windows PC's IP address

#### Hardware Monitoring Dropdown:
Choose your operation mode:

| Option | Description | Requirements | Entities Created |
|--------|-------------|--------------|------------------|
| **Enabled (Requires LibreHardwareMonitor)** | Full system monitoring with real-time sensor data | LibreHardwareMonitor running on PC | Media Player + Remote |
| **Disabled (Remote Control Only)** | Lightweight Windows control without monitoring | HTPC Agent only | Remote only |

#### Optional Settings:
- **Temperature Unit** - Celsius or Fahrenheit (only relevant if monitoring enabled)
- **MAC Address** - For Wake-on-LAN functionality (see Step 5)

**Example Configurations:**

**Configuration 1 - Full Monitoring:**
```
HTPC IP Address: 192.168.1.100
Hardware Monitoring: Enabled (Requires LibreHardwareMonitor)
Temperature Unit: Celsius
MAC Address: 18-C0-4D-8F-29-06

Result: Creates both media player and remote entities
```

**Configuration 2 - Remote Control Only:**
```
HTPC IP Address: 192.168.1.100
Hardware Monitoring: Disabled (Remote Control Only)
Temperature Unit: (not used)
MAC Address: 18-C0-4D-8F-29-06

Result: Creates only remote entity (lightweight mode)
```

### Step 5: Enable Wake-on-LAN (Optional)

To enable remote power-on functionality:

#### On Windows PC:

1. **Find Your MAC Address:**
   ```bash
   # Method 1: Command Prompt
   ipconfig /all
   
   # Method 2: PowerShell
   Get-NetAdapter | Select-Object Name, MacAddress
   
   # Look for your active network adapter's "Physical Address"
   # Example: 18-C0-4D-8F-29-06
   ```

2. **Enable WoL in Network Adapter:**
   - Open **Device Manager** → **Network adapters**
   - Right-click your active adapter → **Properties**
   - **Power Management** tab:
     - ☑ Allow this device to wake the computer
     - ☑ Only allow a magic packet to wake the computer
   - **Advanced** tab:
     - Find "Wake on Magic Packet" → Set to **Enabled**
     - Find "Wake on pattern match" → Set to **Enabled**
   - Click **OK**

3. **Enable WoL in BIOS:**
   - Restart PC and enter BIOS/UEFI (usually Del, F2, or F12)
   - Find **Power Management** or **Advanced** settings
   - Look for options like:
     - "Wake on LAN" → **Enabled**
     - "Power On By PCI-E/PCI" → **Enabled**
     - "Resume by PCI or PCI-E Device" → **Enabled**
   - Save and exit BIOS

4. **Test WoL (Optional):**
   ```bash
   # From another device on the same network:
   # Linux/Mac:
   wakeonlan 18:C0:4D:8F:29:06
   
   # Windows (install WakeMeOnLan utility or use PowerShell script)
   ```

#### During Integration Setup:

1. When setting up the integration, you'll see a **MAC Address** field
2. Enter your PC's MAC address (e.g., `18-C0-4D-8F-29-06` or `18:C0:4D:8F:29:06`)
3. Both formats (hyphen or colon) are accepted
4. If you skip this field, WoL will not be available (you can reconfigure later)

**Result:** A **PowerOn** button will appear on the Power page of the remote entity.

---

## 🎮 Usage

### Entities Created

Entities created depend on your **Hardware Monitoring** setting during setup:

#### Operation Mode: Hardware Monitoring Enabled

Two entities are automatically created:

**1️⃣ HTPC System Monitor (Media Player Entity)**
- **Entity ID**: `htpc_monitor`
- **Type**: Media Player
- **Features:**
  - 8 monitoring views via **SELECT SOURCE**
  - Real-time sensor updates every 5 seconds
  - Power management (Sleep/Wake)
  - Volume control
  - System status display

**2️⃣ HTPC Advanced Remote (Remote Entity)**
- **Entity ID**: `htpc_remote`
- **Type**: Remote
- **Features:**
  - 6 custom UI pages with organized controls
  - Windows keyboard shortcuts and system commands
  - Media playback controls
  - Power management with Wake-on-LAN
  - Custom application launching

#### Operation Mode: Hardware Monitoring Disabled

One entity is created:

**1️⃣ HTPC Advanced Remote (Remote Entity)**
- **Entity ID**: `htpc_remote`
- **Type**: Remote
- **Features:** Same as above

### Source Selection Views (Media Player - Only in Monitoring Mode)

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

### Remote Control UI Pages

| Page | Purpose | Key Features |
|------|---------|--------------|
| **Navigation** | Directional controls | Arrow keys, Enter, Escape, Tab, Space |
| **Media Controls** | Media playback | Play/Pause, Stop, Volume, Transport controls |
| **Windows Shortcuts** | System navigation | Win+key combinations, Alt+Tab, Task Manager |
| **System Tools** | Applications | Calculator, Notepad, PowerShell, Web services |
| **Function Keys** | F1-F12 | Function keys with quick system shortcuts |
| **Power & System** | Power management | PowerOn (WoL), Sleep, Hibernate, PowerOff, Restart |

### Custom Application Launching

Use the **Send Command** feature in the Remote web configurator to launch any Windows application:

**Format**: `launch_exe:FULL_PATH_TO_EXECUTABLE`

**Examples:**
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
launch_exe:"C:\Program Files\Kodi\kodi.exe"
```

**URL Launching:**
```bash
# Launch websites
launch_url:https://www.netflix.com
launch_url:https://www.youtube.com
launch_url:https://app.plex.tv
launch_url:http://localhost:8096  # Jellyfin
```

**Finding Application Paths:**
```bash
# Method 1: Search in Start Menu
# Right-click application → "Open file location" → Properties → Copy path

# Method 2: Command Prompt
where chrome
where vlc

# Method 3: PowerShell
Get-Command chrome | Select-Object Source
```

### Switching Between Modes

You can reconfigure the integration at any time to switch between modes:

1. Open Remote web configurator
2. Navigate to **Integrations** → **HTPC System Monitor**
3. Click **Reconfigure**
4. Change **Hardware Monitoring** dropdown:
   - **Enabled** → Adds media player entity (requires LibreHardwareMonitor)
   - **Disabled** → Removes media player entity (remote only)
5. Complete reconfiguration

**Note:** When switching from "Disabled" to "Enabled", ensure LibreHardwareMonitor is running on your PC before reconfiguring.

### Adding to Activities

1. Create or edit an **Activity**
2. Add **HTPC System Monitor** as the main device (if monitoring enabled)
3. Add **HTPC Advanced Remote** for advanced controls
4. Map power commands
5. Configure macros for custom workflows

---

## 🔧 Troubleshooting

### Setup Issues

**Problem**: Integration setup fails with connection error (Hardware Monitoring Enabled)

**Solutions:**
1. ✅ Verify HTCP IP address with `ping YOUR_HTCP_IP`
2. ✅ Test LibreHardwareMonitor: `curl http://YOUR_HTCP_IP:8085/data.json`
3. ✅ Test HTCP Agent: `curl http://YOUR_HTCP_IP:8086/health`
4. ✅ Check Windows Firewall allows ports 8085 and 8086
5. ✅ Verify same network: Both devices must be on same subnet
6. ✅ Restart LibreHardwareMonitor and re-enable web server

**Problem**: Integration setup fails with connection error (Hardware Monitoring Disabled)

**Solutions:**
1. ✅ Test HTCP Agent: `curl http://YOUR_HTCP_IP:8086/health`
2. ✅ Check Windows Firewall allows port 8086
3. ✅ Verify HTCP Agent is running (check system tray)
4. ✅ Restart HTCP Agent

**Problem**: LibreHardwareMonitor shows no sensors

**Solutions:**
1. ✅ Run as Administrator (required for hardware sensor access)
2. ✅ Check motherboard compatibility - some systems have limited sensor support
3. ✅ Update motherboard drivers - ensure chipset drivers are current
4. ✅ Enable sensors in BIOS - some sensors may be disabled in BIOS

**Problem**: HTCP Agent not starting

**Solutions:**
1. ✅ Check antivirus - some antivirus may block the executable
2. ✅ Run as Administrator - may require elevated privileges
3. ✅ Check dependencies - ensure .NET runtime is installed
4. ✅ Firewall exceptions - add HTCP_Agent.exe to firewall exceptions

> 📖 **For detailed agent troubleshooting**, see: [`agents/README_Agent.md`](agents/README_Agent.md)

### Runtime Issues

**Problem**: System monitoring shows "Connection Error" (Monitoring Enabled mode)

**Solutions:**
1. ✅ Check network connectivity with ping test between devices
2. ✅ Verify services running - both LibreHardwareMonitor and HTCP Agent
3. ✅ Check IP address changes - HTCP may have received new IP via DHCP
4. ✅ Restart services - restart both LibreHardwareMonitor and HTCP Agent
5. ✅ Re-enable web server - in LibreHardwareMonitor, disable and re-enable web server

**Problem**: Remote commands not working

**Solutions:**
1. ✅ Test HTCP Agent: Check `http://HTCP_IP:8086/status`
2. ✅ Check command syntax: Verify proper `launch_exe:` format
3. ✅ Path validation: Ensure executable paths are correct and accessible
4. ✅ Permissions: Some applications may require administrator privileges

**Problem**: Missing temperature or fan data (Monitoring Enabled mode)

**Solutions:**
1. ✅ Hardware compatibility - not all systems support all sensors
2. ✅ Sensor availability - check LibreHardwareMonitor directly for available sensors
3. ✅ Administrative privileges - ensure LibreHardwareMonitor runs as administrator
4. ✅ Motherboard support - some sensors require specific motherboard chipsets

**Problem**: Wake-on-LAN not working

**Solutions:**
1. ✅ Verify WoL enabled in Windows network adapter settings
2. ✅ Verify WoL enabled in BIOS/UEFI settings
3. ✅ Check MAC address format - both `AA-BB-CC-DD-EE-FF` and `AA:BB:CC:DD:EE:FF` work
4. ✅ Test from command line first before blaming integration
5. ✅ Some network switches block WoL packets - test on simple network first
6. ✅ Computer must be connected to power (not just sleeping)

**Problem**: Want to switch between monitoring modes

**Solution:**
1. ✅ Open web configurator → Integrations → HTCP → Reconfigure
2. ✅ Change Hardware Monitoring dropdown to desired mode
3. ✅ If enabling monitoring, ensure LibreHardwareMonitor is running first
4. ✅ Complete reconfiguration - entities will be updated automatically

### Debug Information

**Enable detailed logging in HTCP Agent:**
- Check log file: `%USERPROFILE%\htcp_agent.log`
- System tray → Right-click → **View Log**

**Check integration status:**
```bash
# Via web configurator
http://YOUR_REMOTE_IP/configurator → Integrations → HTCP → Status
```

**Test LibreHardwareMonitor API (if monitoring enabled):**
```bash
# Device information
curl "http://HTCP_IP:8085/data.json"

# Web interface
http://HTCP_IP:8085
```

**Test HTCP Agent API (always):**
```bash
# Health check
curl "http://HTCP_IP:8086/health"

# Status page
http://HTCP_IP:8086/status

# Send test command
curl -X POST "http://HTCP_IP:8086/command" \
  -H "Content-Type: application/json" \
  -d '{"command": "custom_calc"}'
```

---

## ⚠️ Known Limitations

| Limitation | Explanation | Workaround |
|-----------|-------------|------------|
| **Sensor Availability** | Not all motherboards expose all sensors (monitoring mode only) | Use LibreHardwareMonitor directly to verify available sensors |
| **GPU Detection** | Only dedicated GPUs are detected (monitoring mode only) | Integrated graphics (Intel/AMD) not monitored separately |
| **Network Interface Selection** | Automatically detects most active interface | May need static IP if multiple active interfaces |
| **Power Consumption** | Only shows CPU package power if supported (monitoring mode only) | Requires modern Intel/AMD CPU with power reporting |
| **WoL Requirements** | Requires BIOS support and network adapter support | Check motherboard manual for WoL compatibility |
| **Mode Switching** | Requires reconfiguration to change monitoring mode | Quick reconfigure via web configurator |

---

## 🏗️ Architecture

### Integration Components
```
uc-intg-htpc/
├── uc_intg_htpc/
│   ├── icons/                # Base64-embedded monitoring icons
│   ├── __init__.py          # Package initialization with dynamic versioning
│   ├── client.py            # LibreHardwareMonitor & Agent client with WoL
│   ├── config.py            # Configuration management with optional monitoring
│   ├── driver.py            # Main integration driver with conditional entity creation
│   ├── media_player.py      # Media Player entity with 8 monitoring views (optional)
│   ├── remote.py            # Remote Control entity with 6 UI pages (always created)
│   └── setup.py             # Setup flow handler with mode selection
├── agents/
│   ├── HTCP_Agent.exe       # Windows agent for command execution
│   └── README_Agent.md      # Agent documentation
├── driver.json              # Integration metadata (source of truth for version)
├── pyproject.toml           # Python project configuration with dynamic version
├── requirements.txt         # Runtime dependencies
├── Dockerfile               # Docker image definition
├── docker-compose.yml       # Docker Compose configuration
├── LICENSE                  # MPL-2.0 license
└── README.md               # This file
```

### Dependencies

- **ucapi** (>=0.3.1) - Unfolded Circle Integration API
- **aiohttp** (>=3.8.0) - Async HTTP client
- **certifi** (>=2023.5.7) - SSL certificate verification
- **wakeonlan** (>=3.0.0) - Wake-on-LAN magic packet support

---

## 👨‍💻 Development

### Building From Source
```bash
# Clone repository
git clone https://github.com/mase1981/uc-intg-htpc.git
cd uc-intg-htpc

# Install in development mode
pip install -e ".[dev]"

# Run integration directly
python uc_intg_htpc/driver.py

# Build distribution package
python -m build

# Output: dist/uc-intg-htpc-X.X.X.tar.gz
```

### Release Process

```bash
# 1. Update version in driver.json
# Edit driver.json: "version": "0.2.4"

# 2. Commit changes
git add .
git commit -m "Release v0.2.4 - Add optional hardware monitoring"

# 3. Create and push tag
git tag v0.2.4
git push origin main
git push origin v0.2.4

# 4. GitHub Actions automatically:
#    - Builds aarch64 binary
#    - Creates Docker images (amd64 + arm64)
#    - Drafts release with artifacts
```

### Contributing

Contributions are welcome! Please follow these guidelines:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch (`git checkout -b feature/amazing-feature`)
3. 💾 Commit your changes (`git commit -m 'Add amazing feature'`)
4. 📤 Push to the branch (`git push origin feature/amazing-feature`)
5. 🎉 Open a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Add docstrings to functions and classes
- Keep line length to 120 characters
- Use Black for formatting

---

## 🙏 Credits & Acknowledgments

### Integration Development
- **Author**: [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

### Libraries & References
- **LibreHardwareMonitor**: [LibreHardwareMonitor/LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) - Hardware monitoring library
- **Unfolded Circle**: [Integration Python Library](https://github.com/unfoldedcircle/integration-python-library)

### Community
- **Unfolded Circle Community**: For testing and feedback
- **Home Theater PC Enthusiasts**: For feature requests and testing

---

## 💖 Support the Project

If you find this integration useful, please consider:

- ⭐ **Star this repository** on GitHub
- 🐛 **Report issues** to help improve the integration
- 💡 **Share feedback** in discussions
- 📖 **Contribute** documentation or code improvements

### Sponsor

If you'd like to support continued development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-Support-yellow?logo=buy-me-a-coffee)](https://www.buymeacoffee.com/meirmiyara)

---

## 📞 Support & Community

### Getting Help

- 📋 **Issues**: [GitHub Issues](https://github.com/mase1981/uc-intg-htpc/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/mase1981/uc-intg-htpc/discussions)
- 🌐 **UC Community**: [Unfolded Circle Forum](https://unfoldedcircle.com/community)

### Reporting Issues

When reporting issues, please include:

1. Integration version
2. Windows version
3. Operation mode (Hardware Monitoring Enabled/Disabled)
4. LibreHardwareMonitor version (if monitoring enabled)
5. UC Remote firmware version
6. Detailed description of the problem
7. Relevant log excerpts

---

## 📜 License

This project is licensed under the **Mozilla Public License 2.0** (MPL-2.0).

See the [LICENSE](LICENSE) file for full details.
```
Copyright (c) 2025 Meir Miyara

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
```

<div align="center">

**Transform your HTPC into a smart, monitored, and fully controllable entertainment center with your Remote Two/3!** 🎉

Made with ❤️ by [Meir Miyara](https://www.linkedin.com/in/meirmiyara/)

</div>