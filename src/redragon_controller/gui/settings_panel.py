"""
Settings Panel
Application settings and preferences.
"""

from PySide6.QtCore import Qt, Signal, QSettings
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QSpinBox, QPushButton, QLineEdit,
    QFileDialog, QMessageBox, QFormLayout
)
from PySide6.QtGui import QIcon

from .i18n import tr


class SettingsPanel(QWidget):
    """Application settings panel."""
    
    # Signals
    settings_changed = Signal(dict)
    autostart_changed = Signal(bool)
    theme_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = QSettings("RedragonController", "RedragonController")
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # General Settings
        general_group = QGroupBox("Allgemein")
        general_layout = QFormLayout(general_group)
        
        self.language_combo = QComboBox()
        self.language_combo.addItems([tr("settings_language_de"), tr("settings_language_en")])
        self.language_combo.currentTextChanged.connect(self._on_setting_change)
        general_layout.addRow(tr("settings_language"), self.language_combo)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([tr("settings_theme_dark"), tr("settings_theme_light"), tr("settings_theme_system")])
        self.theme_combo.currentTextChanged.connect(self._on_theme_change)
        general_layout.addRow(tr("settings_theme"), self.theme_combo)
        
        layout.addWidget(general_group)
        
        # Startup Settings
        startup_group = QGroupBox("Startverhalten")
        startup_layout = QVBoxLayout(startup_group)
        
        self.autostart_check = QCheckBox(tr("settings_autostart"))
        self.autostart_check.toggled.connect(self._on_autostart_change)
        startup_layout.addWidget(self.autostart_check)
        
        self.minimize_tray_check = QCheckBox(tr("settings_minimize_tray"))
        self.minimize_tray_check.setChecked(True)
        self.minimize_tray_check.toggled.connect(self._on_setting_change)
        startup_layout.addWidget(self.minimize_tray_check)
        
        self.close_tray_check = QCheckBox(tr("settings_close_tray"))
        self.close_tray_check.setChecked(True)
        self.close_tray_check.toggled.connect(self._on_setting_change)
        startup_layout.addWidget(self.close_tray_check)
        
        layout.addWidget(startup_group)
        
        # Device Settings
        device_group = QGroupBox("Gerät")
        device_layout = QFormLayout(device_group)
        
        self.device_combo = QComboBox()
        self.device_combo.addItem("Auto (erstes gefunden)", "auto")
        device_layout.addRow(tr("settings_device"), self.device_combo)
        
        self.api_port_spin = QSpinBox()
        self.api_port_spin.setRange(0, 65535)
        self.api_port_spin.setValue(0)
        self.api_port_spin.setSpecialValueText("Deaktiviert")
        self.api_port_spin.valueChanged.connect(self._on_setting_change)
        device_layout.addRow(tr("settings_api_port"), self.api_port_spin)
        
        layout.addWidget(device_group)
        
        # Logging
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout(log_group)
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setCurrentText("INFO")
        self.log_level_combo.currentTextChanged.connect(self._on_setting_change)
        log_layout.addRow(tr("settings_log_level"), self.log_level_combo)
        
        self.log_file_edit = QLineEdit()
        self.log_file_edit.setPlaceholderText("Leer = nur Konsole")
        self.log_file_edit.textChanged.connect(self._on_setting_change)
        browse_btn = QPushButton("...")
        browse_btn.setFixedWidth(30)
        browse_btn.clicked.connect(self._browse_log_file)
        
        log_file_layout = QHBoxLayout()
        log_file_layout.addWidget(self.log_file_edit)
        log_file_layout.addWidget(browse_btn)
        log_layout.addRow("Log-Datei:", log_file_layout)
        
        layout.addWidget(log_group)
        
        # Advanced
        advanced_group = QGroupBox("Erweitert")
        advanced_layout = QFormLayout(advanced_group)
        
        self.check_updates_check = QCheckBox(tr("settings_check_updates"))
        self.check_updates_check.setChecked(True)
        advanced_layout.addRow("", self.check_updates_check)
        
        self.reset_hid_check = QCheckBox("HID bei Start zurücksetzen")
        advanced_layout.addRow("", self.reset_hid_check)
        
        layout.addWidget(advanced_group)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_save = QPushButton(tr("btn_save_settings"))
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #0078d7;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #1084d8; }
        """)
        self.btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.btn_save)
        
        self.btn_reset = QPushButton(tr("btn_reset_settings"))
        self.btn_reset.clicked.connect(self._reset_settings)
        btn_layout.addWidget(self.btn_reset)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        layout.addStretch()
    
    def _browse_log_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Log-Datei wählen", "", "Log Files (*.log);;All Files (*)")
        if path:
            self.log_file_edit.setText(path)
    
    def _load_settings(self):
        self.language_combo.setCurrentText(self.settings.value("language", tr("settings_language_de")))
        self.theme_combo.setCurrentText(self.settings.value("theme", tr("settings_theme_dark")))
        self.autostart_check.setChecked(self.settings.value("autostart", False, type=bool))
        self.minimize_tray_check.setChecked(self.settings.value("minimize_tray", True, type=bool))
        self.close_tray_check.setChecked(self.settings.value("close_tray", True, type=bool))
        self.api_port_spin.setValue(self.settings.value("api_port", 0, type=int))
        self.log_level_combo.setCurrentText(self.settings.value("log_level", "INFO"))
        self.log_file_edit.setText(self.settings.value("log_file", ""))
        self.check_updates_check.setChecked(self.settings.value("check_updates", True, type=bool))
        self.reset_hid_check.setChecked(self.settings.value("reset_hid", False, type=bool))
        
        # Apply theme
        self._apply_theme(self.theme_combo.currentText())
    
    def _apply_theme(self, theme: str):
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if theme == tr("settings_theme_dark"):
            app.setStyleSheet(self._dark_stylesheet())
        elif theme == tr("settings_theme_light"):
            app.setStyleSheet(self._light_stylesheet())
        else:
            app.setStyleSheet("")  # System default
    
    def _dark_stylesheet(self) -> str:
        return """
        QWidget {
            background: #1e1e1e;
            color: #e0e0e0;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            border: 1px solid #3d3d3d;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #0078d7;
        }
        QPushButton {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover { background: #3d3d3d; border-color: #555; }
        QPushButton:pressed { background: #1a1a1a; }
        QPushButton:disabled { background: #1a1a1a; color: #666; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
            border-color: #0078d7;
        }
        QComboBox::drop-down { border: none; width: 20px; }
        QListWidget {
            background: #252525;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
        }
        QListWidget::item { padding: 8px; border-bottom: 1px solid #2d2d2d; }
        QListWidget::item:selected { background: #0078d7; color: white; }
        QListWidget::item:alternate { background: #2d2d2d; }
        QTableWidget {
            background: #252525;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            gridline-color: #333;
        }
        QHeaderView::section {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3d3d3d;
            padding: 6px;
            font-weight: bold;
        }
        QScrollBar:vertical {
            background: #1e1e1e;
            width: 10px;
            border: none;
        }
        QScrollBar::handle:vertical {
            background: #444;
            border-radius: 5px;
            min-height: 30px;
        }
        QScrollBar::handle:vertical:hover { background: #555; }
        QToolTip {
            background: #2d2d2d;
            color: #e0e0e0;
            border: 1px solid #3d3d3d;
            border-radius: 4px;
            padding: 6px;
        }
        """
    
    def _light_stylesheet(self) -> str:
        return """
        QWidget {
            background: #f5f5f5;
            color: #202020;
            font-family: 'Segoe UI', sans-serif;
            font-size: 13px;
        }
        QGroupBox {
            border: 1px solid #d0d0d0;
            border-radius: 6px;
            margin-top: 12px;
            padding-top: 16px;
            font-weight: bold;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #0078d7;
        }
        QPushButton {
            background: #ffffff;
            color: #202020;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 8px 16px;
        }
        QPushButton:hover { background: #f0f0f0; border-color: #b0b0b0; }
        QPushButton:pressed { background: #e0e0e0; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox {
            background: #ffffff;
            color: #202020;
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 6px;
        }
        QListWidget { background: #ffffff; border: 1px solid #d0d0d0; }
        QTableWidget { background: #ffffff; border: 1px solid #d0d0d0; }
        """
    
    def _on_setting_change(self):
        # Real-time preview for theme
        if self.sender() == self.theme_combo:
            self._apply_theme(self.theme_combo.currentText())
    
    def _on_theme_change(self, theme: str):
        self._apply_theme(theme)
        self.theme_changed.emit(theme)
        self._on_setting_change()
    
    def _on_autostart_change(self, checked: bool):
        self.autostart_changed.emit(checked)
        self._on_setting_change()
    
    def _save_settings(self):
        self.settings.setValue("language", self.language_combo.currentText())
        self.settings.setValue("theme", self.theme_combo.currentText())
        self.settings.setValue("autostart", self.autostart_check.isChecked())
        self.settings.setValue("minimize_tray", self.minimize_tray_check.isChecked())
        self.settings.setValue("close_tray", self.close_tray_check.isChecked())
        self.settings.setValue("api_port", self.api_port_spin.value())
        self.settings.setValue("log_level", self.log_level_combo.currentText())
        self.settings.setValue("log_file", self.log_file_edit.text())
        self.settings.setValue("check_updates", self.check_updates_check.isChecked())
        self.settings.setValue("reset_hid", self.reset_hid_check.isChecked())
        
        self.settings.sync()
        QMessageBox.information(self, "Gespeichert", tr("msg_settings_saved"))
        
        # Emit all settings
        self.settings_changed.emit(self.get_settings())
    
    def _reset_settings(self):
        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, tr("dialog_confirm"), tr("dialog_delete_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings.clear()
            self._load_settings()
            QMessageBox.information(self, "Zurückgesetzt", "Einstellungen auf Standardwerte zurückgesetzt")
    
    def get_settings(self) -> dict:
        return {
            "language": self.language_combo.currentText(),
            "theme": self.theme_combo.currentText(),
            "autostart": self.autostart_check.isChecked(),
            "minimize_tray": self.minimize_tray_check.isChecked(),
            "close_tray": self.close_tray_check.isChecked(),
            "api_port": self.api_port_spin.value(),
            "log_level": self.log_level_combo.currentText(),
            "log_file": self.log_file_edit.text(),
            "check_updates": self.check_updates_check.isChecked(),
            "reset_hid": self.reset_hid_check.isChecked(),
        }