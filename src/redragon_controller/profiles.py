"""
Profile Management
Handles saving/loading complete profiles (RGB + Keymap) to keyboard onboard memory and local files.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json
import yaml
from datetime import datetime

from .protocol import (
    Command, build_command, parse_response,
    cmd_save_profile, cmd_load_profile
)
from .hid_transport import HIDTransport, TransportError, ReportID
from .rgb import RGBController, Effect, Color, RGBZone, RGBEffect, EffectSpeed
from .keymap import KeyMap, Layer, KeyAction, KeyActionType, Macro


@dataclass
class Profile:
    """Complete keyboard profile (RGB + Keymap + Metadata)."""
    name: str
    slot: int = 0  # Onboard profile slot (0-4)
    
    # RGB Configuration
    rgb_effect: RGBEffect = RGBEffect.STATIC
    rgb_color: Color = field(default_factory=lambda: Color(255, 255, 255))
    rgb_speed: int = EffectSpeed.NORMAL
    rgb_direction: int = 0
    rgb_zone: RGBZone = RGBZone.ALL
    rgb_brightness: int = 255
    custom_effects: Dict[str, Effect] = field(default_factory=dict)
    
    # Keymap Configuration
    active_layer: int = 0
    layers: Dict[int, Layer] = field(default_factory=dict)
    macros: Dict[int, Macro] = field(default_factory=dict)
    
    # Metadata
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    modified: str = field(default_factory=lambda: datetime.now().isoformat())
    device_model: str = ""
    firmware_version: str = ""
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def __post_init__(self):
        # Ensure at least base layer exists
        if 0 not in self.layers:
            self.layers[0] = Layer(0, "Base")
        # Ensure all layers have parent references
        for layer in self.layers.values():
            if layer.parent_layer is None and layer.index > 0:
                layer.parent_layer = 0
    
    def to_dict(self) -> dict:
        """Serialize to dict for JSON/YAML storage."""
        data = asdict(self)
        # Convert enums to values
        data["rgb_effect"] = self.rgb_effect.value
        data["rgb_zone"] = self.rgb_zone.value
        # Convert layers
        data["layers"] = {
            idx: {
                "index": layer.index,
                "name": layer.name,
                "keymap": {k: {"type": a.action_type.value, "data": a.data.hex()} 
                          for k, a in layer.keymap.items()},
                "parent_layer": layer.parent_layer
            }
            for idx, layer in self.layers.items()
        }
        # Convert macros
        data["macros"] = {
            idx: {
                "steps": macro.steps,
                "repeat": macro.repeat
            }
            for idx, macro in self.macros.items()
        }
        # Convert color
        data["rgb_color"] = self.rgb_color.to_hex()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Deserialize from dict."""
        # Convert enums
        data["rgb_effect"] = RGBEffect(data.get("rgb_effect", RGBEffect.STATIC))
        data["rgb_zone"] = RGBZone(data.get("rgb_zone", RGBZone.ALL))
        data["rgb_color"] = Color.from_hex(data.get("rgb_color", "#ffffff"))
        
        # Convert layers
        layers = {}
        for idx, layer_data in data.get("layers", {}).items():
            layer = Layer(layer_data["index"], layer_data["name"], layer_data.get("parent_layer"))
            layer.keymap = {
                k: KeyAction(KeyActionType(v["type"]), bytes.fromhex(v["data"]) if v["data"] else b"")
                for k, v in layer_data.get("keymap", {}).items()
            }
            layers[int(idx)] = layer
        data["layers"] = layers
        
        # Convert macros
        macros = {}
        for idx, macro_data in data.get("macros", {}).items():
            macros[int(idx)] = Macro(macro_data["steps"], macro_data.get("repeat", False))
        data["macros"] = macros
        
        return cls(**data)
    
    def save_to_file(self, path: Path) -> None:
        """Save profile to YAML file."""
        path.write_text(yaml.dump(self.to_dict(), sort_keys=False, allow_unicode=True))
    
    @classmethod
    def load_from_file(cls, path: Path) -> "Profile":
        """Load profile from YAML file."""
        data = yaml.safe_load(path.read_text())
        return cls.from_dict(data)


class ProfileManager:
    """
    Manages keyboard profiles - both onboard (5 slots) and local file storage.
    
    Features:
    - 5 onboard profile slots (hardware)
    - Unlimited local profiles (YAML files)
    - Import/export between onboard and local
    - Profile metadata and tagging
    - Auto-sync on connect
    """
    
    def __init__(self, transport: HIDTransport, rgb: RGBController, keymap: KeyMap, 
                 profiles_dir: Optional[Path] = None):
        self.transport = transport
        self.rgb = rgb
        self.keymap = keymap
        self.profiles_dir = profiles_dir or Path.home() / ".config" / "redragon" / "profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self._local_profiles: Dict[str, Profile] = {}
        self._current_profile: Optional[Profile] = None
        self._load_local_profiles()
    
    def _load_local_profiles(self) -> None:
        """Load all local profiles from disk."""
        self._local_profiles.clear()
        for profile_file in self.profiles_dir.glob("*.yaml"):
            try:
                profile = Profile.load_from_file(profile_file)
                self._local_profiles[profile.name] = profile
            except Exception:
                pass  # Skip invalid profiles
    
    def create_profile(self, name: str, slot: int = 0, 
                       base_on_current: bool = True) -> Profile:
        """Create a new profile."""
        if base_on_current and self._current_profile:
            # Copy current settings
            profile = Profile(
                name=name,
                slot=slot,
                rgb_effect=self.rgb._current_effect.effect if self.rgb._current_effect else RGBEffect.STATIC,
                rgb_color=self.rgb._current_effect.color if self.rgb._current_effect else Color(255, 255, 255),
                rgb_speed=self.rgb._current_effect.speed if self.rgb._current_effect else EffectSpeed.NORMAL,
                rgb_direction=self.rgb._current_effect.direction if self.rgb._current_effect else 0,
                rgb_zone=self.rgb._current_effect.zone if self.rgb._current_effect else RGBZone.ALL,
                rgb_brightness=self.rgb._brightness,
                active_layer=self.keymap.active_layer,
                layers={k: Layer(v.index, v.name, v.parent_layer, v.keymap.copy()) 
                       for k, v in self.keymap.layers.items()},
                macros=self.keymap.macros.copy(),
            )
        else:
            profile = Profile(name=name, slot=slot)
        
        return profile
    
    def save_profile(self, profile: Profile, to_onboard: bool = True, 
                     to_local: bool = True) -> bool:
        """Save profile to onboard memory and/or local file."""
        success = True
        profile.modified = datetime.now().isoformat()
        
        if to_onboard:
            success &= self._save_to_onboard(profile)
        
        if to_local:
            success &= self._save_to_local(profile)
        
        return success
    
    def _save_to_onboard(self, profile: Profile) -> bool:
        """Save profile to keyboard onboard slot."""
        # First apply RGB settings
        self.rgb.set_effect(
            profile.rgb_effect, profile.rgb_color,
            profile.rgb_speed, profile.rgb_direction, profile.rgb_zone
        )
        self.rgb.set_brightness(profile.rgb_brightness)
        
        # Apply keymap (already sent via keymap.remap_key)
        
        # Save to onboard slot
        cmd = cmd_save_profile(profile.slot)
        try:
            response = self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
            _, _, success = parse_response(response)
            return success
        except TransportError:
            return False
    
    def _save_to_local(self, profile: Profile) -> bool:
        """Save profile to local YAML file."""
        try:
            filename = f"{profile.name.lower().replace(' ', '_')}.yaml"
            path = self.profiles_dir / filename
            profile.save_to_file(path)
            self._local_profiles[profile.name] = profile
            return True
        except Exception:
            return False
    
    def load_profile(self, name: str, from_onboard: bool = False) -> Optional[Profile]:
        """Load profile by name."""
        if from_onboard:
            # For onboard, name should be slot number
            try:
                slot = int(name)
                if self._load_from_onboard(slot):
                    return self._current_profile
            except ValueError:
                pass
            return None
        return self._load_from_local(name)
    
    def _load_from_onboard(self, slot: int) -> bool:
        """Load profile from onboard slot."""
        cmd = cmd_load_profile(slot)
        try:
            response = self.transport.send_feature_report(ReportID.FEATURE_SET, cmd)
            _, _, success = parse_response(response)
            if success:
                # Update current state from hardware
                self._refresh_from_hardware()
            return success
        except TransportError:
            return False
    
    def _load_from_local(self, name: str) -> Optional[Profile]:
        """Load profile from local storage and apply."""
        profile = self._local_profiles.get(name)
        if not profile:
            return None
        
        # Apply RGB
        self.rgb.set_effect(
            profile.rgb_effect, profile.rgb_color,
            profile.rgb_speed, profile.rgb_direction, profile.rgb_zone
        )
        self.rgb.set_brightness(profile.rgb_brightness)
        
        # Apply keymap
        self.keymap.active_layer = profile.active_layer
        self.keymap.layers = profile.layers
        self.keymap.macros = profile.macros
        
        self._current_profile = profile
        return profile
    
    def _refresh_from_hardware(self) -> None:
        """Query current state from keyboard and update local objects."""
        state = self.rgb.get_state()
        if state:
            self.rgb._current_effect = Effect(
                state["effect"],
                Color(255, 255, 255),  # Color not returned by hardware
                state["speed"],
                state["direction"]
            )
            self.rgb._brightness = state["brightness"]
    
    def list_profiles(self) -> List[dict]:
        """List all local profiles with metadata."""
        return [
            {
                "name": p.name,
                "slot": p.slot,
                "effect": p.rgb_effect.name,
                "color": p.rgb_color.to_hex(),
                "created": p.created,
                "modified": p.modified,
                "tags": p.tags,
                "description": p.description,
            }
            for p in self._local_profiles.values()
        ]
    
    def delete_profile(self, name: str, from_onboard: bool = False, 
                       from_local: bool = True) -> bool:
        """Delete a profile."""
        success = True
        
        if from_local and name in self._local_profiles:
            filename = f"{name.lower().replace(' ', '_')}.yaml"
            try:
                (self.profiles_dir / filename).unlink(missing_ok=True)
                del self._local_profiles[name]
            except Exception:
                success = False
        
        return success
    
    def export_profile(self, name: str, export_path: Path) -> bool:
        """Export profile to a portable file."""
        profile = self._local_profiles.get(name)
        if not profile:
            return False
        try:
            profile.save_to_file(export_path)
            return True
        except Exception:
            return False
    
    def import_profile(self, import_path: Path) -> Optional[Profile]:
        """Import profile from a file."""
        try:
            profile = Profile.load_from_file(import_path)
            self.save_profile(profile, to_onboard=False, to_local=True)
            return profile
        except Exception:
            return None
    
    @property
    def current_profile(self) -> Optional[Profile]:
        return self._current_profile
    
    @property
    def local_profiles(self) -> Dict[str, Profile]:
        return self._local_profiles.copy()