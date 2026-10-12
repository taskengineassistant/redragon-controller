"""
Tray App Entry Point
Connects the GUI with the backend controller.
"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer, Signal, QObject, Slot

from .gui import TrayApplication, main as gui_main
from .hid_transport import HIDTransport
from .rgb import RGBController
from .keymap import KeyMap
from .profiles import ProfileManager
from .protocol import ReportID, RGBCommand, RGBZone, RGBEffect


class BackendController(QObject):
    """Backend controller connecting GUI to hardware."""
    
    # Signals to GUI
    device_changed = Signal(bool, str, str, str)  # connected, name, firmware, profile
    profile_changed = Signal(str, int)  # name, slot
    
    def __init__(self):
        super().__init__()
        self.transport = None
        self.rgb = None
        self.keymap = None
        self.profiles = None
        self.current_profile = None
        self.current_slot = 0
        
        # Auto-reconnect timer
        self.reconnect_timer = QTimer()
        self.reconnect_timer.setInterval(5000)
        self.reconnect_timer.timeout.connect(self._try_connect)
        self.reconnect_timer.start()
        
        # Initial connection
        self._try_connect()
    
    def _try_connect(self):
        """Try to connect to Redragon device."""
        try:
            devices = HIDTransport.discover()
            if not devices:
                if self.transport:
                    self._disconnect()
                return
            
            # Use first found device
            device = devices[0]
            
            if self.transport and self.transport.is_connected:
                # Already connected to this device?
                if (self.transport.device_info and 
                    self.transport.device_info.vendor_id == device.vendor_id and
                    self.transport.device_info.product_id == device.product_id):
                    return
            
            self._connect_device(device)
            
        except Exception as e:
            print(f"Connection error: {e}")
            self._disconnect()
    
    def _connect_device(self, device):
        """Connect to specific device."""
        try:
            self.transport = HIDTransport(
                vendor_id=device.vendor_id,
                product_id=device.product_id,
                path=device.path
            )
            self.transport.connect()
            
            self.rgb = RGBController(self.transport)
            self.keymap = KeyMap(self.transport)
            self.profiles = ProfileManager(self.transport, self.rgb, self.keymap)
            
            # Load default profile
            self.profiles.load_profile("Default", from_onboard=False)
            
            device_name = self.transport.get_device_name()
            firmware = "Unknown"
            if self.transport.device_info:
                firmware = f"VID:0x{self.transport.device_info.vendor_id:04x} PID:0x{self.transport.device_info.product_id:04x}"
            
            self.device_changed.emit(True, device_name, firmware, self.current_profile or "Default")
            
            # Stop reconnect timer
            self.reconnect_timer.stop()
            
        except Exception as e:
            print(f"Failed to connect: {e}")
            self._disconnect()
    
    def _disconnect(self):
        """Disconnect from device."""
        if self.transport:
            try:
                self.transport.disconnect()
            except:
                pass
            self.transport = None
            self.rgb = None
            self.keymap = None
            self.profiles = None
        
        self.device_changed.emit(False, "", "", "")
        self.reconnect_timer.start()
    
    # === Public API for GUI ===
    
    def is_connected(self) -> bool:
        return self.transport is not None and self.transport.is_connected
    
    def get_device_name(self) -> str:
        return self.transport.get_device_name() if self.transport else ""
    
    # RGB Control
    def set_static_color(self, color_hex: str, zone: str = "all", brightness: int = 255):
        if not self.rgb:
            return False
        r = int(color_hex[1:3], 16)
        g = int(color_hex[3:5], 16)
        b = int(color_hex[5:7], 16)
        
        from .rgb import Color, RGBZone
        color = Color(r, g, b, brightness)
        zone_map = {
            "all": RGBZone.ALL, "left": RGBZone.LEFT, "right": RGBZone.RIGHT,
            "center": RGBZone.CENTER, "wasd": RGBZone.WASD, "arrows": RGBZone.ARROWS,
            "function": RGBZone.FUNCTION_ROW, "numbers": RGBZone.NUMBER_ROW,
        }
        return self.rgb.set_static_color(color, zone_map.get(zone, RGBZone.ALL))
    
    def set_effect(self, effect: str, color_hex: str = None, speed: int = 128, 
                   direction: int = 0, zone: str = "all", brightness: int = 255):
        if not self.rgb:
            return False
        
        from .rgb import RGBEffect, RGBZone, Color, EffectSpeed, EffectDirection
        eff = RGBEffect[effect.upper()]
        color = None
        if color_hex:
            r = int(color_hex[1:3], 16)
            g = int(color_hex[3:5], 16)
            b = int(color_hex[5:7], 16)
            color = Color(r, g, b, brightness)
        
        zone_map = {
            "all": RGBZone.ALL, "left": RGBZone.LEFT, "right": RGBZone.RIGHT,
            "center": RGBZone.CENTER, "wasd": RGBZone.WASD, "arrows": RGBZone.ARROWS,
            "function": RGBZone.FUNCTION_ROW, "numbers": RGBZone.NUMBER_ROW,
        }
        return self.rgb.set_effect(eff, color, speed, direction, zone_map.get(zone, RGBZone.ALL))
    
    def rgb_off(self):
        if self.rgb:
            return self.rgb.off()
        return False
    
    def set_brightness(self, level: int):
        if self.rgb:
            return self.rgb.set_brightness(max(0, min(255, level)))
        return False
    
    # Keymap
    def remap_key(self, key: str, action: dict, layer: int = 0):
        if not self.keymap:
            return False
        from .keymap import KeyAction, KeyActionType
        action_type = KeyActionType[action["type"].upper()]
        data = bytes.fromhex(action.get("data", "")) if action.get("data") else b""
        key_action = KeyAction(action_type, data)
        return self.keymap.remap_key(key, key_action, layer)
    
    def set_layer_key(self, key: str, layer_index: int, momentary: bool = True, layer: int = 0):
        if not self.keymap:
            return False
        return self.keymap.set_layer_key(key, layer_index, momentary, layer)
    
    def reset_keymap(self):
        if not self.keymap:
            return False
        return self.keymap.reset_to_default()
    
    # Profiles
    def save_profile(self, name: str, slot: int = 0, onboard: bool = True, local: bool = True):
        if not self.profiles:
            return False
        profile = self.profiles.create_profile(name, slot)
        return self.profiles.save_profile(profile, onboard, local)
    
    def load_profile(self, name: str, from_onboard: bool = False):
        if not self.profiles:
            return False
        profile = self.profiles.load_profile(name, from_onboard)
        if profile:
            self.current_profile = name
            self.profile_changed.emit(name, profile.slot)
            return True
        return False
    
    def list_profiles(self):
        if not self.profiles:
            return []
        return self.profiles.list_profiles()
    
    def delete_profile(self, name: str, local: bool = True):
        if not self.profiles:
            return False
        return self.profiles.delete_profile(name, from_onboard=False, from_local=local)
    
    def set_profile_slot(self, slot: int):
        """Activate onboard profile slot."""
        if not self.profiles or not self.transport:
            return False
        # Send command to activate slot
        from .protocol import cmd_activate_profile, ReportID
        cmd = cmd_activate_profile(slot)
        self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
        return True
    
    # Settings
    def set_ui_callbacks(self, on_device_change=None, on_profile_change=None):
        if on_device_change:
            self.device_changed.connect(on_device_change)
        if on_profile_change:
            self.profile_changed.connect(on_profile_change)


def create_tray_app(controller=None):
    """Create and configure the tray application."""
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("Redragon Controller")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)
    
    # High DPI
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    tray_app = TrayApplication()
    tray_app.initialize(app, controller)
    
    return tray_app


def main():
    """Main entry point."""
    # Create backend controller
    controller = BackendController()
    
    # Create tray app
    tray_app = create_tray_app(controller)
    
    # Run
    return tray_app.run()


if __name__ == "__main__":
    sys.exit(main())