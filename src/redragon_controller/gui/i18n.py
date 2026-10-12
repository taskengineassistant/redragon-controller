"""
German translations for the Redragon Controller GUI.
All UI strings in German for native experience.
"""

TRANSLATIONS = {
    # Main Window
    "app_title": "Redragon Controller",
    "window_title": "Redragon Keyboard Controller",
    "tray_tooltip": "Redragon Controller - Rechtsklick für Menü",
    
    # Tabs
    "tab_dashboard": "Dashboard",
    "tab_rgb": "RGB Beleuchtung",
    "tab_keymap": "Tastenbelegung",
    "tab_macros": "Makros",
    "tab_profiles": "Profile",
    "tab_settings": "Einstellungen",
    
    # Dashboard
    "device_connected": "Gerät verbunden",
    "device_disconnected": "Kein Gerät verbunden",
    "device_name": "Gerät: {name}",
    "firmware_version": "Firmware: {version}",
    "active_profile": "Aktives Profil: {profile}",
    "quick_actions": "Schnellaktionen",
    "btn_connect": "Verbinden",
    "btn_disconnect": "Trennen",
    "btn_refresh": "Aktualisieren",
    
    # RGB Tab
    "rgb_mode": "Modus",
    "rgb_static": "Statisch",
    "rgb_breathing": "Atmen",
    "rgb_wave": "Welle",
    "rgb_ripple": "Welle (Tastendruck)",
    "rgb_reactive": "Reaktiv",
    "rgb_spectrum": "Spektrum",
    "rgb_rainbow_wave": "Regenbogen-Welle",
    "rgb_starlight": "Sternenlicht",
    "rgb_scan": "Scanner",
    "rgb_off": "Aus",
    
    "rgb_color": "Farbe",
    "rgb_brightness": "Helligkeit",
    "rgb_speed": "Geschwindigkeit",
    "rgb_direction": "Richtung",
    "rgb_zone": "Zone",
    "rgb_zone_all": "Alle Tasten",
    "rgb_zone_left": "Linke Seite",
    "rgb_zone_right": "Rechte Seite",
    "rgb_zone_center": "Mitte",
    "rgb_zone_wasd": "WASD",
    "rgb_zone_arrows": "Pfeiltasten",
    "rgb_zone_function": "Funktionstasten",
    "rgb_zone_numbers": "Zahlenreihe",
    "rgb_zone_custom": "Benutzerdefiniert",
    
    "rgb_direction_ltr": "Links → Rechts",
    "rgb_direction_rtl": "Rechts → Links",
    "rgb_direction_ttb": "Oben → Unten",
    "rgb_direction_btt": "Unten → Oben",
    "rgb_direction_center_out": "Mitte → Außen",
    "rgb_direction_out_center": "Außen → Mitte",
    
    "btn_apply_rgb": "Anwenden",
    "btn_save_rgb": "Als Profil speichern",
    
    # Keymap Tab
    "keymap_layer": "Ebene",
    "keymap_base": "Basis",
    "keymap_gaming": "Gaming",
    "keymap_media": "Medien",
    "keymap_custom": "Benutzerdefiniert",
    
    "keymap_key": "Taste",
    "keymap_action": "Aktion",
    "keymap_type": "Typ",
    "keymap_type_keycode": "Tastencode",
    "keymap_type_macro": "Makro",
    "keymap_type_layer": "Ebene wechseln",
    "keymap_type_media": "Medien",
    "keymap_type_mouse": "Maus",
    "keymap_type_none": "Deaktiviert",
    
    "btn_remap": "Neu belegen",
    "btn_reset_key": "Zurücksetzen",
    "btn_reset_all": "Alle zurücksetzen",
    "btn_import_keymap": "Importieren",
    "btn_export_keymap": "Exportieren",
    
    # Key Selection Dialog
    "select_key_title": "Taste auswählen",
    "select_key_prompt": "Klicke auf eine Taste oder wähle aus der Liste",
    "key_search": "Taste suchen...",
    
    # Action Dialog
    "action_title": "Aktion konfigurieren",
    "action_type": "Aktionstyp",
    "action_keycode": "Tastencode",
    "action_macro": "Makro auswählen",
    "action_layer": "Zielebene",
    "action_layer_momentary": "Nur gedrückt halten (Momentan)",
    "action_layer_toggle": "Umschalten (Toggle)",
    "action_media": "Medientaste",
    "action_mouse_btn": "Mausbutton",
    "action_mouse_move": "Mausbewegung",
    
    # Macros Tab
    "macro_name": "Name",
    "macro_steps": "Schritte",
    "macro_add_step": "Schritt hinzufügen",
    "macro_step_key": "Taste",
    "macro_step_action": "Aktion",
    "macro_step_press": "Drücken",
    "macro_step_release": "Loslassen",
    "macro_step_delay": "Verzögerung (ms)",
    "macro_repeat": "Wiederholen",
    "btn_new_macro": "Neues Makro",
    "btn_edit_macro": "Bearbeiten",
    "btn_delete_macro": "Löschen",
    "btn_record_macro": "Aufnehmen",
    "btn_stop_record": "Aufnahme stoppen",
    
    # Profiles Tab
    "profile_name": "Profilname",
    "profile_slot": "Slot (0-4)",
    "profile_description": "Beschreibung",
    "profile_tags": "Tags",
    "profile_created": "Erstellt",
    "profile_modified": "Geändert",
    "btn_new_profile": "Neues Profil",
    "btn_save_profile": "Speichern",
    "btn_load_profile": "Laden",
    "btn_delete_profile": "Löschen",
    "btn_export_profile": "Exportieren",
    "btn_import_profile": "Importieren",
    "btn_sync_onboard": "Mit Tastatur synchronisieren",
    
    # Settings Tab
    "settings_language": "Sprache",
    "settings_language_de": "Deutsch",
    "settings_language_en": "English",
    "settings_theme": "Design",
    "settings_theme_dark": "Dunkel",
    "settings_theme_light": "Hell",
    "settings_theme_system": "System",
    "settings_autostart": "Bei Windows-Start starten",
    "settings_minimize_tray": "In Tray minimieren",
    "settings_close_tray": "Schließen → Tray",
    "settings_check_updates": "Updates prüfen",
    "settings_device": "Standardgerät",
    "settings_api_port": "API Port (0 = deaktiviert)",
    "settings_log_level": "Log-Level",
    "btn_save_settings": "Einstellungen speichern",
    "btn_reset_settings": "Zurücksetzen",
    
    # Tray Menu
    "tray_show": "Anzeigen",
    "tray_hide": "Ausblenden",
    "tray_rgb_off": "RGB aus",
    "tray_profile": "Profil: {name}",
    "tray_settings": "Einstellungen",
    "tray_about": "Über",
    "tray_quit": "Beenden",
    
    # Dialogs
    "dialog_confirm": "Bestätigen",
    "dialog_cancel": "Abbrechen",
    "dialog_ok": "OK",
    "dialog_yes": "Ja",
    "dialog_no": "Nein",
    "dialog_save_changes": "Änderungen speichern?",
    "dialog_delete_confirm": "Wirklich löschen?",
    "dialog_overwrite": "Überschreiben?",
    
    # Messages
    "msg_device_found": "Gerät gefunden: {name}",
    "msg_device_lost": "Gerät getrennt",
    "msg_profile_saved": "Profil '{name}' gespeichert",
    "msg_profile_loaded": "Profil '{name}' geladen",
    "msg_profile_deleted": "Profil '{name}' gelöscht",
    "msg_rgb_applied": "RGB-Einstellungen angewendet",
    "msg_keymap_applied": "Tastenbelegung angewendet",
    "msg_macro_saved": "Makro '{name}' gespeichert",
    "msg_settings_saved": "Einstellungen gespeichert",
    "msg_autostart_enabled": "Autostart aktiviert",
    "msg_autostart_disabled": "Autostart deaktiviert",
    
    # Errors
    "err_no_device": "Kein Redragon-Gerät gefunden",
    "err_device_busy": "Gerät wird bereits verwendet",
    "err_hid_permission": "Keine Berechtigung für HID-Zugriff",
    "err_profile_not_found": "Profil nicht gefunden",
    "err_macro_not_found": "Makro nicht gefunden",
    "err_invalid_config": "Ungültige Konfiguration",
    "err_save_failed": "Speichern fehlgeschlagen",
    "err_load_failed": "Laden fehlgeschlagen",
    
    # Keyboard Visualizer
    "key_esc": "Esc",
    "key_f1": "F1", "key_f2": "F2", "key_f3": "F3", "key_f4": "F4",
    "key_f5": "F5", "key_f6": "F6", "key_f7": "F7", "key_f8": "F8",
    "key_f9": "F9", "key_f10": "F10", "key_f11": "F11", "key_f12": "F12",
    "key_prtsc": "Druck",
    "key_grave": "`", "key_1": "1", "key_2": "2", "key_3": "3", "key_4": "4",
    "key_5": "5", "key_6": "6", "key_7": "7", "key_8": "8", "key_9": "9", "key_0": "0",
    "key_minus": "-", "key_equal": "=", "key_backspace": "⌫",
    "key_tab": "Tab", "key_q": "Q", "key_w": "W", "key_e": "E", "key_r": "R",
    "key_t": "T", "key_y": "Y", "key_u": "U", "key_i": "I", "key_o": "O",
    "key_p": "P", "key_lbracket": "[", "key_rbracket": "]", "key_backslash": "\\",
    "key_caps": "⇪", "key_a": "A", "key_s": "S", "key_d": "D", "key_f": "F",
    "key_g": "G", "key_h": "H", "key_j": "J", "key_k": "K", "key_l": "L",
    "key_semicolon": ";", "key_quote": "'", "key_enter": "↵",
    "key_lshift": "⇧", "key_z": "Z", "key_x": "X", "key_c": "C", "key_v": "V",
    "key_b": "B", "key_n": "N", "key_m": "M", "key_comma": ",", "key_period": ".",
    "key_slash": "/", "key_rshift": "⇧",
    "key_lctrl": "Strg", "key_lwin": "⊞", "key_lalt": "Alt", "key_space": "Leertaste",
    "key_ralt": "AltGr", "key_fn": "Fn", "key_menu": "☰", "key_rctrl": "Strg",
    "key_insert": "Einfg", "key_home": "Pos1", "key_pageup": "Bild↑",
    "key_delete": "Entf", "key_end": "Ende", "key_pagedown": "Bild↓",
    "key_up": "↑", "key_left": "←", "key_down": "↓", "key_right": "→",
    "key_numlock": "Num", "key_kp_divide": "/", "key_kp_multiply": "*", "key_kp_subtract": "-",
    "key_kp_7": "7", "key_kp_8": "8", "key_kp_9": "9", "key_kp_add": "+",
    "key_kp_4": "4", "key_kp_5": "5", "key_kp_6": "6",
    "key_kp_1": "1", "key_kp_2": "2", "key_kp_3": "3", "key_kp_enter": "↵",
    "key_kp_0": "0", "key_kp_decimal": ".",
}


def tr(key: str, **kwargs) -> str:
    """Get translated string with optional formatting."""
    text = TRANSLATIONS.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text