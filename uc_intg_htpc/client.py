"""
LibreHardwareMonitor and HTPC Agent HTTP client.

:copyright: (c) 2026 by Meir Miyara.
:license: MPL-2.0, see LICENSE for more details.
"""

import asyncio
import logging
import re
import time
from typing import Any

import aiohttp
from wakeonlan import send_magic_packet

from uc_intg_htpc.config import HTCPConfig
from uc_intg_htpc.const import AGENT_PORT

_LOG = logging.getLogger(__name__)


class SystemData:
    """Parsed hardware sensor data from LibreHardwareMonitor."""

    def __init__(self) -> None:
        self.cpu_temp: float | None = None
        self.cpu_load: float | None = None
        self.cpu_clock: float | None = None
        self.cpu_power: float | None = None
        self.gpu_temp: float | None = None
        self.gpu_load: float | None = None
        self.memory_used: float | None = None
        self.memory_total: float | None = None
        self.storage_used: float | None = None
        self.storage_total: float | None = None
        self.storage_used_percent: float | None = None
        self.storage_temp: float | None = None
        self.network_up: float | None = None
        self.network_down: float | None = None
        self.motherboard_temp_avg: float | None = None
        self.motherboard_temp_max: float | None = None
        self.fan_speeds: list[float] = []
        self.has_dedicated_gpu: bool = False
        self.detected_cpu_name: str = "CPU"
        self.detected_gpu_name: str = "GPU"
        self.last_updated: float = 0.0


class HTCPClient:
    """Client for LibreHardwareMonitor data and HTPC Agent commands."""

    def __init__(self, config: HTCPConfig) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None
        self._system_data = SystemData()

    @property
    def system_data(self) -> SystemData:
        return self._system_data

    async def connect(self) -> bool:
        if not self._session:
            connector = aiohttp.TCPConnector(limit=3)
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10, connect=5),
                connector=connector,
            )
        if self._config.enable_hardware_monitoring:
            return await self.update_system_data()
        return await self.test_agent()

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def test_agent(self) -> bool:
        session = self._session
        close_after = False
        if not session:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))
            close_after = True
        try:
            url = f"http://{self._config.host}:{AGENT_PORT}/health"
            async with session.get(url) as resp:
                return resp.status == 200
        except Exception:
            return False
        finally:
            if close_after:
                await session.close()

    async def test_lhm(self) -> dict[str, Any]:
        session = self._session
        close_after = False
        if not session:
            session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))
            close_after = True
        try:
            url = f"http://{self._config.host}:{self._config.port}/data.json"
            async with session.get(url) as resp:
                if resp.status != 200:
                    return {"success": False, "error": f"HTTP {resp.status}"}
                data = await resp.json()
                count = self._count_sensors(data)
                return {"success": True, "sensor_count": count}
        except aiohttp.ClientConnectorError:
            return {"success": False, "error": f"Connection refused at {self._config.host}:{self._config.port}"}
        except Exception as err:
            return {"success": False, "error": str(err)}
        finally:
            if close_after:
                await session.close()

    async def update_system_data(self) -> bool:
        if not self._session:
            return False
        try:
            url = f"http://{self._config.host}:{self._config.port}/data.json"
            async with self._session.get(url) as resp:
                resp.raise_for_status()
                raw = await resp.json()
        except Exception as err:
            _LOG.debug("LHM fetch failed: %s", err)
            return False

        old = self._system_data
        sd = SystemData()
        sd.has_dedicated_gpu = old.has_dedicated_gpu
        sd.detected_cpu_name = old.detected_cpu_name
        sd.detected_gpu_name = old.detected_gpu_name

        if "Children" in raw:
            cpu = self._detect_cpu(raw)
            if cpu:
                sd.detected_cpu_name = cpu.get("Text", "CPU")
                self._parse_cpu(cpu, sd)

            gpu = self._detect_gpu(raw)
            if gpu:
                sd.detected_gpu_name = gpu.get("Text", "GPU")
                sd.has_dedicated_gpu = True
                self._parse_gpu(gpu, sd)

            mem = self._detect_memory(raw)
            if mem:
                self._parse_memory(mem, sd)

            storage = self._detect_storage(raw)
            if storage:
                self._parse_storage(storage, sd)

            net = self._detect_network(raw)
            if net:
                self._parse_network(net, sd)

            mb = self._detect_motherboard(raw)
            if mb:
                self._parse_motherboard(mb, sd)

        sd.last_updated = time.time()
        self._system_data = sd
        return True

    FIRE_AND_FORGET_COMMANDS = {"power_sleep", "power_hibernate", "power_shutdown", "power_restart"}

    async def send_command(self, command: str) -> bool:
        if not self._session:
            return False
        url = f"http://{self._config.host}:{AGENT_PORT}/command"
        if command in self.FIRE_AND_FORGET_COMMANDS:
            return await self._send_fire_and_forget(url, command)
        try:
            async with self._session.post(url, json={"command": command}) as resp:
                return resp.status == 200
        except Exception as err:
            _LOG.debug("Command '%s' failed: %s", command, err)
            return False

    async def _send_fire_and_forget(self, url: str, command: str) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=3, connect=2)
            async with self._session.post(url, json={"command": command}, timeout=timeout) as resp:
                return resp.status == 200
        except (asyncio.TimeoutError, aiohttp.ClientError):
            _LOG.info("Power command '%s' sent (host going offline as expected)", command)
            return True

    async def power_on_wol(self) -> bool:
        if not self._config.wol_enabled:
            return False
        try:
            send_magic_packet(self._config.mac_address)
            _LOG.info("WoL packet sent to %s", self._config.mac_address)
            return True
        except Exception as err:
            _LOG.error("WoL failed: %s", err)
            return False

    # --- Hardware detection by HardwareId ---

    CPU_PREFIXES = ("/intelcpu/", "/amdcpu/")
    GPU_PREFIXES = ("/gpu-nvidia/", "/gpu-amd/", "/gpu-intel/")
    MEMORY_PREFIX = "/ram"
    STORAGE_PREFIXES = ("/nvme/", "/hdd/", "/ssd/")
    NETWORK_PREFIX = "/nic/"
    MOTHERBOARD_PREFIX = "/lpc/"

    def _find_components(self, data: dict, prefixes: tuple[str, ...]) -> list[dict]:
        results = []
        for hw in data.get("Children", []):
            for comp in hw.get("Children", []):
                hw_id = comp.get("HardwareId", "").lower()
                if any(hw_id.startswith(p) for p in prefixes):
                    results.append(comp)
        return results

    def _detect_cpu(self, data: dict) -> dict | None:
        cpus = self._find_components(data, self.CPU_PREFIXES)
        if cpus:
            return cpus[0]
        for hw in data.get("Children", []):
            for comp in hw.get("Children", []):
                text = comp.get("Text", "").lower()
                if any(k in text for k in ["cpu", "processor", "ryzen", "core i", "xeon"]):
                    hw_id = comp.get("HardwareId", "").lower()
                    if not any(hw_id.startswith(p) for p in self.GPU_PREFIXES):
                        return comp
        return None

    def _detect_gpu(self, data: dict) -> dict | None:
        gpus = self._find_components(data, self.GPU_PREFIXES)
        return gpus[0] if gpus else None

    def _detect_memory(self, data: dict) -> dict | None:
        for hw in data.get("Children", []):
            for comp in hw.get("Children", []):
                hw_id = comp.get("HardwareId", "").lower()
                if hw_id == self.MEMORY_PREFIX or hw_id.startswith(self.MEMORY_PREFIX + "/"):
                    return comp
        for hw in data.get("Children", []):
            for comp in hw.get("Children", []):
                text = comp.get("Text", "").lower()
                if "memory" in text or text == "ram":
                    return comp
        return None

    def _detect_storage(self, data: dict) -> dict | None:
        devices = []
        for comp in self._find_components(data, self.STORAGE_PREFIXES):
            used = self._find_sensor(comp, ["used space"], group_filter="load")
            if used is None:
                used = self._find_sensor(comp, ["used space"])
            if used is not None:
                devices.append({"component": comp, "used": used})
        if devices:
            return max(devices, key=lambda x: x["used"])["component"]
        return None

    def _detect_network(self, data: dict) -> dict | None:
        interfaces = []
        for comp in self._find_components(data, (self.NETWORK_PREFIX,)):
            text = comp.get("Text", "").lower()
            if any(v in text for v in ["vethernet", "virtual", "loopback"]):
                continue
            dl = self._find_sensor(comp, ["download speed"]) or 0
            ul = self._find_sensor(comp, ["upload speed"]) or 0
            interfaces.append({"component": comp, "activity": dl * 10 + ul})
        if interfaces:
            active = [i for i in interfaces if i["activity"] > 0]
            if active:
                return max(active, key=lambda x: x["activity"])["component"]
            return interfaces[0]["component"]
        return None

    def _detect_motherboard(self, data: dict) -> dict | None:
        chips = self._find_components(data, (self.MOTHERBOARD_PREFIX,))
        return chips[0] if chips else None

    def _find_sensor(
        self, hardware: dict, targets: list[str], group_filter: str | None = None
    ) -> float | None:
        for group in hardware.get("Children", []):
            if group_filter and group_filter not in group.get("Text", "").lower():
                continue
            for sensor in group.get("Children", []):
                text = sensor.get("Text", "").lower()
                for target in targets:
                    if target.lower() in text:
                        val = self._parse_value(sensor.get("Value", ""))
                        if val is not None:
                            return val
        return None

    @staticmethod
    def _parse_value(value_str: str) -> float | None:
        try:
            return float(value_str.split()[0])
        except (ValueError, IndexError):
            return None

    def _parse_cpu(self, hw: dict, sd: SystemData) -> None:
        sd.cpu_temp = self._find_sensor(
            hw, ["core average", "cpu package", "package", "tctl", "tdie"], group_filter="temperature"
        )
        sd.cpu_load = self._find_sensor(
            hw, ["cpu total", "total", "cpu usage"], group_filter="load"
        )
        sd.cpu_power = self._find_sensor(
            hw, ["cpu package", "package power", "cpu power"], group_filter="power"
        )

        clocks = []
        for group in hw.get("Children", []):
            if "clock" in group.get("Text", "").lower():
                for sensor in group.get("Children", []):
                    text = sensor.get("Text", "").lower()
                    if ("core" in text or "cpu" in text) and "bus" not in text:
                        val = self._parse_value(sensor.get("Value", ""))
                        if val and val > 100:
                            clocks.append(val)
        if clocks:
            sd.cpu_clock = sum(clocks) / len(clocks)

    def _parse_gpu(self, hw: dict, sd: SystemData) -> None:
        sd.gpu_temp = self._find_sensor(
            hw, ["gpu core", "gpu", "core", "temperature"], group_filter="temperature"
        )
        sd.gpu_load = self._find_sensor(
            hw, ["gpu core", "gpu", "core load", "3d load"], group_filter="load"
        )

    def _parse_memory(self, hw: dict, sd: SystemData) -> None:
        used = self._find_sensor(hw, ["memory used", "used"], group_filter="data")
        avail = self._find_sensor(hw, ["memory available", "available"], group_filter="data")
        if used:
            sd.memory_used = used
        if used and avail:
            sd.memory_total = used + avail

    def _parse_storage(self, hw: dict, sd: SystemData) -> None:
        used_pct = self._find_sensor(hw, ["used space", "usage"], group_filter="load")
        if used_pct:
            sd.storage_used_percent = used_pct
            name = hw.get("Text", "")
            total = self._extract_size(name)
            if total:
                sd.storage_total = total
                sd.storage_used = (used_pct / 100) * total
        sd.storage_temp = self._find_sensor(hw, ["temperature"], group_filter="temperature")

    def _parse_network(self, hw: dict, sd: SystemData) -> None:
        ul = self._find_sensor(hw, ["upload speed", "tx", "sent"], group_filter="throughput")
        if ul is None:
            ul = self._find_sensor(hw, ["upload speed", "tx", "sent"], group_filter="data")
        dl = self._find_sensor(hw, ["download speed", "rx", "received"], group_filter="throughput")
        if dl is None:
            dl = self._find_sensor(hw, ["download speed", "rx", "received"], group_filter="data")

        def to_mbps(value: float | None, keywords: list[str]) -> float | None:
            if value is None:
                return None
            for group in hw.get("Children", []):
                for sensor in group.get("Children", []):
                    if any(k in sensor.get("Text", "").lower() for k in keywords):
                        v = sensor.get("Value", "")
                        if "MB/s" in v or "Mbps" in v:
                            return value * 8
                        return value / 125
            return value / 125

        sd.network_up = to_mbps(ul, ["upload", "tx", "sent"])
        sd.network_down = to_mbps(dl, ["download", "rx", "received"])

    def _parse_motherboard(self, hw: dict, sd: SystemData) -> None:
        temps = []
        fans = []
        for group in hw.get("Children", []):
            gt = group.get("Text", "").lower()
            if "temperature" in gt:
                for s in group.get("Children", []):
                    v = self._parse_value(s.get("Value", ""))
                    if v and 20 < v < 100:
                        temps.append(v)
            elif "fan" in gt:
                for s in group.get("Children", []):
                    v = self._parse_value(s.get("Value", ""))
                    if v and v > 0:
                        fans.append(v)
        if temps:
            sd.motherboard_temp_avg = sum(temps) / len(temps)
            sd.motherboard_temp_max = max(temps)
        if fans:
            sd.fan_speeds = fans

    @staticmethod
    def _extract_size(name: str) -> float | None:
        match = re.search(r'(\d+(?:\.\d+)?)\s*(TB|GB)', name, re.IGNORECASE)
        if match:
            val = float(match.group(1))
            if match.group(2).upper() == "TB":
                val *= 1000
            return val
        return None

    @staticmethod
    def _count_sensors(data: dict) -> int:
        count = 0
        if isinstance(data, dict):
            if "Value" in data and data.get("Value", "").strip():
                count += 1
            for child in data.get("Children", []):
                count += HTCPClient._count_sensors(child)
        return count
