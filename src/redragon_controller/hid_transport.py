"""
Low-level HID Transport Layer
Handles communication with Redragon keyboards via USB HID.
"""

import hid
import time
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import IntEnum


class ReportID(IntEnum):
    """HID Report IDs used by Redragon keyboards."""
    FEATURE_GET = 0x01      # Get feature report
    FEATURE_SET = 0x02      # Set feature report
    OUTPUT = 0x03           # Output report (RGB, key commands)
    INPUT = 0x04            # Input report (key presses, status)


class TransportError(Exception):
    """Raised when HID communication fails."""
    pass


@dataclass
class DeviceInfo:
    """Information about a connected Redragon device."""
    path: bytes
    vendor_id: int
    product_id: int
    serial_number: str
    manufacturer: str
    product: str
    release_number: int
    interface_number: int


class HIDTransport:
    """
    Cross-platform HID transport for Redragon keyboards.
    
    Uses hidapi for Linux/Windows/macOS compatibility.
    Communicates via Feature Reports (0x01/0x02) for commands
    and Output Reports (0x03) for RGB/key data streaming.
    """
    
    # Known Redragon VID/PID combinations
    KNOWN_DEVICES = [
        (0x258a, 0x0001, "K585 RGB"),
        (0x258a, 0x0002, "K552 RGB"),
        (0x258a, 0x0003, "K530 Pro"),
        (0x0483, 0x5750, "K585 RGB (STM32)"),
        (0x0483, 0x5751, "K552 RGB (STM32)"),
    ]
    
    def __init__(self, vendor_id: Optional[int] = None, product_id: Optional[int] = None, path: Optional[bytes] = None):
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.path = path
        self.device: Optional[hid.device] = None
        self._device_info: Optional[DeviceInfo] = None
        self._report_size = 64  # Standard HID report size
    
    @classmethod
    def discover(cls) -> List[DeviceInfo]:
        """Discover all connected Redragon keyboards."""
        devices = []
        for device_dict in hid.enumerate():
            vid = device_dict["vendor_id"]
            pid = device_dict["product_id"]
            
            # Check if it's a known Redragon device
            is_redragon = any(v == vid and p == pid for v, p, _ in cls.KNOWN_DEVICES)
            
            # Also check manufacturer string
            manufacturer = device_dict.get("manufacturer_string", "").lower()
            product = device_dict.get("product_string", "").lower()
            if "redragon" in manufacturer or "redragon" in product:
                is_redragon = True
            
            if is_redragon:
                devices.append(DeviceInfo(
                    path=device_dict["path"],
                    vendor_id=vid,
                    product_id=pid,
                    serial_number=device_dict.get("serial_number", ""),
                    manufacturer=device_dict.get("manufacturer_string", ""),
                    product=device_dict.get("product_string", ""),
                    release_number=device_dict.get("release_number", 0),
                    interface_number=device_dict.get("interface_number", -1),
                ))
        return devices
    
    def connect(self) -> None:
        """Open connection to the device."""
        if self.device is not None:
            return
        
        try:
            if self.path:
                self.device = hid.device()
                self.device.open_path(self.path)
            else:
                self.device = hid.device()
                self.device.open(self.vendor_id, self.product_id)
            
            # Set non-blocking mode for async reads
            self.device.set_nonblocking(1)
            
            # Cache device info
            self._device_info = DeviceInfo(
                path=self.path or b"",
                vendor_id=self.vendor_id or 0,
                product_id=self.product_id or 0,
                serial_number=self.device.get_serial_number_string() or "",
                manufacturer=self.device.get_manufacturer_string() or "",
                product=self.device.get_product_string() or "",
                release_number=0,
                interface_number=-1,
            )
        except hid.HIDException as e:
            raise TransportError(f"Failed to connect to device: {e}") from e
    
    def disconnect(self) -> None:
        """Close connection to the device."""
        if self.device:
            self.device.close()
            self.device = None
            self._device_info = None
    
    def __enter__(self) -> "HIDTransport":
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.disconnect()
    
    @property
    def is_connected(self) -> bool:
        return self.device is not None
    
    @property
    def device_info(self) -> Optional[DeviceInfo]:
        return self._device_info
    
    def send_feature_report(self, report_id: int, data: bytes) -> bytes:
        """
        Send a Feature Report (Report ID 0x02) and read response (Report ID 0x01).
        
        This is the primary command channel for Redragon keyboards.
        """
        if not self.device:
            raise TransportError("Not connected")
        
        # Build report: [Report ID][Data...]
        report = bytes([report_id]) + data
        
        # Pad to report size
        if len(report) < self._report_size:
            report += bytes([0x00] * (self._report_size - len(report)))
        
        try:
            # Write feature report
            self.device.send_feature_report(report)
            
            # Read response (blocking with timeout)
            response = self._read_feature_report(ReportID.FEATURE_GET)
            return response
        except hid.HIDException as e:
            raise TransportError(f"Feature report failed: {e}") from e
    
    def send_output_report(self, report_id: int, data: bytes) -> None:
        """
        Send an Output Report (Report ID 0x03) for streaming data.
        
        Used for RGB effects, key state updates, etc.
        """
        if not self.device:
            raise TransportError("Not connected")
        
        report = bytes([report_id]) + data
        
        if len(report) < self._report_size:
            report += bytes([0x00] * (self._report_size - len(report)))
        
        try:
            self.device.write(report)
        except hid.HIDException as e:
            raise TransportError(f"Output report failed: {e}") from e
    
    def _read_feature_report(self, report_id: int, timeout: float = 1.0) -> bytes:
        """Read a feature report with timeout."""
        start = time.time()
        while time.time() - start < timeout:
            try:
                data = self.device.get_feature_report(report_id, self._report_size)
                if data:
                    return bytes(data)
            except hid.HIDException:
                pass
            time.sleep(0.01)
        raise TransportError(f"Timeout reading feature report 0x{report_id:02x}")
    
    def read_input_report(self, timeout: float = 0.1) -> Optional[bytes]:
        """Read an input report (non-blocking)."""
        if not self.device:
            return None
        try:
            data = self.device.read(self._report_size)
            return bytes(data) if data else None
        except hid.HIDException:
            return None
    
    def get_device_name(self) -> str:
        """Get human-readable device name."""
        if self._device_info:
            for vid, pid, name in self.KNOWN_DEVICES:
                if vid == self._device_info.vendor_id and pid == self._device_info.product_id:
                    return name
            return f"{self._device_info.manufacturer} {self._device_info.product}"
        return "Unknown Redragon Device"