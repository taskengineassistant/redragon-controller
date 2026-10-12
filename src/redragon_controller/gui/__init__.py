"""
Redragon Controller GUI Package
Modern German GUI with System Tray support.
"""

from .i18n import tr, TRANSLATIONS
from .keyboard_visualizer import KeyboardVisualizer, KeyboardKey, ZoneSelector
from .rgb_panel import RGBControlPanel, ColorButton, EffectSelector, SpeedSlider, DirectionSelector, BrightnessSlider
from .keymap_panel import KeymapPanel, ActionDialog
from .macros_panel import MacrosPanel, MacroRecorder, MacroEditorDialog
from .profiles_panel import ProfilesPanel, ProfileDialog
from .settings_panel import SettingsPanel
from .dashboard_panel import DashboardPanel, DeviceStatusWidget, QuickActionButton
from .main_window import MainWindow, TrayApplication, main

__all__ = [
    "tr",
    "TRANSLATIONS",
    "KeyboardVisualizer",
    "KeyboardKey",
    "ZoneSelector",
    "RGBControlPanel",
    "ColorButton",
    "EffectSelector",
    "SpeedSlider",
    "DirectionSelector",
    "BrightnessSlider",
    "KeymapPanel",
    "ActionDialog",
    "MacrosPanel",
    "MacroRecorder",
    "MacroEditorDialog",
    "ProfilesPanel",
    "ProfileDialog",
    "SettingsPanel",
    "DashboardPanel",
    "DeviceStatusWidget",
    "QuickActionButton",
    "MainWindow",
    "TrayApplication",
    "main",
]