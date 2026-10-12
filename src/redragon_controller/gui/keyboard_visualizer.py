"""
Keyboard Visualizer Widget
Interactive keyboard layout for per-key RGB and remapping.
"""

from typing import Dict, Optional, Callable, List
from PySide6.QtCore import Qt, Signal, QRect, QPoint, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolTip
)
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QMouseEvent, QPolygon


class KeyboardKey:
    """Represents a single key on the keyboard."""
    
    def __init__(self, key_id: str, label: str, x: int, y: int, width: int = 50, height: int = 50, 
                 row: int = 0, col: int = 0, is_modifier: bool = False):
        self.key_id = key_id
        self.label = label
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.row = row
        self.col = col
        self.is_modifier = is_modifier
        
        # Visual state
        self.color = QColor(60, 60, 60)  # Default dark gray
        self.text_color = QColor(220, 220, 220)
        self.border_color = QColor(80, 80, 80)
        self.highlighted = False
        self.selected = False
        self.has_mapping = False
        self.has_macro = False
    
    def rect(self) -> QRect:
        return QRect(self.x, self.y, self.width, self.height)
    
    def contains(self, pos: QPoint) -> bool:
        return self.rect().contains(pos)
    
    def set_color(self, color: QColor):
        self.color = color
        # Auto-adjust text color for contrast
        luminance = (color.red() * 0.299 + color.green() * 0.587 + color.blue() * 0.114) / 255
        self.text_color = QColor(20, 20, 20) if luminance > 0.5 else QColor(235, 235, 235)
    
    def set_rgb(self, r: int, g: int, b: int):
        self.set_color(QColor(r, g, b))


class KeyboardVisualizer(QWidget):
    """Interactive keyboard widget with per-key RGB and remapping support."""
    
    # Signals
    key_clicked = Signal(str, object)  # key_id, key_object
    key_right_clicked = Signal(str, object, QPoint)  # key_id, key_object, global_pos
    key_hovered = Signal(str, object)  # key_id, key_object
    
    def __init__(self, layout_type: str = "tkl_87", parent=None):
        super().__init__(parent)
        self.layout_type = layout_type
        self.keys: Dict[str, KeyboardKey] = {}
        self.selected_key_id: Optional[str] = None
        self.hovered_key_id: Optional[str] = None
        self.mode = "rgb"  # "rgb" or "keymap"
        self.zone_colors: Dict[str, QColor] = {}
        self.custom_zone_keys: List[str] = []
        
        self.setMouseTracking(True)
        self.setMinimumSize(1000, 350)
        self._build_layout()
    
    def _build_layout(self):
        """Build the keyboard layout based on type."""
        if self.layout_type == "tkl_87":
            self._build_tkl_layout()
        elif self.layout_type == "compact_60":
            self._build_60_layout()
    
    def _build_tkl_layout(self):
        """Build TKL 87-key layout."""
        key_w, key_h = 50, 50
        gap = 4
        start_x, start_y = 20, 20
        
        # Row 0: Function row + Esc + PrtSc
        row_y = start_y
        keys_row0 = [
            ("esc", "Esc", 1.0), ("f1", "F1", 1.0), ("f2", "F2", 1.0), ("f3", "F3", 1.0),
            ("f4", "F4", 1.0), ("f5", "F5", 1.0), ("f6", "F6", 1.0), ("f7", "F7", 1.0),
            ("f8", "F8", 1.0), ("f9", "F9", 1.0), ("f10", "F10", 1.0), ("f11", "F11", 1.0),
            ("f12", "F12", 1.0), ("prtsc", "PrtSc", 1.0),
        ]
        self._add_row(keys_row0, row_y, start_x, key_w, key_h, gap, 0)
        
        # Row 1: Number row
        row_y += key_h + gap
        keys_row1 = [
            ("grave", "`", 1.0), ("1", "1", 1.0), ("2", "2", 1.0), ("3", "3", 1.0),
            ("4", "4", 1.0), ("5", "5", 1.0), ("6", "6", 1.0), ("7", "7", 1.0),
            ("8", "8", 1.0), ("9", "9", 1.0), ("0", "0", 1.0), ("minus", "-", 1.0),
            ("equal", "=", 1.0), ("backspace", "⌫", 1.5),
        ]
        self._add_row(keys_row1, row_y, start_x, key_w, key_h, gap, 1)
        
        # Row 2: QWERTY row
        row_y += key_h + gap
        keys_row2 = [
            ("tab", "Tab", 1.25), ("q", "Q", 1.0), ("w", "W", 1.0), ("e", "E", 1.0),
            ("r", "R", 1.0), ("t", "T", 1.0), ("y", "Y", 1.0), ("u", "U", 1.0),
            ("i", "I", 1.0), ("o", "O", 1.0), ("p", "P", 1.0), ("lbracket", "[", 1.0),
            ("rbracket", "]", 1.0), ("backslash", "\\", 1.25),
        ]
        self._add_row(keys_row2, row_y, start_x, key_w, key_h, gap, 2)
        
        # Row 3: ASDF row
        row_y += key_h + gap
        keys_row3 = [
            ("caps", "⇪", 1.5), ("a", "A", 1.0), ("s", "S", 1.0), ("d", "D", 1.0),
            ("f", "F", 1.0), ("g", "G", 1.0), ("h", "H", 1.0), ("j", "J", 1.0),
            ("k", "K", 1.0), ("l", "L", 1.0), ("semicolon", ";", 1.0),
            ("quote", "'", 1.0), ("enter", "↵", 1.75),
        ]
        self._add_row(keys_row3, row_y, start_x, key_w, key_h, gap, 3)
        
        # Row 4: ZXCV row
        row_y += key_h + gap
        keys_row4 = [
            ("lshift", "⇧", 2.0), ("z", "Z", 1.0), ("x", "X", 1.0), ("c", "C", 1.0),
            ("v", "V", 1.0), ("b", "B", 1.0), ("n", "N", 1.0), ("m", "M", 1.0),
            ("comma", ",", 1.0), ("period", ".", 1.0), ("slash", "/", 1.0),
            ("rshift", "⇧", 2.25),
        ]
        self._add_row(keys_row4, row_y, start_x, key_w, key_h, gap, 4)
        
        # Row 5: Bottom row
        row_y += key_h + gap
        keys_row5 = [
            ("lctrl", "Strg", 1.25), ("lwin", "⊞", 1.25), ("lalt", "Alt", 1.25),
            ("space", "Leertaste", 6.0), ("ralt", "AltGr", 1.25),
            ("fn", "Fn", 1.25), ("menu", "☰", 1.25), ("rctrl", "Strg", 1.25),
        ]
        self._add_row(keys_row5, row_y, start_x, key_w, key_h, gap, 5)
        
        # Navigation cluster (right side)
        nav_x = start_x + 14 * (key_w + gap) + 20
        nav_y = start_y + key_h + gap
        
        nav_keys = [
            ("insert", "Einfg", 0, 0), ("home", "Pos1", 1, 0), ("pageup", "Bild↑", 2, 0),
            ("delete", "Entf", 0, 1), ("end", "Ende", 1, 1), ("pagedown", "Bild↓", 2, 1),
        ]
        for key_id, label, col, row in nav_keys:
            x = nav_x + col * (key_w + gap)
            y = nav_y + row * (key_h + gap)
            self.keys[key_id] = KeyboardKey(key_id, label, x, y, key_w, key_h, row + 1, col + 14)
        
        # Arrow keys
        arrow_y = nav_y + 2 * (key_h + gap)
        arrow_keys = [
            ("up", "↑", 1, 0),
            ("left", "←", 0, 1), ("down", "↓", 1, 1), ("right", "→", 2, 1),
        ]
        for key_id, label, col, row in arrow_keys:
            x = nav_x + col * (key_w + gap)
            y = arrow_y + row * (key_h + gap)
            self.keys[key_id] = KeyboardKey(key_id, label, x, y, key_w, key_h, row + 3, col + 14)
        
        # Numpad
        num_x = nav_x + 3 * (key_w + gap) + 20
        num_y = start_y
        
        numpad_keys = [
            ("numlock", "Num", 0, 0), ("kp_divide", "/", 1, 0), ("kp_multiply", "*", 2, 0), ("kp_subtract", "-", 3, 0),
            ("kp_7", "7", 0, 1), ("kp_8", "8", 1, 1), ("kp_9", "9", 2, 1), ("kp_add", "+", 3, 1, 1.0, 2),
            ("kp_4", "4", 0, 2), ("kp_5", "5", 1, 2), ("kp_6", "6", 2, 2),
            ("kp_1", "1", 0, 3), ("kp_2", "2", 1, 3), ("kp_3", "3", 2, 3), ("kp_enter", "↵", 3, 2, 1.0, 2),
            ("kp_0", "0", 0, 4, 2.0), ("kp_decimal", ".", 2, 4),
        ]
        for item in numpad_keys:
            key_id, label, col, row = item[:4]
            w_mult = item[4] if len(item) > 4 else 1.0
            h_mult = item[5] if len(item) > 5 else 1.0
            x = num_x + col * (key_w + gap)
            y = num_y + row * (key_h + gap)
            w = key_w * w_mult + (w_mult - 1) * gap
            h = key_h * h_mult + (h_mult - 1) * gap
            self.keys[key_id] = KeyboardKey(key_id, label, x, y, w, h, row, col + 20)
    
    def _build_60_layout(self):
        """Build 60% compact layout."""
        # Simplified - similar to TKL but without nav cluster, arrows, numpad
        self._build_tkl_layout()
        # Remove keys not present on 60%
        for key_id in ["insert", "home", "pageup", "delete", "end", "pagedown",
                       "up", "left", "down", "right",
                       "numlock", "kp_divide", "kp_multiply", "kp_subtract",
                       "kp_7", "kp_8", "kp_9", "kp_add",
                       "kp_4", "kp_5", "kp_6", "kp_1", "kp_2", "kp_3", "kp_enter",
                       "kp_0", "kp_decimal"]:
            self.keys.pop(key_id, None)
    
    def _add_row(self, keys: List[tuple], y: int, start_x: int, key_w: int, key_h: int, gap: int, row: int):
        """Helper to add a row of keys."""
        x = start_x
        for i, item in enumerate(keys):
            key_id, label = item[0], item[1]
            w_mult = item[2] if len(item) > 2 else 1.0
            w = key_w * w_mult + (w_mult - 1) * gap
            self.keys[key_id] = KeyboardKey(key_id, label, x, y, w, key_h, row, i)
            x += w + gap
    
    def paintEvent(self, event):
        """Paint the keyboard."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background
        painter.fillRect(self.rect(), QColor(30, 30, 30))
        
        for key in self.keys.values():
            self._paint_key(painter, key)
    
    def _paint_key(self, painter: QPainter, key: KeyboardKey):
        """Paint a single key."""
        rect = key.rect()
        
        # Key background
        if key.selected:
            painter.setBrush(QBrush(QColor(0, 120, 215)))
            painter.setPen(QPen(QColor(0, 160, 255), 2))
        elif key.highlighted:
            painter.setBrush(QBrush(QColor(80, 80, 80)))
            painter.setPen(QPen(QColor(120, 120, 120), 1))
        else:
            painter.setBrush(QBrush(key.color))
            painter.setPen(QPen(key.border_color, 1))
        
        # Rounded rect
        painter.drawRoundedRect(rect, 4, 4)
        
        # Key label
        painter.setPen(key.text_color)
        font = QFont("Segoe UI", 9 if key.width > 40 else 8)
        if key.is_modifier:
            font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, key.label)
        
        # Indicators
        if key.has_mapping:
            # Small dot for remapped
            painter.setBrush(QBrush(QColor(255, 200, 0)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.right() - 8, rect.top() + 2, 6, 6)
        
        if key.has_macro:
            # M indicator
            painter.setBrush(QBrush(QColor(255, 100, 100)))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect.left() + 2, rect.top() + 2, 6, 6)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Handle mouse hover."""
        hovered = None
        for key_id, key in self.keys.items():
            if key.contains(event.pos()):
                hovered = key_id
                break
        
        if hovered != self.hovered_key_id:
            if self.hovered_key_id and self.hovered_key_id in self.keys:
                self.keys[self.hovered_key_id].highlighted = False
            if hovered:
                self.keys[hovered].highlighted = True
                self.key_hovered.emit(hovered, self.keys[hovered])
                # Show tooltip
                key = self.keys[hovered]
                QToolTip.showText(event.globalPosition().toPoint(), 
                                 f"{key.label} ({key.key_id})", self)
            else:
                QToolTip.hideText()
            self.hovered_key_id = hovered
            self.update()
    
    def mousePressEvent(self, event: QMouseEvent):
        """Handle mouse click."""
        for key_id, key in self.keys.items():
            if key.contains(event.pos()):
                if event.button() == Qt.LeftButton:
                    self.select_key(key_id)
                    self.key_clicked.emit(key_id, key)
                elif event.button() == Qt.RightButton:
                    self.key_right_clicked.emit(key_id, key, event.globalPosition().toPoint())
                break
    
    def select_key(self, key_id: str):
        """Select a key."""
        if self.selected_key_id and self.selected_key_id in self.keys:
            self.keys[self.selected_key_id].selected = False
        if key_id in self.keys:
            self.keys[key_id].selected = True
            self.selected_key_id = key_id
        self.update()
    
    def set_key_color(self, key_id: str, color: QColor):
        """Set key color for RGB mode."""
        if key_id in self.keys:
            self.keys[key_id].set_color(color)
            self.update()
    
    def set_keys_color(self, key_ids: List[str], color: QColor):
        """Set color for multiple keys."""
        for key_id in key_ids:
            self.set_key_color(key_id, color)
    
    def set_key_mapping(self, key_id: str, has_mapping: bool, has_macro: bool = False):
        """Set key mapping indicators."""
        if key_id in self.keys:
            self.keys[key_id].has_mapping = has_mapping
            self.keys[key_id].has_macro = has_macro
            self.update()
    
    def apply_zone(self, zone: str, color: QColor):
        """Apply color to a zone."""
        zone_map = {
            "all": list(self.keys.keys()),
            "left": [k for k in self.keys if self.keys[k].col < 7],
            "right": [k for k in self.keys if self.keys[k].col >= 7],
            "center": [k for k in self.keys if 4 <= self.keys[k].col <= 9],
            "wasd": ["w", "a", "s", "d"],
            "arrows": ["up", "left", "down", "right"],
            "function": [f"f{i}" for i in range(1, 13)] + ["esc"],
            "numbers": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"],
        }
        keys = zone_map.get(zone, [])
        self.set_keys_color(keys, color)
    
    def clear_all(self):
        """Reset all keys to default."""
        for key in self.keys.values():
            key.set_color(QColor(60, 60, 60))
            key.has_mapping = False
            key.has_macro = False
            key.selected = False
            key.highlighted = False
        self.selected_key_id = None
        self.update()
    
    def set_mode(self, mode: str):
        """Set visual mode: 'rgb' or 'keymap'."""
        self.mode = mode
        self.update()


class ZoneSelector(QWidget):
    """Widget for selecting keyboard zones."""
    
    zone_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        from .i18n import tr
        
        zones = [
            ("all", tr("rgb_zone_all")),
            ("left", tr("rgb_zone_left")),
            ("right", tr("rgb_zone_right")),
            ("center", tr("rgb_zone_center")),
            ("wasd", tr("rgb_zone_wasd")),
            ("arrows", tr("rgb_zone_arrows")),
            ("function", tr("rgb_zone_function")),
            ("numbers", tr("rgb_zone_numbers")),
            ("custom", tr("rgb_zone_custom")),
        ]
        
        from PySide6.QtWidgets import QComboBox
        self.combo = QComboBox()
        for zone_id, zone_name in zones:
            self.combo.addItem(zone_name, zone_id)
        self.combo.currentIndexChanged.connect(lambda: self.zone_changed.emit(self.combo.currentData()))
        layout.addWidget(self.combo)