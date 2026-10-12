"""
RGB Control Panel Widget
Controls for RGB lighting effects, colors, zones.
"""

from typing import Optional
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QSlider, QPushButton, QColorDialog, QCheckBox,
    QGridLayout, QSpinBox, QFrame
)
from PySide6.QtGui import QColor, QPixmap, QPainter, QBrush

from .i18n import tr
from .keyboard_visualizer import KeyboardVisualizer, ZoneSelector


class ColorButton(QPushButton):
    """Button that shows and selects a color."""
    
    color_changed = Signal(QColor)
    
    def __init__(self, color: QColor = None, parent=None):
        super().__init__(parent)
        self._color = color or QColor(255, 0, 0)
        self.setFixedSize(40, 40)
        self.clicked.connect(self._pick_color)
        self._update_icon()
    
    def _update_icon(self):
        """Update button icon with current color."""
        pixmap = QPixmap(36, 36)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(2, 2, 32, 32, 4, 4)
        painter.end()
        self.setIcon(pixmap)
        self.setIconSize(pixmap.size())
        self.setStyleSheet(f"""
            QPushButton {{
                border: 2px solid #555;
                border-radius: 6px;
                background: #2d2d2d;
            }}
            QPushButton:hover {{
                border-color: #888;
            }}
        """)
    
    def _pick_color(self):
        color = QColorDialog.getColor(self._color, self, tr("rgb_color"))
        if color.isValid():
            self.set_color(color)
    
    def set_color(self, color: QColor):
        self._color = color
        self._update_icon()
        self.color_changed.emit(color)
    
    def color(self) -> QColor:
        return self._color


class EffectSelector(QComboBox):
    """Dropdown for selecting RGB effect."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._populate()
    
    def _populate(self):
        effects = [
            ("static", tr("rgb_static")),
            ("breathing", tr("rgb_breathing")),
            ("wave", tr("rgb_wave")),
            ("ripple", tr("rgb_ripple")),
            ("reactive", tr("rgb_reactive")),
            ("spectrum", tr("rgb_spectrum")),
            ("rainbow_wave", tr("rgb_rainbow_wave")),
            ("starlight", tr("rgb_starlight")),
            ("scan", tr("rgb_scan")),
            ("off", tr("rgb_off")),
        ]
        for effect_id, effect_name in effects:
            self.addItem(effect_name, effect_id)
    
    def current_effect(self) -> str:
        return self.currentData()
    
    def set_effect(self, effect_id: str):
        idx = self.findData(effect_id)
        if idx >= 0:
            self.setCurrentIndex(idx)


class SpeedSlider(QWidget):
    """Speed slider with label."""
    
    value_changed = Signal(int)
    
    def __init__(self, min_val=0, max_val=255, default=128, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(tr("rgb_speed"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setValue(default)
        self.value_label = QLabel(str(default))
        self.value_label.setFixedWidth(40)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        
        self.slider.valueChanged.connect(self._on_change)
    
    def _on_change(self, value: int):
        self.value_label.setText(str(value))
        self.value_changed.emit(value)
    
    def value(self) -> int:
        return self.slider.value()
    
    def set_value(self, value: int):
        self.slider.setValue(value)


class DirectionSelector(QComboBox):
    """Dropdown for effect direction."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._populate()
    
    def _populate(self):
        directions = [
            (0, tr("rgb_direction_ltr")),
            (1, tr("rgb_direction_rtl")),
            (2, tr("rgb_direction_ttb")),
            (3, tr("rgb_direction_btt")),
            (4, tr("rgb_direction_center_out")),
            (5, tr("rgb_direction_out_center")),
        ]
        for dir_id, dir_name in directions:
            self.addItem(dir_name, dir_id)
    
    def current_direction(self) -> int:
        return self.currentData()
    
    def set_direction(self, direction: int):
        idx = self.findData(direction)
        if idx >= 0:
            self.setCurrentIndex(idx)


class BrightnessSlider(QWidget):
    """Brightness slider with label."""
    
    value_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel(tr("rgb_brightness"))
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 255)
        self.slider.setValue(255)
        self.value_label = QLabel("255")
        self.value_label.setFixedWidth(40)
        self.value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(self.label)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.value_label)
        
        self.slider.valueChanged.connect(self._on_change)
    
    def _on_change(self, value: int):
        self.value_label.setText(str(value))
        self.value_changed.emit(value)
    
    def value(self) -> int:
        return self.slider.value()


class RGBControlPanel(QWidget):
    """Main RGB control panel."""
    
    # Signals
    apply_requested = Signal(dict)  # Full RGB config
    save_profile_requested = Signal(str)  # Profile name
    
    def __init__(self, keyboard: KeyboardVisualizer, parent=None):
        super().__init__(parent)
        self.keyboard = keyboard
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Effect Selection
        effect_group = QGroupBox(tr("rgb_mode"))
        effect_layout = QHBoxLayout(effect_group)
        
        self.effect_selector = EffectSelector()
        self.effect_selector.currentIndexChanged.connect(self._on_effect_change)
        effect_layout.addWidget(self.effect_selector, 1)
        
        layout.addWidget(effect_group)
        
        # Color Selection
        color_group = QGroupBox(tr("rgb_color"))
        color_layout = QHBoxLayout(color_group)
        
        self.color_button = ColorButton(QColor(255, 0, 0))
        self.color_button.color_changed.connect(self._on_color_change)
        color_layout.addWidget(self.color_button)
        
        # Preset colors
        presets = [
            QColor(255, 0, 0),    # Red
            QColor(0, 255, 0),    # Green
            QColor(0, 0, 255),    # Blue
            QColor(255, 255, 255),# White
            QColor(255, 0, 255),  # Magenta
            QColor(0, 255, 255),  # Cyan
            QColor(255, 255, 0),  # Yellow
            QColor(128, 0, 255),  # Purple
            QColor(255, 128, 0),  # Orange
            QColor(0, 128, 255),  # Light Blue
        ]
        for preset in presets:
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            pixmap = QPixmap(24, 24)
            pixmap.fill(preset)
            btn.setIcon(pixmap)
            btn.setIconSize(pixmap.size())
            btn.clicked.connect(lambda _, c=preset: self.color_button.set_color(c))
            btn.setToolTip(f"RGB({preset.red()}, {preset.green()}, {preset.blue()})")
            color_layout.addWidget(btn)
        
        color_layout.addStretch()
        layout.addWidget(color_group)
        
        # Zone Selector
        zone_group = QGroupBox(tr("rgb_zone"))
        zone_layout = QHBoxLayout(zone_group)
        
        self.zone_selector = ZoneSelector()
        self.zone_selector.zone_changed.connect(self._on_zone_change)
        zone_layout.addWidget(self.zone_selector.combo)
        zone_layout.addStretch()
        
        layout.addWidget(zone_group)
        
        # Brightness
        self.brightness_slider = BrightnessSlider()
        self.brightness_slider.value_changed.connect(self._on_brightness_change)
        layout.addWidget(self.brightness_slider)
        
        # Effect Parameters (dynamic based on effect)
        self.params_group = QGroupBox("Parameter")
        self.params_layout = QVBoxLayout(self.params_group)
        layout.addWidget(self.params_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton(tr("btn_apply_rgb"))
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: #0078d7;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #1084d8; }
            QPushButton:pressed { background: #005a9e; }
        """)
        self.btn_apply.clicked.connect(self._emit_apply)
        btn_layout.addWidget(self.btn_apply)
        
        self.btn_save_profile = QPushButton(tr("btn_save_rgb"))
        self.btn_save_profile.clicked.connect(self._emit_save_profile)
        btn_layout.addWidget(self.btn_save_profile)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
        
        # Initial effect param setup
        self._on_effect_change(0)
    
    def _connect_signals(self):
        """Connect keyboard signals."""
        self.keyboard.key_clicked.connect(self._on_key_clicked)
    
    def _on_effect_change(self, index: int):
        """Update parameter controls based on selected effect."""
        # Clear existing
        while self.params_layout.count():
            item = self.params_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        effect = self.effect_selector.current_effect()
        
        if effect in ["static", "off"]:
            # No extra params for static/off
            pass
        
        elif effect in ["breathing", "starlight", "scan"]:
            # Speed only
            self.speed_slider = SpeedSlider(default=64 if effect == "breathing" else 128)
            self.speed_slider.value_changed.connect(self._on_speed_change)
            self.params_layout.addWidget(self.speed_slider)
        
        elif effect in ["wave", "ripple", "rainbow_wave"]:
            # Speed + Direction
            self.speed_slider = SpeedSlider(default=128)
            self.speed_slider.value_changed.connect(self._on_speed_change)
            self.params_layout.addWidget(self.speed_slider)
            
            self.direction_selector = DirectionSelector()
            self.direction_selector.currentIndexChanged.connect(self._on_direction_change)
            self.params_layout.addWidget(self.direction_selector)
        
        elif effect in ["reactive"]:
            # Speed only (reactive speed)
            self.speed_slider = SpeedSlider(default=192)
            self.speed_slider.value_changed.connect(self._on_speed_change)
            self.params_layout.addWidget(self.speed_slider)
        
        elif effect == "spectrum":
            # Speed only
            self.speed_slider = SpeedSlider(default=128)
            self.speed_slider.value_changed.connect(self._on_speed_change)
            self.params_layout.addWidget(self.speed_slider)
    
    def _on_color_change(self, color: QColor):
        """Apply color to selected zone on keyboard."""
        zone = self.zone_selector.combo.currentData()
        self.keyboard.apply_zone(zone, color)
    
    def _on_zone_change(self, zone: str):
        """Update keyboard preview for zone."""
        self._on_color_change(self.color_button.color())
    
    def _on_brightness_change(self, value: int):
        pass  # Applied on apply
    
    def _on_speed_change(self, value: int):
        pass  # Applied on apply
    
    def _on_direction_change(self, index: int):
        pass  # Applied on apply
    
    def _on_key_clicked(self, key_id: str, key):
        """Handle direct key click for custom zone."""
        zone = self.zone_selector.combo.currentData()
        if zone == "custom":
            # Toggle key in custom zone
            if key_id in self.keyboard.custom_zone_keys:
                self.keyboard.custom_zone_keys.remove(key_id)
                key.set_color(QColor(60, 60, 60))
            else:
                self.keyboard.custom_zone_keys.append(key_id)
                key.set_color(self.color_button.color())
    
    def _emit_apply(self):
        """Emit apply signal with full config."""
        config = {
            "effect": self.effect_selector.current_effect(),
            "color": self.color_button.color().name(QColor.HexRgb),
            "brightness": self.brightness_slider.value(),
            "zone": self.zone_selector.combo.currentData(),
            "custom_keys": self.keyboard.custom_zone_keys,
        }
        if hasattr(self, 'speed_slider'):
            config["speed"] = self.speed_slider.value()
        if hasattr(self, 'direction_selector'):
            config["direction"] = self.direction_selector.current_direction()
        
        self.apply_requested.emit(config)
    
    def _emit_save_profile(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(self, tr("dialog_confirm"), tr("profile_name"))
        if ok and name:
            self.save_profile_requested.emit(name)
    
    def load_config(self, config: dict):
        """Load config into UI."""
        self.effect_selector.set_effect(config.get("effect", "static"))
        self.color_button.set_color(QColor(config.get("color", "#ff0000")))
        self.brightness_slider.slider.setValue(config.get("brightness", 255))
        
        zone = config.get("zone", "all")
        idx = self.zone_selector.combo.findData(zone)
        if idx >= 0:
            self.zone_selector.combo.setCurrentIndex(idx)
        
        if "custom_keys" in config:
            self.keyboard.custom_zone_keys = config["custom_keys"]
        
        if "speed" in config and hasattr(self, 'speed_slider'):
            self.speed_slider.set_value(config["speed"])
        if "direction" in config and hasattr(self, 'direction_selector'):
            self.direction_selector.set_direction(config["direction"])