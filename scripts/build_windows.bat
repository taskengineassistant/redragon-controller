@echo off
REM ===========================================
REM Redragon Controller - Windows Build Script
REM ===========================================
REM Run this on Windows to build the single .exe
REM Requires: Python 3.11+, Visual C++ Build Tools

echo Building Redragon Controller for Windows...
echo.

REM Check Python
python --version
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.11+ from python.org
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install -e ".[windows,build]"
pip install Pillow

REM Create icon
echo Creating icon...
python scripts/create_icon.py

REM Build Unified Executable (GUI + Service + CLI in ONE)
echo.
echo Building redragon.exe (Unified: GUI + Service + CLI)...
pyinstaller --clean --noconfirm ^
  --name=redragon ^
  --onefile ^
  --windowed ^
  --icon=assets/redragon.ico ^
  --add-data "config;config" ^
  --add-data "assets;assets" ^
  --add-data "src/redragon_controller/gui;gui" ^
  --hidden-import=hidapi ^
  --hidden-import=pyyaml ^
  --hidden-import=click ^
  --hidden-import=rich ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --hidden-import=PySide6.QtCore ^
  --hidden-import=PySide6.QtWidgets ^
  --hidden-import=PySide6.QtGui ^
  --hidden-import=PySide6.QtSvg ^
  --hidden-import=win32serviceutil ^
  --hidden-import=win32service ^
  --hidden-import=win32event ^
  --hidden-import=servicemanager ^
  --collect-all=redragon_controller ^
  src/redragon_controller/unified_entry.py

if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

REM Create installer scripts
echo.
echo Creating installer scripts...
@echo @echo off > dist/install_service.bat
@echo echo Installing Redragon Controller Service... >> dist/install_service.bat
@echo redragon.exe service install >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Starting service... >> dist/install_service.bat
@echo redragon.exe service start >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Service installed and started! >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo pause >> dist/install_service.bat

@echo @echo off > dist/uninstall_service.bat
@echo echo Stopping and uninstalling Redragon Controller Service... >> dist/uninstall_service.bat
@echo redragon.exe service stop >> dist/uninstall_service.bat
@echo redragon.exe service uninstall >> dist/uninstall_service.bat
@echo echo. >> dist/uninstall_service.bat
@echo echo Service uninstalled! >> dist/uninstall_service.bat
@echo pause >> dist/uninstall_service.bat

REM Copy config files and manage_service.ps1 to dist for release package
copy config\devices.yaml dist\
copy config\effects.yaml dist\
copy config\default_profile.yaml dist\
copy config\99-redragon.rules dist\
copy scripts\manage_service.ps1 dist\

REM Verify
echo.
echo Verifying build...
dist\redragon.exe cli --help
dist\redragon.exe service --help

echo.
echo ===========================================
echo BUILD SUCCESSFUL!
echo ===========================================
echo.
echo Output files in dist\:
echo   - redragon.exe           (UNIFIED: GUI + Service + CLI)
echo   - install_service.bat    (Run as Admin to install service)
echo   - uninstall_service.bat  (Run as Admin to remove service)
echo   - config files & manage_service.ps1
echo.
echo USAGE:
echo   1. Double-click redragon.exe           -> GUI with System Tray
echo   2. redragon.exe                        -> Same (default = GUI)
echo   3. redragon.exe gui                    -> Explicit GUI mode
echo   4. redragon.exe service install        -> Install Windows Service (Admin)
echo   5. redragon.exe service start          -> Start Service (Admin)
echo   6. redragon.exe service console        -> Debug Service in console
echo   7. redragon.exe cli --help             -> CLI help
echo   8. redragon.exe rgb color ff0000       -> Quick CLI (no 'cli' prefix)
echo   9. redragon.exe profile list           -> Quick CLI
echo.
pause