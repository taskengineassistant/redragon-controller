"""
REST API Server
FastAPI-based HTTP API for controlling Redragon keyboards.
"""

from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import Literal

from .hid_transport import HIDTransport, DeviceInfo
from .rgb import RGBController, Color, RGBEffect, RGBZone, EffectSpeed, EffectDirection
from .keymap import KeyMap, KeyCode, KeyAction, KeyActionType, Macro
from .profiles import ProfileManager, Profile
from .protocol import Command, ReportID, build_command, parse_response


# Global state (in production, use proper dependency injection)
_transport: Optional[HIDTransport] = None
_rgb: Optional[RGBController] = None
_keymap: Optional[KeyMap] = None
_profiles: Optional[ProfileManager] = None


def get_transport() -> HIDTransport:
    if _transport is None or not _transport.is_connected:
        raise HTTPException(503, "No device connected")
    return _transport


def get_rgb() -> RGBController:
    if _rgb is None:
        raise HTTPException(503, "RGB controller not initialized")
    return _rgb


def get_keymap_dep() -> KeyMap:
    if _keymap is None:
        raise HTTPException(503, "Keymap not initialized")
    return _keymap


def get_profiles() -> ProfileManager:
    if _profiles is None:
        raise HTTPException(503, "Profile manager not initialized")
    return _profiles


# Pydantic models
class ColorModel(BaseModel):
    r: int = Field(ge=0, le=255)
    g: int = Field(ge=0, le=255)
    b: int = Field(ge=0, le=255)
    brightness: int = Field(default=255, ge=0, le=255)
    
    def to_color(self) -> Color:
        return Color(self.r, self.g, self.b, self.brightness)
    
    @classmethod
    def from_color(cls, color: Color) -> "ColorModel":
        return cls(r=color.r, g=color.g, b=color.b, brightness=color.brightness)


class RGBStaticRequest(BaseModel):
    color: ColorModel
    zone: Literal["all", "left", "right", "center", "wasd", "arrows", "function", "numbers", "custom"] = "all"
    key_bitmap: Optional[str] = None  # hex string


class RGBEffectRequest(BaseModel):
    effect: str  # RGBEffect name
    color: Optional[ColorModel] = None
    speed: int = Field(default=EffectSpeed.NORMAL, ge=0, le=255)
    direction: int = Field(default=EffectDirection.LEFT_TO_RIGHT, ge=0, le=5)
    zone: Literal["all", "left", "right", "center", "wasd", "arrows", "function", "numbers"] = "all"


class KeyRemapRequest(BaseModel):
    key: str
    action_type: Literal["keycode", "macro", "layer", "media", "mouse", "system", "none"]
    data: str = ""  # hex encoded
    layer: int = 0


class ProfileCreateRequest(BaseModel):
    name: str
    slot: int = Field(default=0, ge=0, le=4)
    save_onboard: bool = True
    save_local: bool = True


class ProfileLoadRequest(BaseModel):
    name: str
    from_onboard: bool = False


class DeviceResponse(BaseModel):
    vendor_id: str
    product_id: str
    manufacturer: str
    product: str
    serial_number: str
    name: str


class RGBStateResponse(BaseModel):
    effect: str
    speed: int
    direction: int
    brightness: int


class ProfileSummary(BaseModel):
    name: str
    slot: int
    effect: str
    color: str
    modified: str
    tags: List[str]
    description: str


# Zone mapping
ZONE_MAP = {
    "all": RGBZone.ALL,
    "left": RGBZone.LEFT,
    "right": RGBZone.RIGHT,
    "center": RGBZone.CENTER,
    "wasd": RGBZone.WASD,
    "arrows": RGBZone.ARROWS,
    "function": RGBZone.FUNCTION_ROW,
    "numbers": RGBZone.NUMBER_ROW,
    "custom": RGBZone.CUSTOM,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _transport, _rgb, _keymap, _profiles
    
    # Try to auto-discover and connect
    devices = HIDTransport.discover()
    if devices:
        try:
            _transport = HIDTransport(
                vendor_id=devices[0].vendor_id,
                product_id=devices[0].product_id,
                path=devices[0].path
            )
            _transport.connect()
            _rgb = RGBController(_transport)
            _keymap = KeyMap(_transport)
            _profiles = ProfileManager(_transport, _rgb, _keymap)
        except Exception as e:
            print(f"Failed to auto-connect: {e}")
    
    yield
    
    # Cleanup
    if _transport:
        _transport.disconnect()


app = FastAPI(
    title="Redragon Keyboard Controller API",
    description="REST API for controlling Redragon RGB keyboards",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "connected": _transport is not None and _transport.is_connected}


# Device endpoints
@app.get("/api/device", response_model=DeviceResponse)
async def get_device(transport: HIDTransport = Depends(get_transport)):
    info = transport.device_info
    if not info:
        raise HTTPException(503, "Device info not available")
    return DeviceResponse(
        vendor_id=f"0x{info.vendor_id:04x}",
        product_id=f"0x{info.product_id:04x}",
        manufacturer=info.manufacturer,
        product=info.product,
        serial_number=info.serial_number,
        name=transport.get_device_name(),
    )


@app.get("/api/device/discover")
async def discover_devices():
    devices = HIDTransport.discover()
    return [
        DeviceResponse(
            vendor_id=f"0x{d.vendor_id:04x}",
            product_id=f"0x{d.product_id:04x}",
            manufacturer=d.manufacturer,
            product=d.product,
            serial_number=d.serial_number,
            name=f"{d.manufacturer} {d.product}",
        )
        for d in devices
    ]


@app.post("/api/device/connect")
async def connect_device(vendor_id: int, product_id: int, path: Optional[str] = None):
    global _transport, _rgb, _keymap, _profiles
    
    if _transport:
        _transport.disconnect()
    
    try:
        _transport = HIDTransport(vendor_id=vendor_id, product_id=product_id, 
                                   path=path.encode() if path else None)
        _transport.connect()
        _rgb = RGBController(_transport)
        _keymap = KeyMap(_transport)
        _profiles = ProfileManager(_transport, _rgb, _keymap)
        return {"status": "connected", "device": _transport.get_device_name()}
    except Exception as e:
        raise HTTPException(400, f"Failed to connect: {e}")


@app.post("/api/device/disconnect")
async def disconnect_device():
    global _transport, _rgb, _keymap, _profiles
    if _transport:
        _transport.disconnect()
        _transport = _rgb = _keymap = _profiles = None
    return {"status": "disconnected"}


# RGB endpoints
@app.get("/api/rgb/status", response_model=RGBStateResponse)
async def get_rgb_status(rgb: RGBController = Depends(get_rgb)):
    state = rgb.get_state()
    if not state:
        raise HTTPException(503, "Could not query device state")
    return RGBStateResponse(
        effect=RGBEffect(state["effect"]).name,
        speed=state["speed"],
        direction=state["direction"],
        brightness=state["brightness"],
    )


@app.post("/api/rgb/static")
async def set_static_color(req: RGBStaticRequest, rgb: RGBController = Depends(get_rgb)):
    zone = ZONE_MAP[req.zone]
    key_bitmap = bytes.fromhex(req.key_bitmap) if req.key_bitmap else None
    
    success = rgb.set_static_color(req.color.to_color(), zone, key_bitmap)
    if not success:
        raise HTTPException(500, "Failed to set color")
    return {"status": "ok"}


@app.post("/api/rgb/effect")
async def set_effect(req: RGBEffectRequest, rgb: RGBController = Depends(get_rgb)):
    eff = RGBEffect[req.effect.upper()]
    zone = ZONE_MAP[req.zone]
    color = req.color.to_color() if req.color else None
    
    success = rgb.set_effect(eff, color, req.speed, req.direction, zone)
    if not success:
        raise HTTPException(500, "Failed to set effect")
    return {"status": "ok"}


@app.post("/api/rgb/off")
async def turn_off_rgb(rgb: RGBController = Depends(get_rgb)):
    success = rgb.off()
    if not success:
        raise HTTPException(500, "Failed to turn off RGB")
    return {"status": "ok"}


@app.post("/api/rgb/brightness")
async def set_brightness(level: int, rgb: RGBController = Depends(get_rgb)):
    level = max(0, min(255, level))
    success = rgb.set_brightness(level)
    if not success:
        raise HTTPException(500, "Failed to set brightness")
    return {"status": "ok", "brightness": level}


@app.post("/api/rgb/speed")
async def set_speed(speed: int, rgb: RGBController = Depends(get_rgb)):
    speed = max(0, min(255, speed))
    success = rgb.set_speed(speed)
    if not success:
        raise HTTPException(500, "Failed to set speed")
    return {"status": "ok", "speed": speed}


# Keymap endpoints
@app.get("/api/keymap/{layer}")
async def get_keymap(layer: int, keymap: KeyMap = Depends(get_keymap_dep)):
    keymap.active_layer = layer
    km = keymap.get_keymap(layer)
    
    result = {}
    for key_idx, action in km.items():
        key_name = next((k for k, v in keymap._key_index_map.items() if v == key_idx), f"key_{key_idx}")
        result[key_name] = {
            "type": action.action_type.name,
            "data": action.data.hex() if action.data else ""
        }
    return {"layer": layer, "keys": result}


@app.post("/api/keymap/remap")
async def remap_key(req: KeyRemapRequest, keymap: KeyMap = Depends(get_keymap_dep)):
    action_type = KeyActionType[req.action_type.upper()]
    data = bytes.fromhex(req.data) if req.data else b""
    action = KeyAction(action_type, data)
    
    success = keymap.remap_key(req.key, action, req.layer)
    if not success:
        raise HTTPException(500, "Failed to remap key")
    return {"status": "ok"}


@app.post("/api/keymap/disable")
async def disable_key(key: str, layer: int = 0, keymap: KeyMap = Depends(get_keymap_dep)):
    action = KeyAction(KeyActionType.NONE)
    success = keymap.remap_key(key, action, layer)
    if not success:
        raise HTTPException(500, "Failed to disable key")
    return {"status": "ok"}


@app.post("/api/keymap/layer")
async def set_layer_key(key: str, layer_index: int, momentary: bool = True, 
                        layer: int = 0, keymap: KeyMap = Depends(get_keymap_dep)):
    success = keymap.set_layer_key(key, layer_index, momentary, layer)
    if not success:
        raise HTTPException(500, "Failed to set layer key")
    return {"status": "ok"}


@app.post("/api/keymap/reset")
async def reset_keymap(keymap: KeyMap = Depends(get_keymap_dep)):
    success = keymap.reset_to_default()
    if not success:
        raise HTTPException(500, "Failed to reset keymap")
    return {"status": "ok"}


# Profile endpoints
@app.get("/api/profiles", response_model=List[ProfileSummary])
async def list_profiles(profiles: ProfileManager = Depends(get_profiles)):
    return profiles.list_profiles()


@app.post("/api/profiles")
async def create_profile(req: ProfileCreateRequest, profiles: ProfileManager = Depends(get_profiles)):
    profile = profiles.create_profile(req.name, req.slot)
    success = profiles.save_profile(profile, req.save_onboard, req.save_local)
    if not success:
        raise HTTPException(500, "Failed to save profile")
    return {"status": "ok", "profile": profile.name}


@app.post("/api/profiles/load")
async def load_profile(req: ProfileLoadRequest, profiles: ProfileManager = Depends(get_profiles)):
    profile = profiles.load_profile(req.name, req.from_onboard)
    if not profile:
        raise HTTPException(404, f"Profile not found: {req.name}")
    return {"status": "ok", "profile": profile.name}


@app.delete("/api/profiles/{name}")
async def delete_profile(name: str, profiles: ProfileManager = Depends(get_profiles)):
    success = profiles.delete_profile(name, from_onboard=False, from_local=True)
    if not success:
        raise HTTPException(500, "Failed to delete profile")
    return {"status": "ok"}


# Web UI (simple HTML)
@app.get("/", response_class=HTMLResponse)
async def web_ui():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Redragon Controller</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 2rem auto; padding: 0 1rem; }
        .card { border: 1px solid #ddd; border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem; }
        button { padding: 0.5rem 1rem; margin: 0.25rem; cursor: pointer; }
        input, select { padding: 0.5rem; margin: 0.25rem; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
        .status { padding: 1rem; border-radius: 4px; margin: 1rem 0; }
        .connected { background: #d4edda; color: #155724; }
        .disconnected { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <h1>Redragon Keyboard Controller</h1>
    <div id="status" class="status disconnected">Disconnected</div>
    
    <div class="card">
        <h2>Device</h2>
        <button onclick="discover()">Discover Devices</button>
        <button onclick="connect()">Connect to First</button>
        <button onclick="disconnect()">Disconnect</button>
        <pre id="device-info"></pre>
    </div>
    
    <div class="card">
        <h2>RGB Control</h2>
        <div class="grid">
            <div>
                <label>Color: <input type="color" id="rgb-color" value="#ff0000"></label>
                <label>Zone: <select id="rgb-zone"><option>all</option><option>left</option><option>right</option><option>center</option><option>wasd</option><option>arrows</option><option>function</option><option>numbers</option></select></label>
                <button onclick="setStatic()">Set Static Color</button>
            </div>
            <div>
                <label>Effect: <select id="rgb-effect"><option>static</option><option>breathing</option><option>wave</option><option>ripple</option><option>reactive</option><option>spectrum</option><option>rainbow_wave</option><option>starlight</option><option>scan</option></select></label>
                <label>Speed: <input type="range" id="rgb-speed" min="0" max="255" value="128"></label>
                <button onclick="setEffect()">Set Effect</button>
            </div>
        </div>
        <button onclick="rgbOff()">Turn Off</button>
        <button onclick="getRGBStatus()">Get Status</button>
        <pre id="rgb-status"></pre>
    </div>
    
    <div class="card">
        <h2>Profiles</h2>
        <input type="text" id="profile-name" placeholder="Profile name">
        <button onclick="saveProfile()">Save Profile</button>
        <button onclick="listProfiles()">List Profiles</button>
        <pre id="profile-list"></pre>
    </div>

    <script>
        async function api(path, options = {}) {
            const res = await fetch('/api' + path, {
                headers: {'Content-Type': 'application/json'},
                ...options
            });
            if (!res.ok) throw new Error(await res.text());
            return res.json();
        }
        
        function updateStatus(connected) {
            const el = document.getElementById('status');
            el.textContent = connected ? 'Connected' : 'Disconnected';
            el.className = 'status ' + (connected ? 'connected' : 'disconnected');
        }
        
        async function discover() {
            const devices = await api('/device/discover');
            document.getElementById('device-info').textContent = JSON.stringify(devices, null, 2);
        }
        
        async function connect() {
            const devices = await api('/device/discover');
            if (devices.length === 0) return alert('No devices found');
            await api('/device/connect', {
                method: 'POST',
                body: JSON.stringify({vendor_id: devices[0].vendor_id, product_id: devices[0].product_id})
            });
            updateStatus(true);
            getDeviceInfo();
        }
        
        async function disconnect() {
            await api('/device/disconnect', {method: 'POST'});
            updateStatus(false);
        }
        
        async function getDeviceInfo() {
            const info = await api('/device');
            document.getElementById('device-info').textContent = JSON.stringify(info, null, 2);
        }
        
        async function setStatic() {
            const color = document.getElementById('rgb-color').value;
            const zone = document.getElementById('rgb-zone').value;
            const r = parseInt(color.slice(1,3), 16);
            const g = parseInt(color.slice(3,5), 16);
            const b = parseInt(color.slice(5,7), 16);
            await api('/rgb/static', {
                method: 'POST',
                body: JSON.stringify({color: {r, g, b, brightness: 255}, zone})
            });
            getRGBStatus();
        }
        
        async function setEffect() {
            const effect = document.getElementById('rgb-effect').value;
            const speed = parseInt(document.getElementById('rgb-speed').value);
            const color = document.getElementById('rgb-color').value;
            const r = parseInt(color.slice(1,3), 16);
            const g = parseInt(color.slice(3,5), 16);
            const b = parseInt(color.slice(5,7), 16);
            await api('/rgb/effect', {
                method: 'POST',
                body: JSON.stringify({effect, color: {r, g, b, brightness: 255}, speed})
            });
            getRGBStatus();
        }
        
        async function rgbOff() {
            await api('/rgb/off', {method: 'POST'});
            getRGBStatus();
        }
        
        async function getRGBStatus() {
            const status = await api('/rgb/status');
            document.getElementById('rgb-status').textContent = JSON.stringify(status, null, 2);
        }
        
        async function saveProfile() {
            const name = document.getElementById('profile-name').value;
            if (!name) return alert('Enter profile name');
            await api('/profiles', {
                method: 'POST',
                body: JSON.stringify({name, slot: 0, save_onboard: true, save_local: true})
            });
            listProfiles();
        }
        
        async function listProfiles() {
            const profiles = await api('/profiles');
            document.getElementById('profile-list').textContent = JSON.stringify(profiles, null, 2);
        }
        
        // Auto-discover on load
        discover();
    </script>
</body>
</html>
"""


def run_server(host: str = "0.0.0.0", port: int = 8080, reload: bool = False):
    """Run the API server."""
    import uvicorn
    uvicorn.run("redragon_controller.api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server()