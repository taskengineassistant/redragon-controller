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

REM Install dependencies
echo Installing dependencies...
pip install --upgrade pip setuptools wheel
pip install -e ".[windows,build]"

REM Create icon
echo Creating icon...
python scripts/create_icon.py

REM Build CLI (GUI, no console)
echo.
echo Building redragon-controller.exe (GUI)...
pyinstaller --clean --noconfirm ^
  --name=redragon-controller ^
  --onefile ^
  --windowed ^
  --icon=assets/redragon.ico ^
  --add-data "config;config" ^
  --add-data "assets;assets" ^
  --hidden-import=hidapi ^
  --hidden-import=pyyaml ^
  --hidden-import=click ^
  --hidden-import=rich ^
  --hidden-import=fastapi ^
  --hidden-import=uvicorn ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --hidden-import=win32serviceutil ^
  --hidden-import=win32service ^
  --hidden-import=win32event ^
  --hidden-import=servicemanager ^
  --collect-all=redragon_controller ^
  src/redragon_controller/cli.py

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
  --hidden-import=fastapi ^
  --hidden-import=uvicorn ^
  --hidden-import=pydantic ^
  --hidden-import=pydantic_settings ^
  --hidden-import=win32serviceutil ^
  --hidden-import=win32service ^
  --hidden-import=win32event ^
  --hidden-import=servicemanager ^
  --collect-all=redragon_controller ^
  src/redragon_controller/windows_service.py

if errorlevel 1 (
    echo ERROR: Service build failed
    pause
    exit /b 1
)

REM Create installer scripts
echo.
echo Creating installer scripts...
@echo @echo off > dist/install_service.bat
@echo echo Installing Redragon Controller Service... >> dist/install_service.bat
@echo redragon-service.exe install >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Starting service... >> dist/install_service.bat
@echo redragon-service.exe start >> dist/install_service.bat
@echo echo. >> dist/install_service.bat
@echo echo Service installed and started! >> dist/install_service.bat
@echo echo API available at: http://localhost:8080 >> dist/install_service.bat
@echo echo Web UI: http://localhost:8080 >> dist/install_service.bat
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
dist\redragon-controller.exe --help
dist\redragon-service.exe --help

echo.
echo ===========================================
echo BUILD SUCCESSFUL!
echo ===========================================
echo.
echo Output files in dist\:
echo   - redragon-controller.exe  (GUI app, run directly)
echo   - redragon-service.exe     (Service manager)
echo   - install_service.bat      (Run as Admin to install service)
echo   - uninstall_service.bat    (Run as Admin to remove service)
echo.
echo To install as Windows Service (run as Administrator):
echo   dist\install_service.bat
echo.
echo To run as regular app:
echo   dist\redragon-controller.exe
echo.
pause