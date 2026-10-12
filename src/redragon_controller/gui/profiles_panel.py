"""
Profiles Panel
Manage keyboard profiles (onboard + local).
"""

from typing import List, Dict
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QTextEdit, QComboBox, QCheckBox, QFileDialog, QMenu,
    QInputDialog
)
from PySide6.QtGui import QColor

from .i18n import tr


class ProfileDialog(QDialog):
    """Dialog for creating/editing a profile."""
    
    def __init__(self, profile: dict = None, parent=None):
        super().__init__(parent)
        self.profile = profile or {}
        self.setWindowTitle(tr("btn_new_profile") if not profile else tr("btn_edit_macro").replace("Makro", "Profil"))
        self.setModal(True)
        self.resize(450, 400)
        self._setup_ui()
        if profile:
            self._load_profile(profile)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("profile_name"))
        form.addRow(tr("profile_name"), self.name_edit)
        
        self.slot_combo = QComboBox()
        for i in range(5):
            self.slot_combo.addItem(f"Slot {i}", i)
        form.addRow(tr("profile_slot"), self.slot_combo)
        
        self.desc_edit = QTextEdit()
        self.desc_edit.setMaximumHeight(80)
        self.desc_edit.setPlaceholderText(tr("profile_description"))
        form.addRow(tr("profile_description"), self.desc_edit)
        
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("gaming, work, rgb (kommagetrennt)")
        form.addRow(tr("profile_tags"), self.tags_edit)
        
        self.onboard_check = QCheckBox(tr("profile_slot"))
        self.onboard_check.setText("Auf Tastatur speichern (Onboard)")
        self.onboard_check.setChecked(True)
        form.addRow("", self.onboard_check)
        
        self.local_check = QCheckBox("Lokal speichern")
        self.local_check.setChecked(True)
        form.addRow("", self.local_check)
        
        layout.addLayout(form)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_profile(self, profile: dict):
        self.name_edit.setText(profile.get("name", ""))
        self.slot_combo.setCurrentIndex(profile.get("slot", 0))
        self.desc_edit.setPlainText(profile.get("description", ""))
        self.tags_edit.setText(", ".join(profile.get("tags", [])))
        self.onboard_check.setChecked(profile.get("onboard", True))
        self.local_check.setChecked(profile.get("local", True))
    
    def get_profile(self) -> dict:
        return {
            "name": self.name_edit.text().strip(),
            "slot": self.slot_combo.currentData(),
            "description": self.desc_edit.toPlainText().strip(),
            "tags": [t.strip() for t in self.tags_edit.text().split(",") if t.strip()],
            "onboard": self.onboard_check.isChecked(),
            "local": self.local_check.isChecked(),
        }


class ProfilesPanel(QWidget):
    """Profile management panel."""
    
    # Signals
    profile_saved = Signal(dict)      # Profile data
    profile_loaded = Signal(str)      # Profile name
    profile_deleted = Signal(str)     # Profile name
    sync_onboard_requested = Signal() # Sync with keyboard
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profiles: List[dict] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.btn_new = QPushButton(tr("btn_new_profile"))
        self.btn_new.clicked.connect(self._new_profile)
        toolbar.addWidget(self.btn_new)
        
        self.btn_load = QPushButton(tr("btn_load_profile"))
        self.btn_load.setEnabled(False)
        self.btn_load.clicked.connect(self._load_profile)
        toolbar.addWidget(self.btn_load)
        
        self.btn_delete = QPushButton(tr("btn_delete_profile"))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_profile)
        toolbar.addWidget(self.btn_delete)
        
        toolbar.addStretch()
        
        self.btn_export = QPushButton(tr("btn_export_profile"))
        self.btn_export.clicked.connect(self._export_profile)
        toolbar.addWidget(self.btn_export)
        
        self.btn_import = QPushButton(tr("btn_import_profile"))
        self.btn_import.clicked.connect(self._import_profile)
        toolbar.addWidget(self.btn_import)
        
        self.btn_sync = QPushButton(tr("btn_sync_onboard"))
        self.btn_sync.clicked.connect(self.sync_onboard_requested.emit)
        toolbar.addWidget(self.btn_sync)
        
        layout.addLayout(toolbar)
        
        # Profile list
        list_group = QGroupBox("Profile")
        list_layout = QVBoxLayout(list_group)
        
        self.profile_list = QListWidget()
        self.profile_list.setAlternatingRowColors(True)
        self.profile_list.currentItemChanged.connect(self._on_selection_change)
        self.profile_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.profile_list.customContextMenuRequested.connect(self._show_context_menu)
        list_layout.addWidget(self.profile_list)
        
        layout.addWidget(list_group, 1)
        
        # Profile details
        details_group = QGroupBox("Details")
        details_layout = QVBoxLayout(details_group)
        
        self.details_label = QLabel("Kein Profil ausgewählt")
        self.details_label.setWordWrap(True)
        details_layout.addWidget(self.details_label)
        
        layout.addWidget(details_group)
        
        layout.addStretch()
    
    def _on_selection_change(self, current, previous):
        has_selection = current is not None
        self.btn_load.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        
        if has_selection:
            profile = current.data(Qt.UserRole)
            self._show_details(profile)
    
    def _show_context_menu(self, pos):
        item = self.profile_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        load_action = menu.addAction(tr("btn_load_profile"))
        load_action.triggered.connect(self._load_profile)
        
        delete_action = menu.addAction(tr("btn_delete_profile"))
        delete_action.triggered.connect(self._delete_profile)
        
        menu.addSeparator()
        
        export_action = menu.addAction(tr("btn_export_profile"))
        export_action.triggered.connect(lambda: self._export_profile(item.data(Qt.UserRole)))
        
        menu.exec(self.profile_list.mapToGlobal(pos))
    
    def _show_details(self, profile: dict):
        tags = ", ".join(profile.get("tags", []))
        self.details_label.setText(
            f"<b>Name:</b> {profile.get('name', '')}<br>"
            f"<b>Slot:</b> {profile.get('slot', 0)}<br>"
            f"<b>Beschreibung:</b> {profile.get('description', '')}<br>"
            f"<b>Tags:</b> {tags}<br>"
            f"<b>Onboard:</b> {'Ja' if profile.get('onboard') else 'Nein'}<br>"
            f"<b>Lokal:</b> {'Ja' if profile.get('local') else 'Nein'}<br>"
            f"<b>Erstellt:</b> {profile.get('created', '')}<br>"
            f"<b>Geändert:</b> {profile.get('modified', '')}"
        )
    
    def _new_profile(self):
        dialog = ProfileDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            profile = dialog.get_profile()
            if profile["name"]:
                from datetime import datetime
                profile["created"] = datetime.now().isoformat()
                profile["modified"] = datetime.now().isoformat()
                self.profiles.append(profile)
                self._refresh_list()
                self.profile_saved.emit(profile)
    
    def _load_profile(self):
        item = self.profile_list.currentItem()
        if item:
            profile = item.data(Qt.UserRole)
            self.profile_loaded.emit(profile["name"])
    
    def _delete_profile(self):
        item = self.profile_list.currentItem()
        if not item:
            return
        
        profile = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, tr("dialog_confirm"),
            f"Profil '{profile['name']}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.profiles = [p for p in self.profiles if p["name"] != profile["name"]]
            self._refresh_list()
            self.profile_deleted.emit(profile["name"])
    
    def _export_profile(self, profile: dict = None):
        if profile is None:
            item = self.profile_list.currentItem()
            if not item:
                return
            profile = item.data(Qt.UserRole)
        
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "Profil exportieren", f"{profile['name']}.yaml",
            "YAML Files (*.yaml *.yml);;JSON Files (*.json)"
        )
        if path:
            import yaml
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(profile, f, allow_unicode=True)
            QMessageBox.information(self, "Erfolg", f"Profil exportiert nach:\n{path}")
    
    def _import_profile(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Profil importieren", "",
            "YAML Files (*.yaml *.yml);;JSON Files (*.json)"
        )
        if path:
            import yaml
            with open(path, 'r', encoding='utf-8') as f:
                profile = yaml.safe_load(f)
            
            if profile and "name" in profile:
                from datetime import datetime
                profile["created"] = datetime.now().isoformat()
                profile["modified"] = datetime.now().isoformat()
                # Check for duplicate name
                existing = next((p for p in self.profiles if p["name"] == profile["name"]), None)
                if existing:
                    reply = QMessageBox.question(
                        self, "Überschreiben?",
                        f"Profil '{profile['name']}' existiert bereits. Überschreiben?",
                        QMessageBox.Yes | QMessageBox.No
                    )
                    if reply == QMessageBox.Yes:
                        self.profiles = [p for p in self.profiles if p["name"] != profile["name"]]
                    else:
                        return
                self.profiles.append(profile)
                self._refresh_list()
                self.profile_saved.emit(profile)
    
    def _refresh_list(self):
        self.profile_list.clear()
        for profile in self.profiles:
            tags = ", ".join(profile.get("tags", [])[:2])
            item = QListWidgetItem(f"{profile['name']} (Slot {profile.get('slot', 0)})")
            if tags:
                item.setToolTip(f"Tags: {tags}")
            item.setData(Qt.UserRole, profile)
            self.profile_list.addItem(item)
    
    def set_profiles(self, profiles: list):
        self.profiles = profiles
        self._refresh_list()
    
    def get_profiles(self) -> list:
        return list(self.profiles)