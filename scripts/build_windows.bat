@echo off
REM ===========================================
REM Redragon Controller - Windows Build Script
REM ===========================================
REM Run this on Windows to build the .exe files
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

# Install dependencies
echo Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install -e ".[windows,build]"
pip install Pillow

REM Create icon
echo Creating icon...
python scripts/create_icon.py

REM Build Tray App (Main GUI - windowed, no console)
echo.
echo Building redragon-tray.exe (Main GUI)...
pyinstaller --clean --noconfirm ^
  --name=redragon-tray ^
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
  src/redragon_controller/tray_entry.py

if errorlevel 1 (
    echo ERROR: Tray app build failed
    pause
    exit /b 1
)

REM Build CLI (for command-line usage)
echo.
echo Building redragon-cli.exe (CLI)...
pyinstaller --clean --noconfirm ^
  --name=redragon-cli ^
  --onefile ^
  --console ^
  --icon=assets/redragon.ico ^
  --add-data "config;config" ^
  --add-data "assets;assets" ^
  --hidden-import=hidapi ^
  --hidden-import=pyyaml ^
  --hidden-import=click ^
  --hidden-import=rich ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --collect-all=redragon_controller ^
  src/redragon_controller/cli_entry.py

if errorlevel 1 (
    echo ERROR: CLI build failed
    pause
    exit /b 1
)

REM Build Service (Console for service management)
echo.
echo Building redragon-service.exe (Service)... 
pyinstaller --clean --noconfirm ^
  --name=redragon-service ^
  --onefile ^
  --console ^
  --icon=assets/redragon.ico ^
  --add-data "config;config" ^
  --add-data "assets;assets" ^
  --hidden-import=hidapi ^
  --hidden-import=pyyaml ^
  --hidden-import=click ^
  --hidden-import=rich ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --hidden-import=win32serviceutil ^
  --hidden-import=win32service ^
  --hidden-import=win32event ^
  --hidden-import=servicemanager ^
  --collect-all=redragon_controller ^
  src/redragon_controller/service_entry.py

if errorlevel 1 (
    echo ERROR: Service build failed
    pause
    exit /b 1
)

REM Create installer scripts
echo.
echo Creating installer scripts...
@echo @echo off > dist/install_tray.bat
@echo echo Installing Redragon Controller Tray App... >> dist/install_tray.bat
@echo echo. >> dist/install_tray.bat
@echo echo The tray app will start automatically on login. >> dist/install_tray.bat
@echo echo. >> dist/install_tray.bat
@echo echo To add to startup: >> dist/install_tray.bat
@echo echo   1. Press Win+R, type: shell:startup >> dist/install_tray.bat
@echo echo   2. Create shortcut to redragon-tray.exe in that folder >> dist/install_tray.bat
@echo echo. >> dist/install_tray.bat
@echo pause >> dist/install_tray.bat

@echo @echo off > dist/install_service.bat
@echo echo Installing Redragon Controller Service... >> dist/install_service.bat
@echo redragon-service.exe install >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Starting service... >> dist/install_service.bat
@echo redragon-service.exe start >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Service installed and started! >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo pause >> dist/install_service.bat

@echo @echo off > dist/uninstall_service.bat
@echo echo Stopping and uninstalling Redragon Controller Service... >> dist/uninstall_service.bat
@echo redragon-service.exe stop >> dist/uninstall_service.bat
@echo redragon-service.exe uninstall >> dist/uninstall_service.bat
@echo echo. >> dist/uninstall_service.bat
@echo echo Service uninstalled! >> dist/uninstall_service.bat
@echo pause >> dist/uninstall_service.bat

REM Verify
echo.
echo Verifying builds...
dist\redragon-tray.exe --help 2>nul || echo (tray app has no --help, this is expected)
dist\redragon-cli.exe --help
dist\redragon-service.exe --help

echo.
echo ===========================================
echo BUILD SUCCESSFUL!
echo ===========================================
echo.
echo Output files in dist\:
echo   - redragon-tray.exe      (MAIN APP - System Tray + Window)
echo   - redragon-cli.exe       (Command-line interface)
echo   - redragon-service.exe   (Windows Service manager)
echo   - install_tray.bat       (Tray app startup helper)
echo   - install_service.bat    (Run as Admin to install service)
echo   - uninstall_service.bat  (Run as Admin to remove service)
echo.
echo USAGE:
echo   1. Run redragon-tray.exe directly for the GUI with system tray
echo   2. Or install as service: dist\install_service.bat (as Admin)
echo   3. CLI: redragon-cli.exe --help
echo.
pause