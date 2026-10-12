"""
Redragon Keyboard Controller - Core Package
Cross-platform HID-based controller for Redragon RGB keyboards.
"""

__version__ = "0.1.0"
__author__ = "Redragon Controller Contributors"

from .hid_transport import HIDTransport, TransportError
from .protocol import (
    Command,
    ReportID,
    ProfileCommand,
    KeyActionType,
    build_command,
    parse_response,
)
from .rgb import RGBController, Effect, Color, Zone
from .keymap import KeyMap, Macro, Layer, KeyAction
from .profiles import ProfileManager, Profile

from .windows_service import (
    RedragonService,
    install_service,
    uninstall_service,
    start_service,
    stop_service,
    run_as_console,
    main as service_main,
)

# GUI (optional - requires PySide6)
try:
    from .gui import (
        MainWindow,
        TrayApplication,
        main as gui_main,
    )
    _GUI_AVAILABLE = True
except ImportError:
    _GUI_AVAILABLE = False

__all__ = [
    "HIDTransport",
    "TransportError",
    "Command",
    "ReportID",
    "ProfileCommand",
    "KeyActionType",
    "build_command",
    "parse_response",
    "RGBController",
    "Effect",
    "Color",
    "Zone",
    "KeyMap",
    "Macro",
    "Layer",
    "KeyAction",
    "ProfileManager",
    "Profile",
    "RedragonService",
    "install_service",
    "uninstall_service",
    "start_service",
    "stop_service",
    "run_as_console",
    "service_main",
]

if _GUI_AVAILABLE:
    __all__.extend([
        "MainWindow",
        "TrayApplication",
        "gui_main",
    ])