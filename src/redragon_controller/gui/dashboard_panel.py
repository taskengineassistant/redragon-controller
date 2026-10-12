"""
Dashboard Panel
Main overview with device status and quick actions.
"""

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QProgressBar, QFrame, QGridLayout
)
from PySide6.QtGui import QFont, QColor, QPixmap, QPainter, QBrush

from .i18n import tr


class DeviceStatusWidget(QFrame):
    """Widget showing device connection status."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
            }
        """)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        
        # Title
        title = QLabel("Gerätestatus")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setStyleSheet("color: #0078d7;")
        layout.addWidget(title)
        
        # Status indicator
        self.status_layout = QHBoxLayout()
        self.status_dot = QLabel("●")
        self.status_dot.setFont(QFont("Segoe UI", 24))
        self.status_dot.setStyleSheet("color: #cc3333;")
        self.status_layout.addWidget(self.status_dot)
        
        self.status_text = QLabel(tr("device_disconnected"))
        self.status_text.setFont(QFont("Segoe UI", 14))
        self.status_layout.addWidget(self.status_text)
        self.status_layout.addStretch()
        
        layout.addLayout(self.status_layout)
        
        # Device info
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #aaa; font-size: 12px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        # Firmware
        self.firmware_label = QLabel("")
        self.firmware_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(self.firmware_label)
        
        # Active profile
        self.profile_label = QLabel("")
        self.profile_label.setStyleSheet("color: #0078d7; font-weight: bold;")
        layout.addWidget(self.profile_label)
    
    def set_connected(self, connected: bool, device_name: str = "", firmware: str = "", profile: str = ""):
        if connected:
            self.status_dot.setStyleSheet("color: #33cc33;")
            self.status_text.setText(tr("device_connected"))
            self.info_label.setText(tr("device_name").format(name=device_name))
            self.firmware_label.setText(tr("firmware_version").format(version=firmware) if firmware else "")
            self.profile_label.setText(tr("active_profile").format(profile=profile) if profile else "")
        else:
            self.status_dot.setStyleSheet("color: #cc3333;")
            self.status_text.setText(tr("device_disconnected"))
            self.info_label.setText("")
            self.firmware_label.setText("")
            self.profile_label.setText("")


class QuickActionButton(QPushButton):
    """Styled button for quick actions."""
    
    def __init__(self, text: str, icon_color: str = "#0078d7", parent=None):
        super().__init__(text, parent)
        self.icon_color = icon_color
        self.setStyleSheet(f"""
            QPushButton {{
                background: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 16px;
                font-size: 13px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: #3d3d3d;
                border-color: {icon_color};
            }}
            QPushButton:pressed {{
                background: #1a1a1a;
            }}
        """)


class DashboardPanel(QWidget):
    """Main dashboard panel."""
    
    # Signals
    connect_requested = Signal()
    disconnect_requested = Signal()
    refresh_requested = Signal()
    rgb_off_requested = Signal()
    profile_change_requested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Device Status
        self.device_status = DeviceStatusWidget()
        layout.addWidget(self.device_status)
        
        # Quick Actions
        actions_group = QGroupBox(tr("quick_actions"))
        actions_layout = QGridLayout(actions_group)
        actions_layout.setSpacing(12)
        
        self.btn_connect = QuickActionButton(tr("btn_connect"), "#33cc33")
        self.btn_connect.clicked.connect(self.connect_requested.emit)
        actions_layout.addWidget(self.btn_connect, 0, 0)
        
        self.btn_disconnect = QuickActionButton(tr("btn_disconnect"), "#cc3333")
        self.btn_disconnect.clicked.connect(self.disconnect_requested.emit)
        self.btn_disconnect.setEnabled(False)
        actions_layout.addWidget(self.btn_disconnect, 0, 1)
        
        self.btn_refresh = QuickActionButton(tr("btn_refresh"), "#0078d7")
        self.btn_refresh.clicked.connect(self.refresh_requested.emit)
        actions_layout.addWidget(self.btn_refresh, 0, 2)
        
        self.btn_rgb_off = QuickActionButton("RGB ausschalten", "#ff8800")
        self.btn_rgb_off.clicked.connect(self.rgb_off_requested.emit)
        actions_layout.addWidget(self.btn_rgb_off, 1, 0)
        
        self.btn_profile_1 = QuickActionButton("Profil 1: Gaming", "#0078d7")
        self.btn_profile_1.clicked.connect(lambda: self.profile_change_requested.emit("Gaming"))
        actions_layout.addWidget(self.btn_profile_1, 1, 1)
        
        self.btn_profile_2 = QuickActionButton("Profil 2: Arbeit", "#0078d7")
        self.btn_profile_2.clicked.connect(lambda: self.profile_change_requested.emit("Arbeit"))
        actions_layout.addWidget(self.btn_profile_2, 1, 2)
        
        layout.addWidget(actions_group)
        
        # Profile Quick Select
        profile_group = QGroupBox("Profil-Schnellwahl")
        profile_layout = QHBoxLayout(profile_group)
        
        self.profile_buttons = []
        for i in range(5):
            btn = QPushButton(f"Slot {i}")
            btn.setCheckable(True)
            btn.setMinimumWidth(80)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2d2d2d;
                    color: #e0e0e0;
                    border: 1px solid #3d3d3d;
                    border-radius: 6px;
                    padding: 8px;
                }
                QPushButton:checked {
                    background: #0078d7;
                    border-color: #0078d7;
                }
                QPushButton:hover:!checked {
                    background: #3d3d3d;
                }
            """)
            btn.clicked.connect(lambda checked, idx=i: self._on_profile_slot(idx))
            self.profile_buttons.append(btn)
            profile_layout.addWidget(btn)
        
        profile_layout.addStretch()
        layout.addWidget(profile_group)
        
        layout.addStretch()
    
    def _on_profile_slot(self, slot: int):
        for i, btn in enumerate(self.profile_buttons):
            if i != slot:
                btn.setChecked(False)
        self.profile_change_requested.emit(f"Slot {slot}")
    
    def update_device_status(self, connected: bool, device_name: str = "", firmware: str = "", profile: str = ""):
        self.device_status.set_connected(connected, device_name, firmware, profile)
        self.btn_connect.setEnabled(not connected)
        self.btn_disconnect.setEnabled(connected)
        self.btn_rgb_off.setEnabled(connected)
        for btn in self.profile_buttons:
            btn.setEnabled(connected)
    
    def set_active_profile_slot(self, slot: int):
        for i, btn in enumerate(self.profile_buttons):
            btn.setChecked(i == slot)