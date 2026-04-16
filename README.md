# HTPC System Monitor Integration for Unfolded Circle Remote 2/3

Transform your Unfolded Circle Remote into a powerful HTPC command center with real-time system monitoring and comprehensive Windows control.

![htpc](https://img.shields.io/badge/htpc-monitor-blue)
[![GitHub Release](https://img.shields.io/github/v/release/mase1981/uc-intg-htpc?style=flat-square)](https://github.com/mase1981/uc-intg-htpc/releases)
![License](https://img.shields.io/badge/license-MPL--2.0-blue?style=flat-square)
[![GitHub issues](https://img.shields.io/github/issues/mase1981/uc-intg-htpc?style=flat-square)](https://github.com/mase1981/uc-intg-htpc/issues)
[![Community Forum](https://img.shields.io/badge/community-forum-blue?style=flat-square)](https://unfolded.community/)
[![Discord](https://badgen.net/discord/online-members/zGVYf58)](https://discord.gg/zGVYf58)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/mase1981/uc-intg-htpc/total?style=flat-square)
[![Buy Me A Coffee](https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=flat-square)](https://buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-donate-blue.svg?style=flat-square)](https://paypal.me/mmiyara)
[![Github Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-30363D?&logo=GitHub-Sponsors&logoColor=EA4AAA&style=flat-square)](https://github.com/sponsors/mase1981)


## Features

Monitor CPU, GPU, memory, storage, network, temperatures, and fan speeds while controlling your Windows HTPC through remote control, media playback, and system management—all from your Unfolded Circle Remote Two/3.

---
## ❤️ Support Development ❤️

If you find this integration useful, consider supporting development:

[![GitHub Sponsors](https://img.shields.io/badge/Sponsor-GitHub-pink?style=for-the-badge&logo=github)](https://github.com/sponsors/mase1981)
[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-FFDD00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://www.buymeacoffee.com/meirmiyara)
[![PayPal](https://img.shields.io/badge/PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/mmiyara)

Your support helps maintain this integration. Thank you! ❤️
---

### 🎛️ **Flexible Operation Modes**

Choose your setup based on your needs:

- **Full Monitoring + Control** - Complete system monitoring with media player entity + remote control
- **Remote Control Only** - Lightweight Windows control without hardware monitoring requirements

### 📊 **System Monitoring** (Media Player + Sensor Entities - Optional)

#### **Dynamic Hardware Discovery**
Hardware is automatically detected using LibreHardwareMonitor's HardwareId system — no manual configuration needed. Works with any CPU (Intel/AMD), any GPU (NVIDIA/AMD/Intel Arc), any storage, and any network adapter.

#### **9 Monitoring Views** (Media Player Entity)
Switch between views using SOURCE selection:
- **System Overview** - CPU temp/load, CPU power, Memory usage
- **CPU Performance** - Temperature, Load percentage, Clock speed
- **GPU Performance** - GPU temperature and load (if dedicated GPU)
- **Memory Usage** - Used/Total memory with percentage
- **Storage Activity** - Used/Total storage with usage percentage
- **Network Activity** - Upload/Download speeds
- **Temperature Overview** - CPU, Storage, Motherboard temperatures
- **Fan Monitoring** - Active fans count, Average/Maximum speeds
- **Power Consumption** - CPU package power draw

#### **10 Sensor Entities**
Individual sensors available for automations and dashboard display:
- CPU Temperature, CPU Load, CPU Power
- GPU Temperature, GPU Load
- Memory Usage, Storage Usage
- Network Download, Network Upload
- Fan Speed

### 🎮 **Remote Control** (Remote Entity - Always Available)

#### **6-Page Layout**
- **Navigation** - Directional controls, arrow keys, Enter, Escape, Tab, Space
- **Media Controls** - Play/Pause, Stop, Volume, Transport controls
- **Windows Shortcuts** - Win+key combinations, Alt+Tab, Task Manager
- **System Tools** - Calculator, Notepad, PowerShell, Web services
- **Function Keys** - F1-F12 with dedicated shortcuts
- **Power & System** - PowerOn (WoL), Sleep, Hibernate, PowerOff, Restart

#### **Advanced Features**
- **Complete Button Mapping** - All Windows keyboard shortcuts and system commands
- **Media Playback** - Full transport controls for any media application
- **Custom App Launching** - Launch any Windows application via "Send Command"
- **Wake-on-LAN Support** - Power on your HTPC remotely

### **Protocol Requirements**

- **HTPC Agent** - Required Windows agent for command execution (included)
- **LibreHardwareMonitor** - Optional for hardware monitoring (free download)
- **Network Ports** - Port 8086 (Agent, required), Port 8085 (LibreHardwareMonitor, optional)
- **Wake-on-LAN** - Port 9 UDP (optional, if using WoL)

### **Network Requirements**

- **Local Network Access** - Integration requires same network as Windows PC
- **Static IP Recommended** - PC should have static IP or DHCP reservation
- **Firewall** - Must allow traffic on required ports
- **Network Isolation** - Must be on same subnet as Remote

## Installation

### Option 1: Remote Web Interface (Recommended)
1. Navigate to the [**Releases**](https://github.com/mase1981/uc-intg-htpc/releases) page
2. Download the latest `uc-intg-htpc-<version>-aarch64.tar.gz` file
3. Open your remote's web interface (`http://your-remote-ip`)
4. Go to **Settings** → **Integrations** → **Add Integration**
5. Click **Upload** and select the downloaded `.tar.gz` file

### Option 2: Docker (Advanced Users)

The integration is available as a pre-built Docker image from GitHub Container Registry:

**Image**: `ghcr.io/mase1981/uc-intg-htpc:latest`

**Docker Compose:**
```yaml
services:
  uc-intg-htpc:
    image: ghcr.io/mase1981/uc-intg-htpc:latest
    container_name: uc-intg-htpc
    network_mode: host
    volumes:
      - </local/path>:/data
    environment:
      - UC_CONFIG_HOME=/data
      - UC_INTEGRATION_HTTP_PORT=9090
      - UC_INTEGRATION_INTERFACE=0.0.0.0
      - PYTHONPATH=/app
    restart: unless-stopped
```

**Docker Run:**
```bash
docker run -d --name uc-htpc --restart unless-stopped --network host -v htpc-config:/app/config -e UC_CONFIG_HOME=/app/config -e UC_INTEGRATION_INTERFACE=0.0.0.0 -e UC_INTEGRATION_HTTP_PORT=9090 -e PYTHONPATH=/app ghcr.io/mase1981/uc-intg-htpc:latest
```

## Configuration

### Step 1: Install HTPC Agent on Windows (Required)

**IMPORTANT**: HTPC Agent must be running on your Windows PC before configuring the integration.

1. Download [HTPC_Agent.exe](https://github.com/mase1981/uc-intg-htpc/blob/main/agents/HTPC_Agent.exe) from GitHub
2. Right-click → Save As → Place in permanent location (e.g., `C:\HTPC_Agent\`)
3. Run `HTPC_Agent.exe` - will appear in system tray
4. Verify - Check system tray for HTPC Agent icon
5. Test - Right-click tray icon → Status & Control → should open web interface

For detailed agent setup and troubleshooting, see: [`agents/README_Agent.md`](agents/README_Agent.md)

### Step 2: Install LibreHardwareMonitor (Optional - Only for Hardware Monitoring)

**Skip this step if you only want remote control functionality.**

1. Download [LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor/releases) from official GitHub releases
2. Extract to permanent location (e.g., `C:\Program Files\LibreHardwareMonitor\`)
3. Run as Administrator (required for sensor access)
4. Enable Web Server:
   - Go to: Options → Web Server
   - Check: Run web server
   - Port: 8085 (default)
   - Click: OK
5. Verify - Open browser to `http://localhost:8085/data.json` - should show sensor data

#### Network Setup:
- **Wired Connection** - Recommended for stability
- **Static IP** - Recommended via DHCP reservation
- **Firewall** - Allow traffic on ports 8086 (required) and 8085 (optional)
- **Network Isolation** - Must be on same subnet as Remote

### Step 3: Setup Integration

1. After installation, go to **Settings** → **Integrations**
2. The HTPC integration should appear in **Available Integrations**
3. Click **"Configure"** to begin setup:

#### **Configuration:**
- **HTPC IP Address** - Your Windows PC's IP address
- **Hardware Monitoring** - Choose operation mode:
  - **Enabled (Requires LibreHardwareMonitor)** - Full system monitoring with real-time sensor data
  - **Disabled (Remote Control Only)** - Lightweight Windows control without monitoring
- **Temperature Unit** - Celsius or Fahrenheit (only relevant if monitoring enabled)
- **MAC Address** - For Wake-on-LAN functionality (optional)
- Click **Submit**

#### **Connection Test:**
- Integration verifies connectivity to HTPC Agent (required)
- If monitoring enabled, also verifies LibreHardwareMonitor connectivity
- Setup fails if required services unreachable

4. Integration will create entities:
   - **HTPC Remote** - Remote entity (always created)
   - **HTPC System Monitor** - Media player entity (only if monitoring enabled)
   - **10 Sensor Entities** - CPU, GPU, Memory, Storage, Network, Fan sensors (only if monitoring enabled)

### Step 4: Enable Wake-on-LAN (Optional)

To enable remote power-on functionality:

#### On Windows PC:

1. **Find Your MAC Address:**
   ```bash
   ipconfig /all
   # Look for "Physical Address" of your active network adapter
   # Example: 18-C0-4D-8F-29-06
   ```

2. **Enable WoL in Network Adapter:**
   - Open Device Manager → Network adapters
   - Right-click adapter → Properties
   - Power Management tab:
     - ☑ Allow this device to wake the computer
     - ☑ Only allow a magic packet to wake the computer
   - Advanced tab:
     - Set "Wake on Magic Packet" → Enabled
   - Click OK

3. **Enable WoL in BIOS:**
   - Enter BIOS/UEFI (usually Del, F2, or F12)
   - Find Power Management settings
   - Enable "Wake on LAN" or "Power On By PCI-E/PCI"
   - Save and exit

4. During Integration Setup:
   - Enter MAC address in configuration (e.g., `18-C0-4D-8F-29-06`)
   - Both formats (hyphen or colon) accepted
   - PowerOn button will appear on Power page of remote entity

## Using the Integration

### Media Player Entity (Only in Monitoring Mode)

The media player entity provides system monitoring:

- **9 Monitoring Views** - Switch via SOURCE selection
- **Real-time Updates** - 5-second monitoring refresh
- **Power Management** - Sleep/Wake controls
- **Volume Control** - System volume adjustment
- **System Status** - Current system state display

### Sensor Entities (Only in Monitoring Mode)

10 individual sensor entities for automations and dashboard widgets:

- **CPU** - Temperature, Load (%), Power (W)
- **GPU** - Temperature, Load (%)
- **Memory** - Usage (%)
- **Storage** - Usage (%)
- **Network** - Download (Mbps), Upload (Mbps)
- **Fans** - Average Speed (RPM)

### Remote Control Entity (Always Available)

The remote entity provides comprehensive Windows control:

- **6 Custom UI Pages** - Organized controls for different functions
- **Windows Shortcuts** - Complete Win+key combinations
- **Media Playback** - Transport controls for any media app
- **System Tools** - Quick access to Calculator, Notepad, PowerShell
- **Power Management** - Wake-on-LAN, Sleep, Hibernate, Shutdown, Restart
- **Custom Applications** - Launch any Windows app via "Send Command"

### Custom Application Launching

#### Option 1: Shortcuts (Recommended)

Launch any application using Windows shortcut files (`.lnk`). This avoids the 20-character command name limit.

**Setup:**
1. Create a `shortcuts` folder next to `HTPC_Agent.exe` (e.g., `C:\HTPC_Agent\shortcuts\`)
2. Create or copy Windows shortcuts into this folder (right-click → New → Shortcut, or copy existing `.lnk` files)
3. Name the shortcut file with a short name, e.g., `Chrome.lnk`, `Plex.lnk`, `Steam.lnk`

**Usage:**
- In the Remote's **Send Command** widget, type the shortcut name **without** `.lnk`
- Example: type `Chrome` to launch `shortcuts\Chrome.lnk`

**Examples:**
| Shortcut File | Send Command | Launches |
|---|---|---|
| `Chrome.lnk` | `Chrome` | Google Chrome |
| `Steam.lnk` | `Steam` | Steam |
| `Plex.lnk` | `Plex` | Plex Desktop |
| `VLC.lnk` | `VLC` | VLC Media Player |

> **Note:** Requires HTPC Agent v3.0.0 or later.

#### Option 2: Direct Launch Commands

Use the **Send Command** feature with full paths (limited to 20 characters):

**Format**: `launch_exe:PATH` or `launch_url:URL`

**Examples:**
```
launch_url:netflix.com
launch_url:youtube.com
```

### Switching Between Modes

You can reconfigure the integration at any time to switch between modes:

1. Open Remote web configurator
2. Navigate to Integrations → HTPC System Monitor
3. Click Reconfigure
4. Change Hardware Monitoring dropdown
5. Complete reconfiguration - entities will be updated automatically

## Credits

- **Developer** - Meir Miyara
- **LibreHardwareMonitor** - [LibreHardwareMonitor/LibreHardwareMonitor](https://github.com/LibreHardwareMonitor/LibreHardwareMonitor) - Hardware monitoring library
- **Unfolded Circle** - Remote 2/3 integration framework (ucapi)
- **Community** - Testing and feedback from UC community

## License

This project is licensed under the Mozilla Public License 2.0 (MPL-2.0) - see LICENSE file for details.

## Support & Community

- **GitHub Issues** - [Report bugs and request features](https://github.com/mase1981/uc-intg-htpc/issues)
- **UC Community Forum** - [General discussion and support](https://unfolded.community/)
- **Developer** - [Meir Miyara](https://www.linkedin.com/in/meirmiyara)

---

**Made with ❤️ for the Unfolded Circle Community**

**Thank You** - Meir Miyara
