"""
Audio Device Manager
Handles audio device enumeration, switching, and hot-swapping
"""

import subprocess
import re
import platform
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AudioDevice:
    """Represents an audio device"""
    index: str
    name: str
    platform: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "name": self.name,
            "platform": self.platform,
        }


class AudioDeviceManager:
    """Manages audio device enumeration and switching"""

    def __init__(self):
        """Initialize audio device manager"""
        self.current_device: Optional[str] = None
        self.devices: Dict[str, AudioDevice] = {}
        self.is_enumerating: bool = False
        self.enum_start_time: Optional[float] = None
        self.system = platform.system()
        self._enumerate_devices()

    def _get_platform_config(self) -> Dict[str, Any]:
        """Get FFmpeg configuration for current platform"""
        if self.system == "Windows":
            return {
                "format": "dshow",
                "device_prefix": "audio=",
                "list_devices_cmd": ['ffmpeg', '-list_devices', 'true', '-f', 'dshow', '-i', 'dummy']
            }
        elif self.system == "Darwin":  # macOS
            return {
                "format": "avfoundation",
                "device_prefix": ":",
                "list_devices_cmd": ['ffmpeg', '-f', 'avfoundation', '-list_devices', 'true', '-i', '""']
            }
        elif self.system == "Linux":
            return {
                "format": "alsa",
                "device_prefix": "",
                "list_devices_cmd": ['arecord', '-l']
            }
        else:
            raise NotImplementedError(f"Unsupported OS: {self.system}")

    def _enumerate_devices(self):
        """Enumerate available audio devices"""
        try:
            config = self._get_platform_config()
            result = subprocess.run(
                config['list_devices_cmd'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                timeout=5
            )

            output = result.stdout + "\n" + result.stderr
            self.devices = {}

            if self.system == "Windows":
                # Windows: "DirectShow audio device" format
                devices = re.findall(r'\"(.*?)\" \(audio\)', output, re.IGNORECASE)
                for i, name in enumerate(devices):
                    device_id = f"audio={name}"
                    self.devices[device_id] = AudioDevice(
                        index=str(i),
                        name=name,
                        platform="windows"
                    )

            elif self.system == "Darwin":  # macOS
                # macOS: AVFoundation format
                # Look for the AVFoundation section
                if "AVFoundation audio devices:" in output or "AVFoundation indev" in output:
                    devices = re.findall(r'\[AVFoundation indev @ .*?\] \[(\d+)\] (.*)', output)
                    for index, name in devices:
                        device_id = f":{index}"
                        self.devices[device_id] = AudioDevice(
                            index=index,
                            name=name.strip(),
                            platform="macos"
                        )

            elif self.system == "Linux":
                # Linux: ALSA format
                # Parse arecord output
                lines = output.split('\n')
                for line in lines:
                    # Look for lines like "**** List of CAPTURE Hardware Devices ****"
                    if "card" in line.lower() and "device" in line.lower():
                        match = re.search(r'card (\d+).*device (\d+):', line)
                        if match:
                            card, device = match.groups()
                            device_id = f"hw:{card},{device}"
                            self.devices[device_id] = AudioDevice(
                                index=f"{card},{device}",
                                name=line.strip(),
                                platform="linux"
                            )

        except subprocess.TimeoutExpired:
            print("✗ Timeout while enumerating audio devices")
        except FileNotFoundError:
            print(f"✗ Required tool not found for {self.system}")
        except Exception as e:
            print(f"✗ Error enumerating audio devices: {e}")

    async def refresh_devices(self) -> bool:
        """Refresh device list asynchronously"""
        if self.is_enumerating:
            print("Device enumeration already in progress...")
            return False

        try:
            self.is_enumerating = True
            self.enum_start_time = datetime.now()

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._enumerate_devices)

            enum_time = (datetime.now() - self.enum_start_time).total_seconds()
            print(f"✓ Enumerated {len(self.devices)} audio devices in {enum_time:.2f}s")
            return True

        except Exception as e:
            print(f"✗ Failed to refresh devices: {e}")
            return False

        finally:
            self.is_enumerating = False
            self.enum_start_time = None

    def set_device(self, device_id: str) -> bool:
        """Set current audio device"""
        if device_id not in self.devices and device_id not in ["default", "0"]:
            print(f"✗ Device {device_id} not found in enumerated devices")
            return False

        self.current_device = device_id
        print(f"✓ Audio device set to: {device_id}")
        return True

    def get_device(self) -> Optional[str]:
        """Get current audio device"""
        return self.current_device

    def get_devices_list(self) -> List[Dict[str, Any]]:
        """Get list of available devices as dicts"""
        return [device.to_dict() for device in self.devices.values()]

    def get_status(self) -> Dict[str, Any]:
        """Get current status of audio device manager"""
        return {
            "current_device": self.current_device,
            "device_count": len(self.devices),
            "devices": self.get_devices_list(),
            "is_enumerating": self.is_enumerating,
            "platform": self.system,
        }


# Global audio device manager instance
_device_manager: Optional[AudioDeviceManager] = None


def get_device_manager() -> AudioDeviceManager:
    """Get or create global audio device manager"""
    global _device_manager
    if _device_manager is None:
        _device_manager = AudioDeviceManager()
    return _device_manager
