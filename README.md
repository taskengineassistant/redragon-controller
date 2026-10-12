# Redragon Keyboard Controller
Cross-platform, highly customizable controller for Redragon RGB keyboards (K585, K552, K530, etc.)
Built with Python + hidapi, containerized with Docker, reverse-engineered using REA.

## Features
- 🎨 **Full RGB Control** - Per-key, zones, effects, animations
- ⌨️ **Key Remapping** - Custom layouts, macros, layers
- 🔧 **Hardware Profiles** - Save/load profiles to keyboard onboard memory
- 🐳 **Docker Support** - Run anywhere, no driver conflicts
- 🌐 **REST API** - Control via HTTP for integrations
- 📱 **Web UI** - Browser-based configuration
- 🔌 **Plugin System** - Extend with custom effects/integrations
- 🖥️ **Modern GUI** - Native PySide6 window with system tray, German UI
- ⌨️ **Per-Key Customization** - Every key individually configurable

## Supported Keyboards
| Model | VID | PID | Status |
|-------|-----|-----|--------|
| K585 RGB | 0x258a | 0x0001 | 🔍 Reverse Engineering |
| K552 RGB | 0x258a | 0x0002 | 📋 Planned |
| K530 Pro | 0x258a | 0x0003 | 📋 Planned |

## Quick Start

### Docker (Recommended)
```bash
docker run -d \
  --name redragon-controller \
  --device /dev/hidraw0:/dev/hidraw0 \
  -p 8080:8080 \
  -v ./config:/app/config \
  ghcr.io/yourusername/redragon-controller:latest
```

### Windows .exe (Standalone)
**Option 1: Download Release** (Recommended)
- Go to [GitHub Releases](https://github.com/taskengineassistant/redragon-controller/releases)
- Download `redragon-controller-vX.Y.Z-windows-x64.zip`
- Extract and run `redragon-tray.exe` (Main GUI App)

**Option 2: Build Yourself**
```cmd
REM Run in Developer Command Prompt for VS (or with Build Tools installed)
scripts\build_windows.bat
```

**Option 3: Python Native**
```powershell
pip install -e ".[windows]"
redragon-tray
```

### Main GUI App (`redragon-tray.exe`)
The **primary way to use Redragon Controller** - a native Windows application with:
- **System Tray** - Runs in background, click to open window
- **Modern German UI** - 6 tabs: Dashboard, RGB, Keymap, Macros, Profiles, Settings
- **Per-Key RGB** - Click any key to set individual color
- **Visual Keyboard** - Interactive TKL/Full-size keyboard display
- **Macro Recorder** - Record keystrokes as macros
- **Profile Management** - Save to onboard memory + local files
- **Auto-start** - Optional Windows startup integration

```cmd
# Run directly (shows window, minimizes to tray on close)
redragon-tray.exe

# Or add shortcut to shell:startup for auto-start
```

### CLI (`redragon-cli.exe`)
Command-line interface for scripts/automation:
```cmd
redragon-cli.exe --discover
redragon-cli.exe --set-color ff0000 --zone all
redragon-cli.exe --effect breathing --color 00ff00 --speed 5
```

### Native Python (Linux/macOS)
```bash
pip install -r requirements.txt
python -m redragon_controller --discover
python -m redragon_controller --set-color ff0000 --zone all
```

## Windows Service (Background Daemon)

The `redragon-service.exe` runs as a **Windows Service** (auto-start on boot, background, no UI).

### Install as Service (Run as Administrator)
```cmd
REM Option 1: Use installer script
dist\install_service.bat

REM Option 2: PowerShell (more control)
.\scripts\manage_service.ps1 -Action Install

REM Option 3: Direct command
redragon-service.exe install
redragon-service.exe start
```

### Service Management
```cmd
# Start/Stop/Restart
redragon-service.exe start
redragon-service.exe stop
redragon-service.exe restart

# Check status
redragon-service.exe status

# Uninstall
redragon-service.exe uninstall

# PowerShell wrapper
.\scripts\manage_service.ps1 -Action Start
.\scripts\manage_service.ps1 -Action Stop
.\scripts\manage_service.ps1 -Action Status
```

### Service Details
| Property | Value |
|----------|-------|
| **Service Name** | `RedragonController` |
| **Display Name** | `Redragon Keyboard Controller` |
| **Start Type** | Automatic (boot) |
| **Port** | 8080 (REST API + Web UI) |
| **Config** | `%PROGRAMDATA%\RedragonController\profiles\` |
| **Logs** | Windows Event Log (Application) |

### Firewall Rule (Allow API Access)
```powershell
# Run as Admin
New-NetFirewallRule -DisplayName "Redragon Controller API" -Direction Inbound -LocalPort 8080 -Protocol TCP -Action Allow
```

## Architecture
```
redragon-controller/
├── src/redragon_controller/
│   ├── __init__.py
│   ├── hid_transport.py      # Low-level HID communication
│   ├── protocol.py           # Redragon command protocol
│   ├── rgb.py                # RGB effects & animations
│   ├── keymap.py             # Key remapping & macros
│   ├── profiles.py           # Profile management
│   ├── api.py                # FastAPI REST server
│   ├── cli.py                # Command-line interface
│   ├── windows_service.py    # Windows Service wrapper
│   └── gui/                  # PySide6 GUI package
│       ├── __init__.py
│       ├── i18n.py           # German translations
│       ├── keyboard_visualizer.py
│       ├── rgb_panel.py
│       ├── keymap_panel.py
│       ├── macros_panel.py
│       ├── profiles_panel.py
│       ├── settings_panel.py
│       ├── dashboard_panel.py
│       ├── main_window.py
│       └── tray_app.py
├── config/
│   ├── devices.yaml          # Device definitions
│   ├── effects.yaml          # Built-in effects
│   ├── default_profile.yaml  # Default keymap/RGB
│   └── 99-redragon.rules     # Udev rules (Linux)
├── assets/                   # Icons, images
├── scripts/                  # Build/install scripts
├── web-ui/                   # React/Vue frontend (optional)
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── pyproject.toml
```

## Protocol Notes (from REA Analysis)
- **Transport**: USB HID (Feature Reports: 0x01/0x02, Output Reports: 0x03)
- **Command Structure**: `[Report ID][Command][Length][Data...][Checksum]`
- **RGB Commands**: 0x10-0x1F range (per-key, zone, effect, speed, brightness)
- **Key Remap**: 0x20-0x2F (scancode mapping, macros, layers)
- **Profile Storage**: 0x30-0x3F (save/load/activate 5 onboard profiles)

## Development
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Build Docker
docker build -t redragon-controller .

# Run web UI dev server
cd web-ui && npm run dev
```

## License
MIT - Built for the community, reverse-engineered for interoperability.

## Credits
- REA (Reverse Engineer Anything) for binary analysis
- hidapi / python-hid for cross-platform HID
- Redragon community for protocol documentation