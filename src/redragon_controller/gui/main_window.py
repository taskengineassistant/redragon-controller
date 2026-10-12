"""
Main Window
Modern German GUI with tabs for all features.
"""

from PySide6.QtCore import Qt, Signal, QTimer, QSettings, QPoint
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTabBar, QLabel, QPushButton, QMessageBox, QSystemTrayIcon,
    QMenu, QStyle, QApplication, QSplitter
)
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction

from .i18n import tr
from .keyboard_visualizer import KeyboardVisualizer
from .rgb_panel import RGBControlPanel
from .keymap_panel import KeymapPanel
from .macros_panel import MacrosPanel
from .profiles_panel import ProfilesPanel
from .settings_panel import SettingsPanel
from .dashboard_panel import DashboardPanel


class MainWindow(QMainWindow):
    """Main application window."""
    
    # Signals
    minimize_to_tray = Signal()
    close_to_tray = Signal()
    
    def __init__(self, tray_app=None):
        super().__init__()
        self.tray_app = tray_app
        self.settings = QSettings("RedragonController", "RedragonController")
        self._setup_ui()
        self._load_window_state()
        self._apply_theme()
    
    def _setup_ui(self):
        self.setWindowTitle(tr("window_title"))
        self.resize(1200, 750)
        self.setMinimumSize(1000, 650)
        
        # Central widget with tabs
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tab widget
        self.tabs = QTabWidget()
        self.tabs.setTabBarAutoHide(False)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs)
        
        # Create keyboard visualizer (shared)
        self.keyboard = KeyboardVisualizer("tkl_87")
        
        # Create panels
        self.dashboard = DashboardPanel()
        self.rgb_panel = RGBControlPanel(self.keyboard)
        self.keymap_panel = KeymapPanel(self.keyboard)
        self.macros_panel = MacrosPanel()
        self.profiles_panel = ProfilesPanel()
        self.settings_panel = SettingsPanel()
        
        # Connect panel signals
        self._connect_panel_signals()
        
        # Add tabs
        self.tabs.addTab(self.dashboard, tr("tab_dashboard"))
        self.tabs.addTab(self.rgb_panel, tr("tab_rgb"))
        self.tabs.addTab(self.keymap_panel, tr("tab_keymap"))
        self.tabs.addTab(self.macros_panel, tr("tab_macros"))
        self.tabs.addTab(self.profiles_panel, tr("tab_profiles"))
        self.tabs.addTab(self.settings_panel, tr("tab_settings"))
        
        # Style tabs
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
                background: #1e1e1e;
                border-radius: 0 0 6px 6px;
            }
            QTabBar::tab {
                background: #2d2d2d;
                color: #aaa;
                border: 1px solid #3d3d3d;
                border-bottom: none;
                border-radius: 6px 6px 0 0;
                padding: 10px 20px;
                margin-right: 2px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #1e1e1e;
                color: #0078d7;
                border-color: #3d3d3d;
                border-bottom: 2px solid #0078d7;
            }
            QTabBar::tab:hover:!selected {
                background: #3d3d3d;
                color: #e0e0e0;
            }
        """)
        
        # Window icon
        self.setWindowIcon(self._create_window_icon())
    
    def _create_window_icon(self) -> QIcon:
        """Create application icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 0, 0)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(4, 4, 56, 56, 8, 8)
        painter.setPen(QColor(255, 255, 255))
        painter.setFont(QFont("Segoe UI", 28, QFont.Bold))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "R")
        painter.end()
        return QIcon(pixmap)
    
    def _connect_panel_signals(self):
        """Connect panel signals to handlers."""
        # Dashboard
        self.dashboard.connect_requested.connect(self._on_connect)
        self.dashboard.disconnect_requested.connect(self._on_disconnect)
        self.dashboard.refresh_requested.connect(self._on_refresh)
        self.dashboard.rgb_off_requested.connect(self._on_rgb_off)
        self.dashboard.profile_change_requested.connect(self._on_profile_change)
        
        # RGB Panel
        self.rgb_panel.apply_requested.connect(self._on_rgb_apply)
        self.rgb_panel.save_profile_requested.connect(self._on_save_rgb_profile)
        
        # Keymap Panel
        self.keymap_panel.apply_requested.connect(self._on_keymap_apply)
        self.keymap_panel.reset_requested.connect(self._on_keymap_reset)
        self.keymap_panel.import_requested.connect(self._on_import_keymap)
        self.keymap_panel.export_requested.connect(self._on_export_keymap)
        
        # Macros Panel
        self.macros_panel.apply_requested.connect(self._on_macros_apply)
        self.macros_panel.macro_selected.connect(self._on_macro_selected)
        
        # Profiles Panel
        self.profiles_panel.profile_saved.connect(self._on_profile_saved)
        self.profiles_panel.profile_loaded.connect(self._on_profile_loaded)
        self.profiles_panel.profile_deleted.connect(self._on_profile_deleted)
        self.profiles_panel.sync_onboard_requested.connect(self._on_sync_onboard)
        
        # Settings Panel
        self.settings_panel.settings_changed.connect(self._on_settings_changed)
        self.settings_panel.autostart_changed.connect(self._on_autostart_changed)
        self.settings_panel.theme_changed.connect(self._on_theme_changed)
    
    def _apply_theme(self):
        theme = self.settings.value("theme", tr("settings_theme_dark"))
        self.settings_panel._apply_theme(theme)
    
    def _load_window_state(self):
        geometry = self.settings.value("window_geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self.settings.value("window_state")
        if state:
            self.restoreState(state)
    
    def _save_window_state(self):
        self.settings.setValue("window_geometry", self.saveGeometry())
        self.settings.setValue("window_state", self.saveState())
    
    def closeEvent(self, event):
        """Handle close event - minimize to tray if enabled."""
        if self.settings.value("close_tray", True, type=bool):
            event.ignore()
            self.hide()
            self.minimize_to_tray.emit()
            if self.tray_app:
                self.tray_app.show_message("Redragon Controller", "Anwendung läuft im Hintergrund. Klicke auf das Tray-Icon um das Fenster anzuzeigen.")
        else:
            self._save_window_state()
            self.close_to_tray.emit()
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes."""
        if event.type() == event.WindowStateChange:
            if self.isMinimized() and self.settings.value("minimize_tray", True, type=bool):
                event.ignore()
                self.hide()
                self.minimize_to_tray.emit()
                return
        super().changeEvent(event)
    
    def showEvent(self, event):
        super().showEvent(event)
        if self.tray_app:
            self.tray_app.set_tray_active(True)
    
    def hideEvent(self, event):
        super().hideEvent(event)
        if self.tray_app:
            self.tray_app.set_tray_active(False)
    
    # === Event Handlers ===
    
    def _on_connect(self):
        """Handle connect request."""
        # Implemented by tray_app/controller
        pass
    
    def _on_disconnect(self):
        pass
    
    def _on_refresh(self):
        pass
    
    def _on_rgb_off(self):
        pass
    
    def _on_profile_change(self, profile_name: str):
        pass
    
    def _on_rgb_apply(self, config: dict):
        pass
    
    def _on_save_rgb_profile(self, name: str):
        pass
    
    def _on_keymap_apply(self, config: dict):
        pass
    
    def _on_keymap_reset(self):
        pass
    
    def _on_import_keymap(self):
        pass
    
    def _on_export_keymap(self):
        pass
    
    def _on_macros_apply(self, macros: list):
        self.keymap_panel.set_macros(macros)
    
    def _on_macro_selected(self, macro: dict):
        pass
    
    def _on_profile_saved(self, profile: dict):
        pass
    
    def _on_profile_loaded(self, name: str):
        pass
    
    def _on_profile_deleted(self, name: str):
        pass
    
    def _on_sync_onboard(self):
        pass
    
    def _on_settings_changed(self, settings: dict):
        pass
    
    def _on_autostart_changed(self, enabled: bool):
        pass
    
    def _on_theme_changed(self, theme: str):
        self._apply_theme()
    
    def update_device_status(self, connected: bool, device_name: str = "", firmware: str = "", profile: str = ""):
        """Update device status in dashboard."""
        self.dashboard.update_device_status(connected, device_name, firmware, profile)
    
    def set_active_profile(self, name: str, slot: int = -1):
        """Update active profile display."""
        self.dashboard.set_active_profile_slot(slot)
        self.profiles_panel.set_profiles(self.profiles_panel.get_profiles())  # Refresh


class TrayApplication:
    """System tray application controller."""
    
    def __init__(self):
        self.app = None
        self.window = None
        self.tray_icon = None
        self.controller = None  # Backend controller
        
    def initialize(self, app: QApplication, controller):
        """Initialize the tray application."""
        self.app = app
        self.controller = controller
        
        # Create main window
        self.window = MainWindow(tray_app=self)
        
        # Create tray icon
        self._create_tray_icon()
        
        # Connect controller callbacks
        if controller:
            controller.set_ui_callbacks(
                on_device_change=self.window.update_device_status,
                on_profile_change=self.window.set_active_profile,
            )
        
        # Show window on startup if not minimized
        if not self.settings.value("minimize_tray", True, type=bool):
            self.window.show()
        else:
            # Start minimized
            pass
    
    def _create_tray_icon(self):
        """Create system tray icon with menu."""
        self.tray_icon = QSystemTrayIcon(self.window)
        self.tray_icon.setIcon(self.window._create_window_icon())
        self.tray_icon.setToolTip(tr("tray_tooltip"))
        
        # Tray menu
        tray_menu = QMenu()
        
        show_action = QAction(tr("tray_show"), self.window)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        hide_action = QAction(tr("tray_hide"), self.window)
        hide_action.triggered.connect(self.window.hide)
        tray_menu.addAction(hide_action)
        
        tray_menu.addSeparator()
        
        # Quick profile switch
        profile_menu = tray_menu.addMenu(tr("tray_profile").format(name="Profile"))
        for i in range(5):
            action = QAction(f"Slot {i}", self.window)
            action.triggered.connect(lambda _, s=i: self.controller.set_profile_slot(s) if self.controller else None)
            profile_menu.addAction(action)
        
        tray_menu.addSeparator()
        
        rgb_off_action = QAction(tr("tray_rgb_off"), self.window)
        rgb_off_action.triggered.connect(lambda: self.controller.rgb_off() if self.controller else None)
        tray_menu.addAction(rgb_off_action)
        
        tray_menu.addSeparator()
        
        settings_action = QAction(tr("tray_settings"), self.window)
        settings_action.triggered.connect(lambda: self.window.tabs.setCurrentIndex(5))
        tray_menu.addAction(settings_action)
        
        about_action = QAction(tr("tray_about"), self.window)
        about_action.triggered.connect(self.show_about)
        tray_menu.addAction(about_action)
        
        tray_menu.addSeparator()
        
        quit_action = QAction(tr("tray_quit"), self.window)
        quit_action.triggered.connect(self.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()
    
    def _on_tray_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_window()
    
    def show_window(self):
        """Show and raise main window."""
        self.window.show()
        self.window.raise_()
        self.window.activateWindow()
        self.set_tray_active(True)
    
    def set_tray_active(self, active: bool):
        """Update tray icon appearance."""
        # Could change icon color based on active state
        pass
    
    def show_message(self, title: str, message: str, icon=QSystemTrayIcon.Information, timeout=3000):
        """Show tray notification."""
        self.tray_icon.showMessage(title, message, icon, timeout)
    
    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self.window, "Über Redragon Controller", 
            f"<h3>{tr('app_title')}</h3>"
            "<p>Version 0.1.0</p>"
            "<p>Moderne Steuerung für Redragon RGB-Tastaturen</p>"
            "<p>Entwickelt mit Python & PySide6</p>"
            "<br>"
            "<p><a href='https://github.com/taskengineassistant/redragon-controller'>GitHub Repository</a></p>"
        )
    
    def quit(self):
        """Quit application."""
        self.tray_icon.hide()
        self.app.quit()
    
    def run(self):
        """Run the application."""
        return self.app.exec()


def main():
    """Main entry point for GUI."""
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setApplicationName("Redragon Controller")
    app.setApplicationVersion("0.1.0")
    app.setQuitOnLastWindowClosed(False)  # Keep running in tray
    
    # High DPI scaling
    app.setAttribute(Qt.AA_EnableHighDpiScaling)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps)
    
    tray_app = TrayApplication()
    tray_app.initialize(app, None)  # Controller will be set later
    
    return tray_app.run()


if __name__ == "__main__":
    sys.exit(main())