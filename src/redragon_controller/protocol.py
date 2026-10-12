"""
Redragon Keyboard Command Protocol
Defines the command structure for communicating with Redragon keyboards.
"""

from enum import IntEnum
from dataclasses import dataclass
from typing import Optional, List
import struct


class Command(IntEnum):
    """Main command categories."""
    # RGB Commands (0x10-0x1F)
    RGB_SET_COLOR = 0x10        # Set single key/zone color
    RGB_SET_EFFECT = 0x11       # Set effect (wave, ripple, breathing, etc.)
    RGB_SET_BRIGHTNESS = 0x12   # Set brightness level (0-255)
    RGB_SET_SPEED = 0x13        # Set effect speed (0-255)
    RGB_SET_DIRECTION = 0x14    # Set effect direction
    RGB_SAVE_PROFILE = 0x15     # Save current RGB to profile slot
    RGB_LOAD_PROFILE = 0x16     # Load RGB from profile slot
    RGB_GET_STATE = 0x17        # Query current RGB state
    RGB_RESET = 0x1F            # Reset to defaults
    
    # Key Commands (0x20-0x2F)
    KEY_REMAP = 0x20            # Remap single key
    KEY_SET_MACRO = 0x21        # Assign macro to key
    KEY_SET_LAYER = 0x22        # Configure layer
    KEY_GET_MAP = 0x23          # Query current keymap
    KEY_RESET = 0x2F            # Reset keymap to default
    
    # Profile Commands (0x30-0x3F)
    PROFILE_SAVE = 0x30         # Save full profile (RGB + keys) to slot
    PROFILE_LOAD = 0x31         # Load profile from slot
    PROFILE_GET_ACTIVE = 0x32   # Get active profile slot
    PROFILE_SET_ACTIVE = 0x33   # Set active profile slot
    PROFILE_GET_INFO = 0x34     # Get profile metadata
    PROFILE_DELETE = 0x3F       # Clear profile slot
    
    # System Commands (0x40-0x4F)
    SYS_GET_INFO = 0x40         # Get device info (FW version, caps)
    SYS_GET_FW_VERSION = 0x41   # Get firmware version
    SYS_ENTER_BOOTLOADER = 0x4E # Enter DFU/bootloader mode
    SYS_RESET = 0x4F            # Full device reset


class ReportID(IntEnum):
    """HID Report IDs."""
    FEATURE_GET = 0x01
    FEATURE_SET = 0x02
    OUTPUT = 0x03
    INPUT = 0x04


class RGBZone(IntEnum):
    """Predefined RGB zones for K585 (87-key TKL)."""
    ALL = 0x00
    LEFT = 0x01       # Left side (Esc-F12, ~-Backspace, Tab-\\)
    RIGHT = 0x02      # Right side (Insert-PgDn, NumLock-+/Enter)
    CENTER = 0x03     # Center (alphanumeric)
    WASD = 0x04       # WASD cluster
    ARROWS = 0x05     # Arrow keys
    FUNCTION_ROW = 0x06  # F1-F12
    NUMBER_ROW = 0x07    # 1-0, -,
    CUSTOM = 0xFF     # Custom zone (followed by key bitmap)


class RGBEffect(IntEnum):
    """Built-in RGB effects."""
    OFF = 0x00
    STATIC = 0x01         # Solid color
    BREATHING = 0x02      # Fade in/out
    WAVE = 0x03           # Horizontal wave
    RIPPLE = 0x04         # Ripple from keypress
    REACTIVE = 0x05       # Light up on press
    SPECTRUM = 0x06       # Rainbow cycle
    RAINBOW_WAVE = 0x07   # Moving rainbow
    STARLIGHT = 0x08      # Random twinkle
    SCAN = 0x09           # Scan line
    CUSTOM = 0xFF         # Custom effect (user-defined frames)


class KeyActionType(IntEnum):
    """Types of key actions for remapping."""
    KEYCODE = 0x00        # Single keycode
    MACRO = 0x01          # Macro sequence
    LAYER = 0x02          # Layer toggle/momentary
    MEDIA = 0x03          # Media key
    MOUSE = 0x04          # Mouse button/movement
    SYSTEM = 0x05         # System control (sleep, wake, etc.)
    NONE = 0xFF           # Disabled


@dataclass
class KeyAction:
    """Represents a key action (remap, macro, layer, etc.)."""
    action_type: KeyActionType
    # For KEYCODE: single HID usage code
    # For MACRO: index into macro table
    # For LAYER: layer number (0-3) + toggle/momentary flag
    # For MEDIA: HID consumer page usage
    # For MOUSE: encoded mouse action
    data: bytes = b""
    
    def to_bytes(self) -> bytes:
        return bytes([self.action_type]) + self.data
    
    @classmethod
    def from_bytes(cls, data: bytes) -> "KeyAction":
        if not data:
            return cls(KeyActionType.NONE)
        return cls(KeyActionType(data[0]), data[1:])


@dataclass
class Macro:
    """Macro sequence: list of (keycode, press/release, delay_ms)."""
    steps: List[tuple]  # (usage_code, is_press, delay_ms)
    repeat: bool = False
    
    def to_bytes(self) -> bytes:
        result = bytearray([len(self.steps), 0x01 if self.repeat else 0x00])
        for usage, is_press, delay in self.steps:
            result.extend(struct.pack("<HBH", usage, 0x01 if is_press else 0x00, delay))
        return bytes(result)


@dataclass
class Color:
    """RGB Color with brightness."""
    r: int
    g: int
    b: int
    brightness: int = 255
    
    def __post_init__(self):
        self.r = max(0, min(255, self.r))
        self.g = max(0, min(255, self.g))
        self.b = max(0, min(255, self.b))
        self.brightness = max(0, min(255, self.brightness))
    
    def to_bytes(self) -> bytes:
        # Apply brightness
        r = (self.r * self.brightness) // 255
        g = (self.g * self.brightness) // 255
        b = (self.b * self.brightness) // 255
        return bytes([r, g, b])
    
    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return cls(r, g, b)
        elif len(hex_str) == 8:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            brightness = int(hex_str[6:8], 16)
            return cls(r, g, b, brightness)
        raise ValueError(f"Invalid hex color: {hex_str}")
    
    def to_hex(self) -> str:
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}{self.brightness:02x}"


def build_command(cmd: Command, payload: bytes = b"") -> bytes:
    """
    Build a complete command packet.
    
    Format: [Command][Length][Payload...][Checksum]
    Checksum = XOR of all bytes
    """
    length = len(payload)
    packet = bytearray([cmd, length])
    packet.extend(payload)
    
    # Calculate checksum (XOR of all bytes)
    checksum = 0
    for b in packet:
        checksum ^= b
    packet.append(checksum)
    
    return bytes(packet)


def parse_response(data: bytes) -> tuple[Command, bytes, bool]:
    """
    Parse a response packet.
    
    Returns: (command, payload, success)
    Format: [Command][Status][Length][Payload...][Checksum]
    Status: 0x00 = OK, 0xFF = Error
    """
    if len(data) < 4:
        raise ValueError("Response too short")
    
    cmd = Command(data[0])
    status = data[1]
    length = data[2]
    payload = data[3:3+length]
    checksum = data[3+length] if len(data) > 3+length else 0
    
    # Verify checksum
    calc_checksum = 0
    for b in data[:3+length]:
        calc_checksum ^= b
    
    success = (status == 0x00) and (checksum == calc_checksum)
    return cmd, payload, success


# Predefined command builders
def cmd_set_color(zone: RGBZone, color: Color, key_bitmap: Optional[bytes] = None) -> bytes:
    """Build RGB_SET_COLOR command."""
    payload = bytearray([zone])
    payload.extend(color.to_bytes())
    if zone == RGBZone.CUSTOM and key_bitmap:
        payload.extend(key_bitmap)
    return build_command(Command.RGB_SET_COLOR, bytes(payload))


def cmd_set_effect(effect: RGBEffect, color: Optional[Color] = None, 
                   speed: int = 128, direction: int = 0) -> bytes:
    """Build RGB_SET_EFFECT command."""
    payload = bytearray([effect, speed, direction])
    if color:
        payload.extend(color.to_bytes())
    return build_command(Command.RGB_SET_EFFECT, bytes(payload))


def cmd_set_brightness(level: int) -> bytes:
    """Build RGB_SET_BRIGHTNESS command."""
    return build_command(Command.RGB_SET_BRIGHTNESS, bytes([max(0, min(255, level))]))


def cmd_set_speed(speed: int) -> bytes:
    """Build RGB_SET_SPEED command."""
    return build_command(Command.RGB_SET_SPEED, bytes([max(0, min(255, speed))]))


def cmd_remap_key(key_index: int, action: KeyAction) -> bytes:
    """Build KEY_REMAP command."""
    payload = bytearray([key_index])
    payload.extend(action.to_bytes())
    return build_command(Command.KEY_REMAP, bytes(payload))


def cmd_save_profile(slot: int) -> bytes:
    """Build PROFILE_SAVE command."""
    return build_command(Command.PROFILE_SAVE, bytes([slot]))


def cmd_load_profile(slot: int) -> bytes:
    """Build PROFILE_LOAD command."""
    return build_command(Command.PROFILE_LOAD, bytes([slot]))


def cmd_get_device_info() -> bytes:
    """Build SYS_GET_INFO command."""
    return build_command(Command.SYS_GET_INFO, b"")