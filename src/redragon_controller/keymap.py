"""
Key Mapping and Macro System
Handles key remapping, macros, layers, and advanced key behaviors.
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import IntEnum
import json

from .protocol import (
    Command, KeyActionType, KeyAction, Macro,
    build_command, parse_response,
    cmd_remap_key
)
from .hid_transport import HIDTransport, TransportError, ReportID


# Standard HID Usage Codes (USB HID Usage Tables)
class KeyCode(IntEnum):
    """Common HID keyboard usage codes."""
    # Modifier keys
    LCtrl = 0xE0
    LShift = 0xE1
    LAlt = 0xE2
    LGUI = 0xE3
    RCtrl = 0xE4
    RShift = 0xE5
    RAlt = 0xE6
    RGUI = 0xE7
    
    # Letters
    A = 0x04
    B = 0x05
    C = 0x06
    D = 0x07
    E = 0x08
    F = 0x09
    G = 0x0A
    H = 0x0B
    I = 0x0C
    J = 0x0D
    K = 0x0E
    L = 0x0F
    M = 0x10
    N = 0x11
    O = 0x12
    P = 0x13
    Q = 0x14
    R = 0x15
    S = 0x16
    T = 0x17
    U = 0x18
    V = 0x19
    W = 0x1A
    X = 0x1B
    Y = 0x1C
    Z = 0x1D
    
    # Numbers
    Num1 = 0x1E
    Num2 = 0x1F
    Num3 = 0x20
    Num4 = 0x21
    Num5 = 0x22
    Num6 = 0x23
    Num7 = 0x24
    Num8 = 0x25
    Num9 = 0x26
    Num0 = 0x27
    
    # Special keys
    Enter = 0x28
    Escape = 0x29
    Backspace = 0x2A
    Tab = 0x2B
    Space = 0x2C
    Minus = 0x2D
    Equal = 0x2E
    LeftBrace = 0x2F
    RightBrace = 0x30
    Backslash = 0x31
    Semicolon = 0x33
    Quote = 0x34
    Grave = 0x35
    Comma = 0x36
    Period = 0x37
    Slash = 0x38
    CapsLock = 0x39
    
    # Function keys
    F1 = 0x3A
    F2 = 0x3B
    F3 = 0x3C
    F4 = 0x3D
    F5 = 0x3E
    F6 = 0x3F
    F7 = 0x40
    F8 = 0x41
    F9 = 0x42
    F10 = 0x43
    F11 = 0x44
    F12 = 0x45
    
    # Navigation
    PrintScreen = 0x46
    ScrollLock = 0x47
    Pause = 0x48
    Insert = 0x49
    Home = 0x4A
    PageUp = 0x4B
    Delete = 0x4C
    End = 0x4D
    PageDown = 0x4E
    Right = 0x4F
    Left = 0x50
    Down = 0x51
    Up = 0x52
    
    # Numpad
    NumLock = 0x53
    KP_Divide = 0x54
    KP_Multiply = 0x55
    KP_Subtract = 0x56
    KP_Add = 0x57
    KP_Enter = 0x58
    KP_1 = 0x59
    KP_2 = 0x5A
    KP_3 = 0x5B
    KP_4 = 0x5C
    KP_5 = 0x5D
    KP_6 = 0x5E
    KP_7 = 0x5F
    KP_8 = 0x60
    KP_9 = 0x61
    KP_0 = 0x62
    KP_Dot = 0x63
    
    # Media keys (Consumer Page)
    Media_Next = 0xB5
    Media_Prev = 0xB6
    Media_Stop = 0xB7
    Media_PlayPause = 0xCD
    Media_Mute = 0xE2
    Media_VolUp = 0xE9
    Media_VolDown = 0xEA


@dataclass
class Layer:
    """A keyboard layer with its own key mappings."""
    index: int
    name: str
    keymap: Dict[int, KeyAction] = field(default_factory=dict)
    parent_layer: Optional[int] = None  # For fallback lookups
    
    def get_action(self, key_index: int) -> Optional[KeyAction]:
        """Get action for key, checking parent layer if not found."""
        if key_index in self.keymap:
            return self.keymap[key_index]
        if self.parent_layer is not None:
            # Would need access to layer manager for recursive lookup
            return None
        return None


class KeyMap:
    """
    Manages key mappings, macros, and layers.
    
    Supports:
    - Per-key remapping
    - Macros (key sequences with delays)
    - Multiple layers (up to 4)
    - Layer switching (momentary/toggle)
    - Media keys
    - Mouse emulation
    """
    
    def __init__(self, transport: HIDTransport):
        self.transport = transport
        self.layers: Dict[int, Layer] = {}
        self.active_layer = 0
        self.macros: Dict[int, Macro] = {}
        self._key_index_map = self._build_key_index_map()
    
    def _build_key_index_map(self) -> Dict[str, int]:
        """Map key names to hardware key indices."""
        # This maps standard key names to the keyboard's internal key indices
        # Based on K585 layout - may need adjustment per model
        return {
            # Function row
            "esc": 0, "f1": 1, "f2": 2, "f3": 3, "f4": 4, "f5": 5, "f6": 6,
            "f7": 7, "f8": 8, "f9": 9, "f10": 10, "f11": 11, "f12": 12, "print_screen": 13,
            
            # Number row
            "grave": 14, "1": 15, "2": 16, "3": 17, "4": 18, "5": 19, "6": 20,
            "7": 21, "8": 22, "9": 23, "0": 24, "minus": 25, "equal": 26, "backspace": 27,
            
            # QWERTY row
            "tab": 28, "q": 29, "w": 30, "e": 31, "r": 32, "t": 33, "y": 34, "u": 35,
            "i": 36, "o": 37, "p": 38, "lbrace": 39, "rbrace": 40, "backslash": 41,
            
            # Home row
            "caps": 42, "a": 43, "s": 44, "d": 45, "f": 46, "g": 47, "h": 48, "j": 49,
            "k": 50, "l": 51, "semicolon": 52, "quote": 53, "enter": 54,
            
            # Bottom row
            "lshift": 55, "z": 56, "x": 57, "c": 58, "v": 59, "b": 60, "n": 61, "m": 62,
            "comma": 63, "period": 64, "slash": 65, "rshift": 66,
            
            # Modifiers
            "lctrl": 67, "lwin": 68, "lalt": 69, "space": 70, "ralt": 71, "fn": 72, "menu": 73, "rctrl": 74,
            
            # Navigation
            "insert": 75, "home": 76, "page_up": 77,
            "delete": 78, "end": 79, "page_down": 80,
            
            # Arrows
            "left": 81, "down": 82, "right": 83, "up": 84,
        }
    
    def add_layer(self, index: int, name: str, parent: Optional[int] = None) -> Layer:
        """Create a new layer."""
        layer = Layer(index, name, parent_layer=parent)
        self.layers[index] = layer
        return layer
    
    def set_layer(self, index: int) -> bool:
        """Set active layer."""
        if index in self.layers:
            self.active_layer = index
            return True
        return False
    
    def remap_key(self, key: str, action: KeyAction, layer: Optional[int] = None) -> bool:
        """Remap a key to an action."""
        layer_idx = layer if layer is not None else self.active_layer
        if layer_idx not in self.layers:
            self.add_layer(layer_idx, f"Layer {layer_idx}")
        
        key_idx = self._key_index_map.get(key.lower())
        if key_idx is None:
            return False
        
        self.layers[layer_idx].keymap[key_idx] = action
        return self._send_remap(key_idx, action)
    
    def map_key(self, from_key: str, to_key: KeyCode, layer: Optional[int] = None) -> bool:
        """Simple key-to-key remap."""
        action = KeyAction(KeyActionType.KEYCODE, bytes([to_key]))
        return self.remap_key(from_key, action, layer)
    
    def set_macro(self, key: str, macro: Macro, layer: Optional[int] = None) -> bool:
        """Assign a macro to a key."""
        # Store macro and get its index
        macro_idx = len(self.macros)
        self.macros[macro_idx] = macro
        
        action = KeyAction(KeyActionType.MACRO, bytes([macro_idx]))
        return self.remap_key(key, action, layer)
    
    def set_layer_key(self, key: str, layer_idx: int, momentary: bool = True, 
                      layer: Optional[int] = None) -> bool:
        """Set a key to switch layers."""
        data = bytes([layer_idx, 0x01 if momentary else 0x00])
        action = KeyAction(KeyActionType.LAYER, data)
        return self.remap_key(key, action, layer)
    
    def set_media_key(self, key: str, media_code: int, layer: Optional[int] = None) -> bool:
        """Set a key to a media control."""
        action = KeyAction(KeyActionType.MEDIA, bytes([media_code & 0xFF, (media_code >> 8) & 0xFF]))
        return self.remap_key(key, action, layer)
    
    def disable_key(self, key: str, layer: Optional[int] = None) -> bool:
        """Disable a key."""
        action = KeyAction(KeyActionType.NONE)
        return self.remap_key(key, action, layer)
    
    def clear_layer(self, layer: Optional[int] = None) -> None:
        """Clear all mappings in a layer."""
        layer_idx = layer if layer is not None else self.active_layer
        if layer_idx in self.layers:
            self.layers[layer_idx].keymap.clear()
    
    def reset_to_default(self) -> bool:
        """Reset keymap to factory defaults."""
        cmd = build_command(Command.KEY_RESET)
        try:
            response = self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
            _, _, success = parse_response(response)
            if success:
                for layer in self.layers.values():
                    layer.keymap.clear()
            return success
        except TransportError:
            return False
    
    def get_keymap(self, layer: Optional[int] = None) -> Dict[int, KeyAction]:
        """Get current keymap for a layer."""
        layer_idx = layer if layer is not None else self.active_layer
        if layer_idx in self.layers:
            return self.layers[layer_idx].keymap.copy()
        return {}
    
    def _send_remap(self, key_index: int, action: KeyAction) -> bool:
        """Send remap command to keyboard."""
        cmd = cmd_remap_key(key_index, action)
        try:
            response = self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
            _, _, success = parse_response(response)
            return success
        except TransportError:
            return False
    
    def export_keymap(self, layer: Optional[int] = None) -> dict:
        """Export keymap as JSON-serializable dict."""
        layer_idx = layer if layer is not None else self.active_layer
        keymap = self.get_keymap(layer_idx)
        
        result = {
            "layer": layer_idx,
            "layer_name": self.layers.get(layer_idx, Layer(layer_idx, "")).name,
            "keys": {}
        }
        
        for key_idx, action in keymap.items():
            # Find key name
            key_name = next((k for k, v in self._key_index_map.items() if v == key_idx), f"key_{key_idx}")
            result["keys"][key_name] = {
                "type": action.action_type.name,
                "data": action.data.hex() if action.data else ""
            }
        
        return result
    
    def import_keymap(self, data: dict) -> bool:
        """Import keymap from dict."""
        layer_idx = data.get("layer", 0)
        if layer_idx not in self.layers:
            self.add_layer(layer_idx, data.get("layer_name", f"Layer {layer_idx}"))
        
        success = True
        for key_name, action_data in data.get("keys", {}).items():
            key_idx = self._key_index_map.get(key_name)
            if key_idx is None:
                continue
            
            action_type = KeyActionType[action_data["type"]]
            action = KeyAction(action_type, bytes.fromhex(action_data["data"]))
            
            if not self._send_remap(key_idx, action):
                success = False
            else:
                self.layers[layer_idx].keymap[key_idx] = action
        
        return success