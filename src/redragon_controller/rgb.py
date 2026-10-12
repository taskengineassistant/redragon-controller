"""
High-level RGB Controller
Provides easy-to-use interface for RGB effects and animations.
"""

from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import IntEnum
import time
import threading

from .protocol import (
    Command, RGBZone, RGBEffect, Color, ReportID,
    build_command, parse_response,
    cmd_set_color, cmd_set_effect, cmd_set_brightness, cmd_set_speed
)
from .hid_transport import HIDTransport, TransportError


class EffectSpeed(IntEnum):
    """Effect speed presets."""
    SLOWEST = 16
    SLOW = 64
    NORMAL = 128
    FAST = 192
    FASTEST = 240


class EffectDirection(IntEnum):
    """Effect direction presets."""
    LEFT_TO_RIGHT = 0
    RIGHT_TO_LEFT = 1
    TOP_TO_BOTTOM = 2
    BOTTOM_TO_TOP = 3
    CENTER_OUT = 4
    OUT_TO_CENTER = 5


@dataclass
class Effect:
    """Represents an RGB effect configuration."""
    effect: RGBEffect
    color: Optional[Color] = None
    speed: int = EffectSpeed.NORMAL
    direction: int = EffectDirection.LEFT_TO_RIGHT
    zone: RGBZone = RGBZone.ALL
    key_bitmap: Optional[bytes] = None
    name: str = ""
    
    def to_command(self) -> bytes:
        """Generate command bytes for this effect."""
        if self.effect == RGBEffect.STATIC and self.color:
            return cmd_set_color(self.zone, self.color, self.key_bitmap)
        return cmd_set_effect(self.effect, self.color, self.speed, self.direction)


@dataclass
class AnimationFrame:
    """Single frame of a custom animation."""
    colors: Dict[int, Color]  # key_index -> Color
    duration_ms: int = 100


@dataclass
class CustomAnimation:
    """Custom multi-frame animation."""
    frames: List[AnimationFrame]
    loop: bool = True
    name: str = ""


class RGBController:
    """
    High-level RGB controller for Redragon keyboards.
    
    Provides convenient methods for common operations:
    - Static colors per key/zone
    - Built-in effects
    - Custom animations
    - Brightness/speed control
    """
    
    # K585 key layout (87 keys TKL) - key index to position mapping
    KEY_LAYOUT = {
        # Row 0: Function row
        0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (3, 0),  # Esc, F1, F2, F3
        4: (4, 0), 5: (5, 0), 6: (6, 0), 7: (7, 0),  # F4, F5, F6, F7
        8: (8, 0), 9: (9, 0), 10: (10, 0), 11: (11, 0), 12: (12, 0), 13: (13, 0),  # F8-F12, PrtSc
        
        # Row 1: Number row
        14: (0, 1), 15: (1, 1), 16: (2, 1), 17: (3, 1), 18: (4, 1), 19: (5, 1),  # ~, 1, 2, 3, 4, 5
        20: (6, 1), 21: (7, 1), 22: (8, 1), 23: (9, 1), 24: (10, 1), 25: (11, 1), 26: (12, 1), 27: (13, 1),  # 6,7,8,9,0,-,=,Backspace
        
        # Row 2: QWERTY row
        28: (0, 2), 29: (1, 2), 30: (2, 2), 31: (3, 2), 32: (4, 2), 33: (5, 2), 34: (6, 2), 35: (7, 2),  # Tab, Q, W, E, R, T, Y, U
        36: (8, 2), 37: (9, 2), 38: (10, 2), 39: (11, 2), 40: (12, 2), 41: (13, 2),  # I, O, P, [, ], \\
        
        # Row 3: ASDF row
        42: (0, 3), 43: (1, 3), 44: (2, 3), 45: (3, 3), 46: (4, 3), 47: (5, 3), 48: (6, 3), 49: (7, 3),  # Caps, A, S, D, F, G, H, J
        50: (8, 3), 51: (9, 3), 52: (10, 3), 53: (11, 3), 54: (12, 3),  # K, L, ;, ', Enter
        
        # Row 4: ZXCV row
        55: (0, 4), 56: (1, 4), 57: (2, 4), 58: (3, 4), 59: (4, 4), 60: (5, 4), 61: (6, 4), 62: (7, 4),  # Shift, Z, X, C, V, B, N, M
        63: (8, 4), 64: (9, 4), 65: (10, 4), 66: (11, 4), 67: (12, 4),  # ,, ., /, Shift
        
        # Row 5: Bottom row
        68: (0, 5), 69: (1, 5), 70: (2, 5), 71: (3, 5),  # Ctrl, Win, Alt, Space
        72: (7, 5), 73: (8, 5), 74: (9, 5), 75: (10, 5),  # Alt, Fn, Menu, Ctrl
        
        # Navigation cluster
        76: (13, 1), 77: (13, 2), 78: (13, 3),  # Ins, Home, PgUp
        79: (13, 4), 80: (13, 5), 81: (13, 6),  # Del, End, PgDn
        
        # Arrow keys
        82: (11, 4), 83: (12, 4), 84: (11, 5), 85: (12, 5),  # Left, Down, Right, Up (approx)
        
        # Numpad (if present)
        86: (15, 0), 87: (16, 0), 88: (17, 0),  # NumLock, /, *
        89: (15, 1), 90: (16, 1), 91: (17, 1), 92: (18, 1),  # 7, 8, 9, -
        93: (15, 2), 94: (16, 2), 95: (17, 2),  # 4, 5, 6
        96: (15, 3), 97: (16, 3), 98: (17, 3), 99: (18, 2),  # 1, 2, 3, +
        100: (15, 4), 101: (16, 4), 102: (17, 4),  # 0, ., Enter
    }
    
    def __init__(self, transport: HIDTransport):
        self.transport = transport
        self._current_effect: Optional[Effect] = None
        self._brightness = 255
        self._animation_thread: Optional[threading.Thread] = None
        self._stop_animation = threading.Event()
    
    def set_static_color(self, color: Color, zone: RGBZone = RGBZone.ALL, 
                         key_bitmap: Optional[bytes] = None) -> bool:
        """Set a static color for a zone or all keys."""
        cmd = cmd_set_color(zone, color, key_bitmap)
        return self._send_command(cmd)
    
    def set_key_color(self, key_index: int, color: Color) -> bool:
        """Set color for a single key."""
        # Use custom zone with single key bitmap
        bitmap = bytearray(16)  # 128 bits = 16 bytes for up to 128 keys
        if key_index < 128:
            bitmap[key_index // 8] |= (1 << (key_index % 8))
        return self.set_static_color(color, RGBZone.CUSTOM, bytes(bitmap))
    
    def set_effect(self, effect: RGBEffect, color: Optional[Color] = None,
                   speed: int = EffectSpeed.NORMAL, 
                   direction: int = EffectDirection.LEFT_TO_RIGHT,
                   zone: RGBZone = RGBZone.ALL) -> bool:
        """Set a built-in effect."""
        eff = Effect(effect, color, speed, direction, zone)
        self._current_effect = eff
        return self._send_command(eff.to_command())
    
    def breathing(self, color: Color, speed: int = EffectSpeed.NORMAL) -> bool:
        """Breathing effect with single color."""
        return self.set_effect(RGBEffect.BREATHING, color, speed)
    
    def wave(self, color: Optional[Color] = None, 
             speed: int = EffectSpeed.NORMAL,
             direction: int = EffectDirection.LEFT_TO_RIGHT) -> bool:
        """Wave effect."""
        return self.set_effect(RGBEffect.WAVE, color, speed, direction)
    
    def ripple(self, color: Color, speed: int = EffectSpeed.NORMAL) -> bool:
        """Ripple effect on keypress."""
        return self.set_effect(RGBEffect.RIPPLE, color, speed)
    
    def reactive(self, color: Color, speed: int = EffectSpeed.FAST) -> bool:
        """Reactive - light up keys on press."""
        return self.set_effect(RGBEffect.REACTIVE, color, speed)
    
    def spectrum(self, speed: int = EffectSpeed.SLOW) -> bool:
        """Rainbow spectrum cycling."""
        return self.set_effect(RGBEffect.SPECTRUM, speed=speed)
    
    def rainbow_wave(self, speed: int = EffectSpeed.NORMAL,
                     direction: int = EffectDirection.LEFT_TO_RIGHT) -> bool:
        """Moving rainbow wave."""
        return self.set_effect(RGBEffect.RAINBOW_WAVE, speed=speed, direction=direction)
    
    def starlight(self, color: Optional[Color] = None, 
                  speed: int = EffectSpeed.NORMAL) -> bool:
        """Random twinkling stars."""
        return self.set_effect(RGBEffect.STARLIGHT, color, speed)
    
    def scan(self, color: Color, speed: int = EffectSpeed.FAST,
             direction: int = EffectDirection.TOP_TO_BOTTOM) -> bool:
        """Scanning line effect."""
        return self.set_effect(RGBEffect.SCAN, color, speed, direction)
    
    def off(self) -> bool:
        """Turn off all RGB."""
        return self.set_effect(RGBEffect.OFF)
    
    def set_brightness(self, level: int) -> bool:
        """Set global brightness (0-255)."""
        self._brightness = max(0, min(255, level))
        return self._send_command(cmd_set_brightness(self._brightness))
    
    def set_speed(self, speed: int) -> bool:
        """Set effect speed (0-255)."""
        return self._send_command(cmd_set_speed(speed))
    
    def get_state(self) -> Optional[dict]:
        """Query current RGB state from keyboard."""
        cmd = build_command(Command.RGB_GET_STATE)
        response = self._send_command_raw(cmd)
        if response:
            cmd_id, payload, success = parse_response(response)
            if success and len(payload) >= 4:
                return {
                    "effect": RGBEffect(payload[0]),
                    "speed": payload[1],
                    "direction": payload[2],
                    "brightness": payload[3],
                }
        return None
    
    def start_custom_animation(self, animation: CustomAnimation) -> None:
        """Start a custom multi-frame animation in background thread."""
        self.stop_animation()
        self._stop_animation.clear()
        self._animation_thread = threading.Thread(
            target=self._run_animation, args=(animation,), daemon=True
        )
        self._animation_thread.start()
    
    def stop_animation(self) -> None:
        """Stop any running custom animation."""
        self._stop_animation.set()
        if self._animation_thread:
            self._animation_thread.join(timeout=1.0)
            self._animation_thread = None
    
    def _run_animation(self, animation: CustomAnimation) -> None:
        """Background thread for custom animation."""
        frame_idx = 0
        while not self._stop_animation.is_set():
            frame = animation.frames[frame_idx % len(animation.frames)]
            
            # Send colors for this frame
            for key_idx, color in frame.colors.items():
                if self._stop_animation.is_set():
                    break
                self.set_key_color(key_idx, color)
            
            time.sleep(frame.duration_ms / 1000.0)
            frame_idx += 1
            
            if not animation.loop and frame_idx >= len(animation.frames):
                break
    
    def _send_command(self, cmd: bytes) -> bool:
        """Send command via feature report and verify response."""
        try:
            response = self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
            _, _, success = parse_response(response)
            return success
        except TransportError:
            return False
    
    def _send_command_raw(self, cmd: bytes) -> Optional[bytes]:
        """Send command and return raw response."""
        try:
            return self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
        except TransportError:
            return None
    
    def create_gradient(self, start: Color, end: Color, steps: int) -> List[Color]:
        """Create a color gradient between two colors."""
        colors = []
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0
            r = int(start.r + (end.r - start.r) * t)
            g = int(start.g + (end.g - start.g) * t)
            b = int(start.b + (end.b - start.b) * t)
            colors.append(Color(r, g, b))
        return colors
    
    def create_rainbow(self, steps: int, offset: int = 0) -> List[Color]:
        """Create a rainbow color sequence."""
        import colorsys
        colors = []
        for i in range(steps):
            h = ((i + offset) % steps) / steps
            r, g, b = colorsys.hsv_to_rgb(h, 1.0, 1.0)
            colors.append(Color(int(r*255), int(g*255), int(b*255)))
        return colors