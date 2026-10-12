"""
Macro Editor Panel
Record, edit, and manage macros.
"""

from typing import List, Dict
from PySide6.QtCore import Qt, Signal, QTimer, QPoint
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QLineEdit,
    QDialog, QFormLayout, QDialogButtonBox, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QSpinBox, QCheckBox, QMenu, QInputDialog
)
from PySide6.QtGui import QColor, QKeyEvent

from .i18n import tr


class MacroRecorder(QWidget):
    """Widget for recording keystrokes as macro."""
    
    recording_finished = Signal(list)  # List of steps
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.steps = []
        self._setup_ui()
        
        # Timer for delays
        self.last_time = 0
        self.timer = QTimer()
        self.timer.setSingleShot(False)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Status
        self.status_label = QLabel(tr("btn_record_macro"))
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 16px;
                background: #2d2d2d;
                border-radius: 8px;
                font-size: 14px;
                color: #aaa;
            }
        """)
        layout.addWidget(self.status_label)
        
        # Record/Stop buttons
        btn_layout = QHBoxLayout()
        
        self.btn_record = QPushButton(tr("btn_record_macro"))
        self.btn_record.setStyleSheet("""
            QPushButton {
                background: #cc3333;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background: #dd4444; }
            QPushButton:disabled { background: #555; color: #888; }
        """)
        self.btn_record.clicked.connect(self._toggle_record)
        btn_layout.addWidget(self.btn_record)
        
        self.btn_stop = QPushButton(tr("btn_stop_record"))
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self._stop_record)
        btn_layout.addWidget(self.btn_stop)
        
        layout.addLayout(btn_layout)
        
        # Recorded steps preview
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels([
            tr("macro_step_key"), tr("macro_step_action"), 
            tr("macro_step_delay"), "Typ"
        ])
        self.steps_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.steps_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.steps_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.steps_table, 1)
        
        # Clear button
        self.btn_clear = QPushButton("Aufnahme löschen")
        self.btn_clear.clicked.connect(self._clear)
        layout.addWidget(self.btn_clear)
    
    def _toggle_record(self):
        if not self.recording:
            self._start_record()
        else:
            self._stop_record()
    
    def _start_record(self):
        self.recording = True
        self.steps = []
        self.last_time = 0
        self.btn_record.setText("Aufnahme läuft...")
        self.btn_record.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.status_label.setText("🔴 AUFNAHME LÄUFT - Drücke Tasten...")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 16px;
                background: #cc3333;
                border-radius: 8px;
                font-size: 14px;
                color: white;
                font-weight: bold;
            }
        """)
        self.steps_table.setRowCount(0)
        self.grabKeyboard()
    
    def _stop_record(self):
        if self.recording:
            self.recording = False
            self.releaseKeyboard()
            self.btn_record.setText(tr("btn_record_macro"))
            self.btn_record.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.status_label.setText(tr("btn_record_macro"))
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 16px;
                    background: #2d2d2d;
                    border-radius: 8px;
                    font-size: 14px;
                    color: #aaa;
                }
            """)
            self.recording_finished.emit(self.steps)
    
    def _clear(self):
        self.steps = []
        self.steps_table.setRowCount(0)
    
    def keyPressEvent(self, event: QKeyEvent):
        if self.recording and not event.isAutoRepeat():
            self._add_step(event.key(), event.text(), "press")
    
    def keyReleaseEvent(self, event: QKeyEvent):
        if self.recording and not event.isAutoRepeat():
            self._add_step(event.key(), event.text(), "release")
    
    def _add_step(self, key_code: int, key_text: str, action: str):
        import time
        now = int(time.time() * 1000)
        delay = now - self.last_time if self.last_time > 0 else 0
        self.last_time = now
        
        step = {
            "key_code": key_code,
            "key_text": key_text if key_text else f"Key({key_code})",
            "action": action,
            "delay": min(delay, 5000)  # Cap at 5 seconds
        }
        self.steps.append(step)
        self._update_table()
    
    def _update_table(self):
        self.steps_table.setRowCount(len(self.steps))
        for i, step in enumerate(self.steps):
            self.steps_table.setItem(i, 0, QTableWidgetItem(step["key_text"]))
            self.steps_table.setItem(i, 1, QTableWidgetItem(
                tr("macro_step_press") if step["action"] == "press" else tr("macro_step_release")
            ))
            self.steps_table.setItem(i, 2, QTableWidgetItem(f"{step['delay']} ms"))
            self.steps_table.setItem(i, 3, QTableWidgetItem("Taste"))


class MacroEditorDialog(QDialog):
    """Dialog for editing a macro."""
    
    def __init__(self, macro: dict = None, parent=None):
        super().__init__(parent)
        self.macro = macro or {"name": "", "steps": [], "repeat": 1}
        self.setWindowTitle(tr("btn_new_macro") if not macro else tr("btn_edit_macro"))
        self.setModal(True)
        self.resize(500, 400)
        self._setup_ui()
        if macro:
            self._load_macro(macro)
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Name
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("macro_name"))
        form.addRow(tr("macro_name"), self.name_edit)
        
        self.repeat_spin = QSpinBox()
        self.repeat_spin.setRange(1, 999)
        self.repeat_spin.setValue(1)
        form.addRow(tr("macro_repeat"), self.repeat_spin)
        
        layout.addLayout(form)
        
        # Steps table
        self.steps_table = QTableWidget()
        self.steps_table.setColumnCount(4)
        self.steps_table.setHorizontalHeaderLabels([
            tr("macro_step_key"), tr("macro_step_action"), 
            tr("macro_step_delay"), "Aktion"
        ])
        self.steps_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.steps_table, 1)
        
        # Step buttons
        step_btn_layout = QHBoxLayout()
        
        self.btn_add_key = QPushButton("Taste hinzufügen")
        self.btn_add_key.clicked.connect(self._add_key_step)
        step_btn_layout.addWidget(self.btn_add_key)
        
        self.btn_add_delay = QPushButton("Verzögerung")
        self.btn_add_delay.clicked.connect(self._add_delay_step)
        step_btn_layout.addWidget(self.btn_add_delay)
        
        self.btn_remove_step = QPushButton("Entfernen")
        self.btn_remove_step.clicked.connect(self._remove_step)
        step_btn_layout.addWidget(self.btn_remove_step)
        
        step_btn_layout.addStretch()
        layout.addLayout(step_btn_layout)
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _load_macro(self, macro: dict):
        self.name_edit.setText(macro.get("name", ""))
        self.repeat_spin.setValue(macro.get("repeat", 1))
        
        for step in macro.get("steps", []):
            row = self.steps_table.rowCount()
            self.steps_table.insertRow(row)
            self.steps_table.setItem(row, 0, QTableWidgetItem(step.get("key", "")))
            self.steps_table.setItem(row, 1, QTableWidgetItem(step.get("action", "press")))
            self.steps_table.setItem(row, 2, QTableWidgetItem(str(step.get("delay", 0))))
            self.steps_table.setItem(row, 3, QTableWidgetItem(step.get("type", "key")))
    
    def _add_key_step(self):
        # Simple dialog to select key
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox
        dialog = QDialog(self)
        dialog.setWindowTitle("Taste wählen")
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Drücke die gewünschte Taste..."))
        key_edit = QLineEdit()
        key_edit.setReadOnly(True)
        layout.addWidget(key_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        def keyPressEvent(event):
            key_edit.setText(event.text() if event.text() else f"Key({event.key()})")
        dialog.keyPressEvent = keyPressEvent
        
        if dialog.exec() == QDialog.Accepted and key_edit.text():
            row = self.steps_table.rowCount()
            self.steps_table.insertRow(row)
            self.steps_table.setItem(row, 0, QTableWidgetItem(key_edit.text()))
            self.steps_table.setItem(row, 1, QTableWidgetItem("press"))
            self.steps_table.setItem(row, 2, QTableWidgetItem("0"))
            self.steps_table.setItem(row, 3, QTableWidgetItem("key"))
    
    def _add_delay_step(self):
        delay, ok = QInputDialog.getInt(self, "Verzögerung", "Verzögerung (ms):", 100, 0, 5000)
        if ok:
            row = self.steps_table.rowCount()
            self.steps_table.insertRow(row)
            self.steps_table.setItem(row, 0, QTableWidgetItem(f"Delay {delay}ms"))
            self.steps_table.setItem(row, 1, QTableWidgetItem("delay"))
            self.steps_table.setItem(row, 2, QTableWidgetItem(str(delay)))
            self.steps_table.setItem(row, 3, QTableWidgetItem("delay"))
    
    def _remove_step(self):
        row = self.steps_table.currentRow()
        if row >= 0:
            self.steps_table.removeRow(row)
    
    def get_macro(self) -> dict:
        steps = []
        for row in range(self.steps_table.rowCount()):
            key_item = self.steps_table.item(row, 0)
            action_item = self.steps_table.item(row, 1)
            delay_item = self.steps_table.item(row, 2)
            type_item = self.steps_table.item(row, 3)
            
            if key_item and action_item:
                step_type = type_item.text() if type_item else "key"
                if step_type == "delay":
                    steps.append({"type": "delay", "delay": int(delay_item.text()) if delay_item else 0})
                else:
                    steps.append({
                        "type": "key",
                        "key": key_item.text(),
                        "action": action_item.text(),
                        "delay": int(delay_item.text()) if delay_item else 0
                    })
        
        return {
            "name": self.name_edit.text().strip(),
            "steps": steps,
            "repeat": self.repeat_spin.value()
        }


class MacrosPanel(QWidget):
    """Macro management panel."""
    
    # Signals
    apply_requested = Signal(list)  # List of macros
    macro_selected = Signal(dict)   # Single macro for assignment
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.macros: List[dict] = []
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.btn_new = QPushButton(tr("btn_new_macro"))
        self.btn_new.clicked.connect(self._new_macro)
        toolbar.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton(tr("btn_edit_macro"))
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_macro)
        toolbar.addWidget(self.btn_edit)
        
        self.btn_delete = QPushButton(tr("btn_delete_macro"))
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_macro)
        toolbar.addWidget(self.btn_delete)
        
        toolbar.addStretch()
        
        self.btn_record = QPushButton(tr("btn_record_macro"))
        self.btn_record.setStyleSheet("background: #cc3333; color: white; font-weight: bold;")
        self.btn_record.clicked.connect(self._show_recorder)
        toolbar.addWidget(self.btn_record)
        
        layout.addLayout(toolbar)
        
        # Macro list
        list_group = QGroupBox("Makros")
        list_layout = QVBoxLayout(list_group)
        
        self.macro_list = QListWidget()
        self.macro_list.setAlternatingRowColors(True)
        self.macro_list.currentItemChanged.connect(self._on_selection_change)
        self.macro_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.macro_list.customContextMenuRequested.connect(self._show_context_menu)
        list_layout.addWidget(self.macro_list)
        
        layout.addWidget(list_group, 1)
        
        # Recorder (hidden by default)
        self.recorder = MacroRecorder()
        self.recorder.recording_finished.connect(self._on_recording_finished)
        self.recorder.hide()
        layout.addWidget(self.recorder)
        
        layout.addStretch()
    
    def _on_selection_change(self, current, previous):
        has_selection = current is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        
        if has_selection:
            macro = current.data(Qt.UserRole)
            self.macro_selected.emit(macro)
    
    def _show_context_menu(self, pos):
        item = self.macro_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        edit_action = menu.addAction(tr("btn_edit_macro"))
        edit_action.triggered.connect(self._edit_macro)
        
        delete_action = menu.addAction(tr("btn_delete_macro"))
        delete_action.triggered.connect(self._delete_macro)
        
        menu.exec(self.macro_list.mapToGlobal(pos))
    
    def _new_macro(self):
        dialog = MacroEditorDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            macro = dialog.get_macro()
            if macro["name"]:
                macro["id"] = f"macro_{len(self.macros) + 1}"
                self.macros.append(macro)
                self._refresh_list()
                self.apply_requested.emit(self.macros)
    
    def _edit_macro(self):
        item = self.macro_list.currentItem()
        if not item:
            return
        
        macro = item.data(Qt.UserRole)
        dialog = MacroEditorDialog(macro, parent=self)
        if dialog.exec() == QDialog.Accepted:
            updated = dialog.get_macro()
            if updated["name"]:
                macro.update(updated)
                self._refresh_list()
                self.apply_requested.emit(self.macros)
    
    def _delete_macro(self):
        item = self.macro_list.currentItem()
        if not item:
            return
        
        macro = item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, tr("dialog_confirm"), 
            f"Makro '{macro['name']}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.macros = [m for m in self.macros if m["id"] != macro["id"]]
            self._refresh_list()
            self.apply_requested.emit(self.macros)
    
    def _show_recorder(self):
        self.recorder.show()
        self.recorder._start_record()
    
    def _on_recording_finished(self, steps: list):
        if not steps:
            return
        
        name, ok = QInputDialog.getText(self, tr("dialog_confirm"), "Name für das aufgezeichnete Makro:")
        if ok and name:
            macro = {
                "id": f"macro_{len(self.macros) + 1}",
                "name": name,
                "steps": steps,
                "repeat": 1
            }
            self.macros.append(macro)
            self._refresh_list()
            self.apply_requested.emit(self.macros)
    
    def _refresh_list(self):
        self.macro_list.clear()
        for macro in self.macros:
            item = QListWidgetItem(f"{macro['name']} ({len(macro['steps'])} Schritte)")
            item.setData(Qt.UserRole, macro)
            self.macro_list.addItem(item)
    
    def set_macros(self, macros: list):
        self.macros = macros
        self._refresh_list()
    
    def get_macros(self) -> list:
        return list(self.macros)