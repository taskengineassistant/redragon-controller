"""
Keymap Editor Panel
Per-key remapping with visual keyboard.
"""

from typing import Optional, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QPushButton, QListWidget, QListWidgetItem,
    QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QCheckBox, QSpinBox, QTabWidget
)
from PySide6.QtGui import QColor

from .i18n import tr
from .keyboard_visualizer import KeyboardVisualizer, KeyboardKey


class ActionDialog(QDialog):
    """Dialog for configuring key action."""
    
    def __init__(self, key: KeyboardKey, current_action: dict = None, macros: list = None, layers: list = None, parent=None):
        super().__init__(parent)
        self.key = key
        self.macros = macros or []
        self.layers = layers or ["Base", "Gaming", "Media", "Custom 1", "Custom 2", "Custom 3"]
        self.setWindowTitle(tr("action_title"))
        self.setModal(True)
        self.resize(400, 500)
        
        self._setup_ui()
        if current_action:
            self._load_action(current_action)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Key info
        info_label = QLabel(f"{tr('keymap_key')}: {self.key.label} ({self.key.key_id})")
        info_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 8px;")
        layout.addWidget(info_label)
        
        # Action type
        type_group = QGroupBox(tr("action_type"))
        type_layout = QVBoxLayout(type_group)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems([
            tr("keymap_type_keycode"),
            tr("keymap_type_macro"),
            tr("keymap_type_layer"),
            tr("keymap_type_media"),
            tr("keymap_type_none"),
        ])
        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        type_layout.addWidget(self.type_combo)
        layout.addWidget(type_group)
        
        # Stacked pages for each type
        self.pages = QTabWidget()
        self.pages.setTabBarVisible(False)
        layout.addWidget(self.pages, 1)
        
        # Page 0: Keycode
        self._setup_keycode_page()
        
        # Page 1: Macro
        self._setup_macro_page()
        
        # Page 2: Layer
        self._setup_layer_page()
        
        # Page 3: Media
        self._setup_media_page()
        
        # Page 4: None (empty)
        none_page = QWidget()
        none_layout = QVBoxLayout(none_page)
        none_layout.addWidget(QLabel(tr("keymap_type_none")))
        none_layout.addStretch()
        self.pages.addTab(none_page, "")
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _setup_keycode_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        
        self.keycode_edit = QLineEdit()
        self.keycode_edit.setPlaceholderText("z.B. 0x04 für 'A' oder 'A'")
        layout.addRow(tr("action_keycode"), self.keycode_edit)
        
        # Quick select buttons
        quick_layout = QHBoxLayout()
        common_keys = [
            ("A", "0x04"), ("B", "0x05"), ("C", "0x06"), ("D", "0x07"),
            ("E", "0x08"), ("F", "0x09"), ("G", "0x0A"), ("H", "0x0B"),
            ("I", "0x0C"), ("J", "0x0D"), ("K", "0x0E"), ("L", "0x0F"),
            ("M", "0x10"), ("N", "0x11"), ("O", "0x12"), ("P", "0x13"),
            ("Q", "0x14"), ("R", "0x15"), ("S", "0x16"), ("T", "0x17"),
            ("U", "0x18"), ("V", "0x19"), ("W", "0x1A"), ("X", "0x1B"),
            ("Y", "0x1C"), ("Z", "0x1D"),
            ("Space", "0x2C"), ("Enter", "0x28"), ("Esc", "0x29"),
            ("Tab", "0x2B"), ("Backspace", "0x2A"),
        ]
        for label, code in common_keys:
            btn = QPushButton(label)
            btn.setFixedWidth(50)
            btn.clicked.connect(lambda _, c=code: self.keycode_edit.setText(c))
            quick_layout.addWidget(btn)
        quick_layout.addStretch()
        
        from PySide6.QtWidgets import QScrollArea
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(120)
        container = QWidget()
        container.setLayout(quick_layout)
        scroll.setWidget(container)
        layout.addRow("Schnellauswahl:", scroll)
        
        self.pages.addTab(page, "")
    
    def _setup_macro_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        
        if self.macros:
            self.macro_combo = QComboBox()
            for macro in self.macros:
                self.macro_combo.addItem(macro["name"], macro["id"])
            layout.addWidget(QLabel(tr("action_macro")))
            layout.addWidget(self.macro_combo)
        else:
            layout.addWidget(QLabel("Keine Makros definiert"))
        
        layout.addStretch()
        self.pages.addTab(page, "")
    
    def _setup_layer_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        
        self.layer_combo = QComboBox()
        self.layer_combo.addItems(self.layers)
        layout.addRow(tr("action_layer"), self.layer_combo)
        
        self.momentary_check = QCheckBox(tr("action_layer_momentary"))
        self.momentary_check.setChecked(True)
        layout.addRow("", self.momentary_check)
        
        layout.addStretch()
        self.pages.addTab(page, "")
    
    def _setup_media_page(self):
        page = QWidget()
        layout = QFormLayout(page)
        
        self.media_combo = QComboBox()
        media_keys = [
            ("Play/Pause", "0xCD"), ("Stop", "0xB7"), ("Previous", "0xB6"), ("Next", "0xB5"),
            ("Mute", "0xE2"), ("Volume Up", "0xE9"), ("Volume Down", "0xEA"),
            ("Calculator", "0x92"), ("Browser", "0x96"), ("Mail", "0x9A"),
        ]
        for label, code in media_keys:
            self.media_combo.addItem(label, code)
        layout.addRow(tr("action_media"), self.media_combo)
        
        layout.addStretch()
        self.pages.addTab(page, "")
    
    def _on_type_change(self, index: int):
        self.pages.setCurrentIndex(index)
    
    def _load_action(self, action: dict):
        action_type = action.get("type", "keycode")
        type_map = {
            "keycode": 0, "macro": 1, "layer": 2, "media": 3, "none": 4
        }
        self.type_combo.setCurrentIndex(type_map.get(action_type, 0))
        
        if action_type == "keycode":
            self.keycode_edit.setText(action.get("data", ""))
        elif action_type == "macro":
            idx = self.macro_combo.findData(action.get("data"))
            if idx >= 0:
                self.macro_combo.setCurrentIndex(idx)
        elif action_type == "layer":
            self.layer_combo.setCurrentText(action.get("data", "Base"))
            self.momentary_check.setChecked(action.get("momentary", True))
        elif action_type == "media":
            idx = self.media_combo.findData(action.get("data"))
            if idx >= 0:
                self.media_combo.setCurrentIndex(idx)
    
    def get_action(self) -> dict:
        """Get configured action."""
        index = self.type_combo.currentIndex()
        
        if index == 0:  # Keycode
            return {"type": "keycode", "data": self.keycode_edit.text().strip()}
        elif index == 1:  # Macro
            return {"type": "macro", "data": self.macro_combo.currentData()}
        elif index == 2:  # Layer
            return {
                "type": "layer",
                "data": self.layer_combo.currentText(),
                "momentary": self.momentary_check.isChecked()
            }
        elif index == 3:  # Media
            return {"type": "media", "data": self.media_combo.currentData()}
        else:  # None
            return {"type": "none", "data": ""}


class KeymapPanel(QWidget):
    """Keymap editor panel."""
    
    # Signals
    apply_requested = Signal(dict)  # Full keymap config
    reset_requested = Signal()
    import_requested = Signal()
    export_requested = Signal()
    
    def __init__(self, keyboard: KeyboardVisualizer, parent=None):
        super().__init__(parent)
        self.keyboard = keyboard
        self.keymap: Dict[str, dict] = {}  # key_id -> action
        self.macros: list = []
        self.current_layer = 0
        
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Layer Selector
        layer_group = QGroupBox(tr("keymap_layer"))
        layer_layout = QHBoxLayout(layer_group)
        
        self.layer_combo = QComboBox()
        self.layer_combo.addItems([
            tr("keymap_base"),
            tr("keymap_gaming"),
            tr("keymap_media"),
            tr("keymap_custom"),
        ])
        self.layer_combo.currentIndexChanged.connect(self._on_layer_change)
        layer_layout.addWidget(self.layer_combo)
        layer_layout.addStretch()
        layout.addWidget(layer_group)
        
        # Selected Key Info
        self.key_info = QLabel(tr("select_key_prompt"))
        self.key_info.setStyleSheet("padding: 8px; background: #2d2d2d; border-radius: 4px;")
        self.key_info.setWordWrap(True)
        layout.addWidget(self.key_info)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_remap = QPushButton(tr("btn_remap"))
        self.btn_remap.setEnabled(False)
        self.btn_remap.clicked.connect(self._on_remap)
        btn_layout.addWidget(self.btn_remap)
        
        self.btn_reset_key = QPushButton(tr("btn_reset_key"))
        self.btn_reset_key.setEnabled(False)
        self.btn_reset_key.clicked.connect(self._on_reset_key)
        btn_layout.addWidget(self.btn_reset_key)
        
        btn_layout.addStretch()
        
        self.btn_reset_all = QPushButton(tr("btn_reset_all"))
        self.btn_reset_all.clicked.connect(self._on_reset_all)
        btn_layout.addWidget(self.btn_reset_all)
        
        self.btn_import = QPushButton(tr("btn_import_keymap"))
        self.btn_import.clicked.connect(self.import_requested.emit)
        btn_layout.addWidget(self.btn_import)
        
        self.btn_export = QPushButton(tr("btn_export_keymap"))
        self.btn_export.clicked.connect(self.export_requested.emit)
        btn_layout.addWidget(self.btn_export)
        
        layout.addLayout(btn_layout)
        
        # Current Mappings List
        list_group = QGroupBox("Aktuelle Belegungen (Ebene: Basis)")
        list_layout = QVBoxLayout(list_group)
        
        self.mapping_list = QListWidget()
        self.mapping_list.setAlternatingRowColors(True)
        list_layout.addWidget(self.mapping_list)
        
        layout.addWidget(list_group, 1)
        
        layout.addStretch()
    
    def _connect_signals(self):
        self.keyboard.key_clicked.connect(self._on_key_clicked)
        self.keyboard.key_right_clicked.connect(self._on_key_right_clicked)
    
    def _on_layer_change(self, index: int):
        self.current_layer = index
        self._refresh_mapping_list()
        self.key_info.setText(tr("select_key_prompt"))
        self.btn_remap.setEnabled(False)
        self.btn_reset_key.setEnabled(False)
    
    def _on_key_clicked(self, key_id: str, key: KeyboardKey):
        self._update_key_info(key_id, key)
    
    def _on_key_right_clicked(self, key_id: str, key: KeyboardKey, pos):
        self._update_key_info(key_id, key)
        # Show context menu
        from PySide6.QtWidgets import QMenu
        menu = QMenu(self)
        
        remap_action = menu.addAction(tr("btn_remap"))
        remap_action.triggered.connect(lambda: self._on_remap())
        
        if key_id in self.keymap:
            reset_action = menu.addAction(tr("btn_reset_key"))
            reset_action.triggered.connect(lambda: self._on_reset_key())
        
        menu.exec(pos)
    
    def _update_key_info(self, key_id: str, key: KeyboardKey):
        self.key_info.setText(
            f"{tr('keymap_key')}: {key.label} ({key_id})\n"
            f"{tr('keymap_action')}: {self._action_to_string(self.keymap.get(key_id))}"
        )
        self.btn_remap.setEnabled(True)
        self.btn_reset_key.setEnabled(key_id in self.keymap)
    
    def _action_to_string(self, action: dict) -> str:
        if not action:
            return "Standard"
        t = action.get("type", "")
        d = action.get("data", "")
        if t == "keycode":
            return f"Tastencode: {d}"
        elif t == "macro":
            macro = next((m for m in self.macros if m["id"] == d), None)
            return f"Makro: {macro['name'] if macro else d}"
        elif t == "layer":
            return f"Ebene: {d} ({'Momentan' if action.get('momentary') else 'Toggle'})"
        elif t == "media":
            return f"Medien: {d}"
        return "Unbekannt"
    
    def _on_remap(self):
        if not hasattr(self, 'selected_key_id'):
            return
        
        key = self.keyboard.keys.get(self.selected_key_id)
        if not key:
            return
        
        current = self.keymap.get(self.selected_key_id)
        dialog = ActionDialog(key, current, self.macros, parent=self)
        if dialog.exec() == QDialog.Accepted:
            action = dialog.get_action()
            if action["type"] == "none":
                self.keymap.pop(self.selected_key_id, None)
            else:
                self.keymap[self.selected_key_id] = action
            
            # Update visual
            self.keyboard.set_key_mapping(
                self.selected_key_id,
                self.selected_key_id in self.keymap,
                action.get("type") == "macro"
            )
            self._refresh_mapping_list()
            self._update_key_info(self.selected_key_id, key)
    
    def _on_reset_key(self):
        if hasattr(self, 'selected_key_id'):
            self.keymap.pop(self.selected_key_id, None)
            key = self.keyboard.keys.get(self.selected_key_id)
            if key:
                self.keyboard.set_key_mapping(self.selected_key_id, False)
                self._update_key_info(self.selected_key_id, key)
            self._refresh_mapping_list()
    
    def _on_reset_all(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, tr("dialog_confirm"), tr("dialog_delete_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.keymap.clear()
            for key in self.keyboard.keys.values():
                key.has_mapping = False
                key.has_macro = False
            self.keyboard.update()
            self._refresh_mapping_list()
            self.reset_requested.emit()
    
    def _refresh_mapping_list(self):
        self.mapping_list.clear()
        for key_id, action in sorted(self.keymap.items()):
            key = self.keyboard.keys.get(key_id)
            label = key.label if key else key_id
            item = QListWidgetItem(f"{label} ({key_id}): {self._action_to_string(action)}")
            item.setData(Qt.UserRole, key_id)
            self.mapping_list.addItem(item)
    
    def set_macros(self, macros: list):
        self.macros = macros
    
    def get_keymap(self) -> dict:
        return dict(self.keymap)
    
    def load_keymap(self, keymap: dict):
        self.keymap = dict(keymap)
        # Update visual indicators
        for key_id, action in self.keymap.items():
            self.keyboard.set_key_mapping(
                key_id, True, action.get("type") == "macro"
            )
        self._refresh_mapping_list()