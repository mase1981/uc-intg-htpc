"""
LibreHardwareMonitor HTTP client for HTPC System Monitor Integration.

:copyright: (c) 2025 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import json
import logging
import ssl
import time
import re
from typing import Any, Dict, List, Optional

import aiohttp
import certifi

from uc_intg_htpc.config import HTCPConfig

_LOG = logging.getLogger(__name__)


class HTCPSystemData:
    """Container for parsed HTCP system data."""

    def __init__(self):
        """Initialize system data container."""
        self.cpu_temp: Optional[float] = None
        self.cpu_load: Optional[float] = None
        self.cpu_clock: Optional[float] = None
        self.gpu_temp: Optional[float] = None
        self.gpu_load: Optional[float] = None
        self.memory_used: Optional[float] = None
        self.memory_total: Optional[float] = None
        self.storage_used: Optional[float] = None
        self.storage_total: Optional[float] = None
        self.storage_used_percent: Optional[float] = None
        self.network_up: Optional[float] = None
        self.network_down: Optional[float] = None
        self.last_updated: float = time.time()
        
        self.motherboard_temp_avg: Optional[float] = None
        self.motherboard_temp_max: Optional[float] = None
        self.fan_speeds: List[float] = []
        self.cpu_power: Optional[float] = None
        self.storage_temp: Optional[float] = None
        
        self.has_dedicated_gpu: bool = False
        self.has_network_data: bool = False
        self.has_storage_data: bool = False
        self.detected_cpu_name: str = "CPU"
        self.detected_gpu_name: str = "GPU"
        self.detected_storage_name: str = "Storage"
        self.detected_network_name: str = "Network"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "cpu_temp": self.cpu_temp,
            "cpu_load": self.cpu_load,
            "cpu_clock": self.cpu_clock,
            "gpu_temp": self.gpu_temp,
            "gpu_load": self.gpu_load,
            "memory_used": self.memory_used,
            "memory_total": self.memory_total,
            "storage_used": self.storage_used,
            "storage_total": self.storage_total,
            "storage_used_percent": self.storage_used_percent,
            "network_up": self.network_up,
            "network_down": self.network_down,
            "last_updated": self.last_updated,
            "motherboard_temp_avg": self.motherboard_temp_avg,
            "motherboard_temp_max": self.motherboard_temp_max,
            "fan_speeds": self.fan_speeds,
            "cpu_power": self.cpu_power,
            "storage_temp": self.storage_temp,
            "has_dedicated_gpu": self.has_dedicated_gpu,
            "has_network_data": self.has_network_data,
            "has_storage_data": self.has_storage_data,
            "detected_cpu_name": self.detected_cpu_name,
            "detected_gpu_name": self.detected_gpu_name,
            "detected_storage_name": self.detected_storage_name,
            "detected_network_name": self.detected_network_name
        }


class HTCPClient:
    """HTTP client for LibreHardwareMonitor communication."""

    def __init__(self, config: HTCPConfig):
        """
        Initialize HTCP client.
        
        :param config: configuration instance
        """
        self._config = config
        self._session: Optional[aiohttp.ClientSession] = None
        self._system_data = HTCPSystemData()
        self._is_connected = False

    async def connect(self) -> bool:
        """
        Connect to LibreHardwareMonitor.
        
        :return: True if connected successfully
        """
        try:
            if self._session is None:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=10)
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector
                )

            await self._fetch_data()
            self._is_connected = True
            _LOG.info("Connected to LibreHardwareMonitor at %s", self._config.base_url)
            return True

        except Exception as ex:
            _LOG.error("Failed to connect to LibreHardwareMonitor: %s", ex)
            self._is_connected = False
            return False

    async def disconnect(self) -> None:
        """Disconnect from LibreHardwareMonitor."""
        if self._session:
            await self._session.close()
            self._session = None
        self._is_connected = False
        _LOG.info("Disconnected from LibreHardwareMonitor")

    async def _fetch_data(self) -> Dict[str, Any]:
        """
        Fetch raw JSON data from LibreHardwareMonitor.
        
        :return: raw JSON data
        :raises: aiohttp.ClientError if request fails
        """
        if not self._session:
            raise aiohttp.ClientError("Not connected")

        url = f"{self._config.base_url}/data.json"
        async with self._session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    def _parse_sensor_value(self, value_str: str) -> Optional[float]:
        """
        Parse sensor value from string format.
        
        :param value_str: sensor value string
        :return: parsed float value or None
        """
        try:
            parts = value_str.split()
            if parts:
                return float(parts[0])
        except (ValueError, IndexError):
            pass
        return None

    def _find_sensor_by_text(self, hardware: Dict[str, Any], target_texts: List[str]) -> Optional[float]:
        """
        Find a sensor by matching text patterns.
        
        :param hardware: hardware node from JSON
        :param target_texts: list of text patterns to match
        :return: sensor value or None if not found
        """
        for sensor_group in hardware.get("Children", []):
            for sensor in sensor_group.get("Children", []):
                sensor_text = sensor.get("Text", "").lower()
                for target in target_texts:
                    if target.lower() in sensor_text:
                        value = self._parse_sensor_value(sensor.get("Value", ""))
                        if value is not None:
                            return value
        return None

    def _detect_cpu_hardware(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect CPU hardware dynamically."""
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if any(keyword in component_text for keyword in ["intel", "amd", "processor", "core", "ryzen", "cpu"]):
                    if not any(gpu_keyword in component_text for gpu_keyword in ["graphics", "radeon", "geforce", "gpu"]):
                        self._system_data.detected_cpu_name = component.get("Text", "CPU")
                        return component
        return None

    def _detect_gpu_hardware(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect dedicated GPU hardware dynamically."""
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if any(keyword in component_text for keyword in ["nvidia", "amd", "radeon", "geforce", "rtx", "gtx", "rx"]):
                    if not any(integrated in component_text for integrated in ["uhd", "integrated", "igpu"]):
                        self._system_data.detected_gpu_name = component.get("Text", "GPU")
                        self._system_data.has_dedicated_gpu = True
                        return component
        return None

    def _detect_memory_hardware(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect memory hardware dynamically."""
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if "memory" in component_text and "cpu" not in component_text:
                    return component
        return None

    def _detect_storage_hardware(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect primary storage hardware dynamically."""
        storage_devices = []
        
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if any(keyword in component_text for keyword in ["ssd", "hdd", "nvme", "samsung", "wd", "crucial", "seagate", "toshiba", "kingston"]):
                    used_space = self._find_sensor_by_text(component, ["used space"])
                    if used_space is not None:
                        storage_devices.append({
                            "component": component,
                            "name": component.get("Text", "Storage"),
                            "used_percent": used_space
                        })
        
        if storage_devices:
            primary_storage = max(storage_devices, key=lambda x: x["used_percent"])
            self._system_data.detected_storage_name = primary_storage["name"]
            self._system_data.has_storage_data = True
            return primary_storage["component"]
        
        return None

    def _detect_active_network_interface(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect the active network interface dynamically."""
        interfaces = []
        
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if any(keyword in component_text for keyword in ["ethernet", "wifi", "wireless", "network"]):
                    if not any(virtual in component_text for virtual in ["vethernet", "virtual", "loopback"]):
                        upload_speed = self._find_sensor_by_text(component, ["upload speed"])
                        download_speed = self._find_sensor_by_text(component, ["download speed"])
                        utilization = self._find_sensor_by_text(component, ["network utilization"])
                        
                        activity_score = 0
                        if upload_speed and upload_speed > 0:
                            activity_score += upload_speed
                        if download_speed and download_speed > 0:
                            activity_score += download_speed * 10
                        if utilization and utilization > 0:
                            activity_score += utilization
                        
                        interfaces.append({
                            "component": component,
                            "name": component.get("Text", "Network"),
                            "activity": activity_score
                        })
        
        if interfaces:
            active_interfaces = [iface for iface in interfaces if iface["activity"] > 0]
            if active_interfaces:
                primary_interface = max(active_interfaces, key=lambda x: x["activity"])
            else:
                ethernet_interfaces = [iface for iface in interfaces if "ethernet" in iface["name"].lower()]
                primary_interface = ethernet_interfaces[0] if ethernet_interfaces else interfaces[0]
            
            self._system_data.detected_network_name = primary_interface["name"]
            self._system_data.has_network_data = True
            return primary_interface["component"]
        
        return None

    def _detect_motherboard_hardware(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Detect motherboard hardware for temperature and fan sensors."""
        for hardware in data.get("Children", []):
            for component in hardware.get("Children", []):
                component_text = component.get("Text", "").lower()
                
                if any(keyword in component_text for keyword in ["z590", "b550", "x570", "asus", "gigabyte", "msi", "asrock", "it8689", "nct"]):
                    return component
        return None

    def _extract_storage_size_from_name(self, hardware_name: str) -> Optional[float]:
        """Extract storage size from hardware name."""
        try:
            size_patterns = [
                r'(\d+(?:\.\d+)?)\s*TB',
                r'(\d+(?:\.\d+)?)\s*GB',
                r'(\d+(?:\.\d+)?)\s*tb',
                r'(\d+(?:\.\d+)?)\s*gb'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, hardware_name, re.IGNORECASE)
                if match:
                    size_value = float(match.group(1))
                    if 'tb' in pattern.lower():
                        size_value *= 1000
                    return size_value
        except:
            pass
        return None

    def _parse_cpu_data(self, cpu_hardware: Dict[str, Any]) -> None:
        """Parse CPU sensor data."""
        cpu_temp = self._find_sensor_by_text(cpu_hardware, [
            "core average", "cpu package", "package", "tctl", "tdie"
        ])
        if cpu_temp:
            self._system_data.cpu_temp = cpu_temp
        
        cpu_load = self._find_sensor_by_text(cpu_hardware, [
            "cpu total", "total", "cpu usage", "processor usage"
        ])
        if cpu_load:
            self._system_data.cpu_load = cpu_load
            
        clocks = []
        for sensor_group in cpu_hardware.get("Children", []):
            group_text = sensor_group.get("Text", "").lower()
            if "clocks" in group_text or "frequencies" in group_text:
                for sensor in sensor_group.get("Children", []):
                    sensor_text = sensor.get("Text", "").lower()
                    if any(core_indicator in sensor_text for core_indicator in ["core", "cpu"]) and "bus" not in sensor_text:
                        clock = self._parse_sensor_value(sensor.get("Value", ""))
                        if clock is not None and clock > 100:
                            clocks.append(clock)
        
        if clocks:
            self._system_data.cpu_clock = sum(clocks) / len(clocks)

    def _parse_gpu_data(self, gpu_hardware: Dict[str, Any]) -> None:
        """Parse GPU sensor data."""
        gpu_temp = self._find_sensor_by_text(gpu_hardware, [
            "gpu core", "gpu", "core", "temperature"
        ])
        if gpu_temp:
            self._system_data.gpu_temp = gpu_temp
            
        gpu_load = self._find_sensor_by_text(gpu_hardware, [
            "gpu core", "gpu", "core load", "3d load", "cuda load"
        ])
        if gpu_load:
            self._system_data.gpu_load = gpu_load

    def _parse_memory_data(self, memory_hardware: Dict[str, Any]) -> None:
        """Parse memory sensor data."""
        memory_used = self._find_sensor_by_text(memory_hardware, ["memory used", "used"])
        memory_available = self._find_sensor_by_text(memory_hardware, ["memory available", "available"])
        
        if memory_used:
            self._system_data.memory_used = memory_used
            
        if memory_used and memory_available:
            self._system_data.memory_total = memory_used + memory_available

    def _parse_storage_data(self, storage_hardware: Dict[str, Any]) -> None:
        """Parse storage sensor data."""
        used_percent = self._find_sensor_by_text(storage_hardware, ["used space", "usage"])
        if used_percent:
            self._system_data.storage_used_percent = used_percent
            
            hardware_name = storage_hardware.get("Text", "")
            total_size = self._extract_storage_size_from_name(hardware_name)
            
            if total_size:
                self._system_data.storage_total = total_size
                self._system_data.storage_used = (used_percent / 100) * total_size

    def _parse_network_data(self, network_hardware: Dict[str, Any]) -> None:
        """Parse network sensor data."""
        upload_speed = self._find_sensor_by_text(network_hardware, ["upload speed", "tx", "sent"])
        if upload_speed is not None:
            is_megabytes = False
            for sensor_group in network_hardware.get("Children", []):
                for sensor in sensor_group.get("Children", []):
                    if any(term in sensor.get("Text", "").lower() for term in ["upload", "tx", "sent"]):
                        value_str = sensor.get("Value", "")
                        if "MB/s" in value_str or "Mbps" in value_str:
                            is_megabytes = True
                        break
            
            if is_megabytes:
                self._system_data.network_up = upload_speed * 8
            else:
                self._system_data.network_up = upload_speed / 125
            
        download_speed = self._find_sensor_by_text(network_hardware, ["download speed", "rx", "received"])
        if download_speed is not None:
            is_megabytes = False
            for sensor_group in network_hardware.get("Children", []):
                for sensor in sensor_group.get("Children", []):
                    if any(term in sensor.get("Text", "").lower() for term in ["download", "rx", "received"]):
                        value_str = sensor.get("Value", "")
                        if "MB/s" in value_str or "Mbps" in value_str:
                            is_megabytes = True
                        break
            
            if is_megabytes:
                self._system_data.network_down = download_speed * 8
            else:
                self._system_data.network_down = download_speed / 125

    def _parse_motherboard_data(self, motherboard_hardware: Dict[str, Any]) -> None:
        """Parse motherboard sensor data for temperatures and fans."""
        temperatures = []
        fan_speeds = []
        
        for chip in motherboard_hardware.get("Children", []):
            chip_text = chip.get("Text", "").lower()
            
            if any(chip_type in chip_text for chip_type in ["ite", "nct", "super i/o"]):
                for sensor_group in chip.get("Children", []):
                    group_text = sensor_group.get("Text", "").lower()
                    
                    if "temperatures" in group_text:
                        for sensor in sensor_group.get("Children", []):
                            temp = self._parse_sensor_value(sensor.get("Value", ""))
                            if temp is not None and 20 < temp < 100:
                                temperatures.append(temp)
                    
                    elif "fans" in group_text:
                        for sensor in sensor_group.get("Children", []):
                            fan_speed = self._parse_sensor_value(sensor.get("Value", ""))
                            if fan_speed is not None and fan_speed > 0:
                                fan_speeds.append(fan_speed)
        
        if temperatures:
            self._system_data.motherboard_temp_avg = sum(temperatures) / len(temperatures)
            self._system_data.motherboard_temp_max = max(temperatures)
        
        if fan_speeds:
            self._system_data.fan_speeds = fan_speeds

    def _parse_cpu_power_data(self, cpu_hardware: Dict[str, Any]) -> None:
        """Parse CPU power consumption data."""
        cpu_power = self._find_sensor_by_text(cpu_hardware, ["cpu package", "package power", "cpu power"])
        if cpu_power:
            self._system_data.cpu_power = cpu_power

    def _parse_storage_temperature(self, storage_hardware: Dict[str, Any]) -> None:
        """Parse storage temperature data."""
        storage_temp = self._find_sensor_by_text(storage_hardware, ["temperature"])
        if storage_temp:
            self._system_data.storage_temp = storage_temp

    async def update_system_data(self) -> bool:
        """
        Update system data from LibreHardwareMonitor.
        
        :return: True if update successful
        """
        try:
            raw_data = await self._fetch_data()
            
            old_data = self._system_data
            self._system_data = HTCPSystemData()
            
            if old_data.last_updated > 0:
                self._system_data.has_dedicated_gpu = old_data.has_dedicated_gpu
                self._system_data.has_network_data = old_data.has_network_data
                self._system_data.has_storage_data = old_data.has_storage_data
                self._system_data.detected_cpu_name = old_data.detected_cpu_name
                self._system_data.detected_gpu_name = old_data.detected_gpu_name
                self._system_data.detected_storage_name = old_data.detected_storage_name
                self._system_data.detected_network_name = old_data.detected_network_name
            
            if "Children" in raw_data:
                cpu_hardware = self._detect_cpu_hardware(raw_data)
                if cpu_hardware:
                    self._parse_cpu_data(cpu_hardware)
                    self._parse_cpu_power_data(cpu_hardware)
                
                gpu_hardware = self._detect_gpu_hardware(raw_data)
                if gpu_hardware:
                    self._parse_gpu_data(gpu_hardware)
                
                memory_hardware = self._detect_memory_hardware(raw_data)
                if memory_hardware:
                    self._parse_memory_data(memory_hardware)
                
                storage_hardware = self._detect_storage_hardware(raw_data)
                if storage_hardware:
                    self._parse_storage_data(storage_hardware)
                    self._parse_storage_temperature(storage_hardware)
                
                network_hardware = self._detect_active_network_interface(raw_data)
                if network_hardware:
                    self._parse_network_data(network_hardware)
                
                motherboard_hardware = self._detect_motherboard_hardware(raw_data)
                if motherboard_hardware:
                    self._parse_motherboard_data(motherboard_hardware)
            
            self._system_data.last_updated = time.time()
            _LOG.debug("System data updated successfully")
            return True
            
        except Exception as ex:
            _LOG.error("Failed to update system data: %s", ex)
            self._is_connected = False
            return False

    async def send_remote_command(self, command: str) -> bool:
        """
        Send a remote command to the Windows agent.
        
        :param command: command to send
        :return: True if successful
        """
        try:
            agent_url = f"http://{self._config.host}:8086/command"
            
            if not self._session:
                ssl_context = ssl.create_default_context(cafile=certifi.where())
                connector = aiohttp.TCPConnector(ssl=ssl_context)
                timeout = aiohttp.ClientTimeout(total=10)
                self._session = aiohttp.ClientSession(
                    timeout=timeout,
                    connector=connector
                )
            
            async with self._session.post(agent_url, json={"command": command}) as response:
                if response.status == 200:
                    result = await response.json()
                    _LOG.info(f"Remote command '{command}' executed successfully: {result}")
                    return True
                else:
                    _LOG.error(f"Remote command '{command}' failed with status {response.status}")
                    return False
                    
        except Exception as ex:
            _LOG.error(f"Failed to send remote command '{command}': {ex}")
            return False

    async def launch_application(self, app_name: str) -> bool:
        """
        Launch application on HTPC.
        
        :param app_name: name of application to launch
        :return: True if launched successfully
        """
        return await self.send_remote_command(f"app_{app_name}")

    async def set_volume(self, volume: int) -> bool:
        """
        Set system volume on HTPC.
        
        :param volume: volume level (0-100)
        :return: True if successful
        """
        return await self.send_remote_command(f"set_volume:{volume}")

    async def mute_toggle(self) -> bool:
        """
        Toggle mute on HTPC.
        
        :return: True if successful
        """
        return await self.send_remote_command("mute_toggle")

    async def power_sleep(self) -> bool:
        """
        Put HTPC to sleep.
        
        :return: True if successful
        """
        return await self.send_remote_command("power_sleep")

    async def power_wake(self) -> bool:
        """
        Wake HTPC from sleep.
        
        :return: True if successful
        """
        return await self.send_remote_command("power_wake")

    @property
    def is_connected(self) -> bool:
        """Check if connected to LibreHardwareMonitor."""
        return self._is_connected

    @property
    def system_data(self) -> HTCPSystemData:
        """Get current system data."""
        return self._system_data