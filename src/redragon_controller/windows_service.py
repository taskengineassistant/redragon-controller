"""
Windows Service Wrapper
Allows redragon-controller to run as a Windows Background Service.
No web server - pure HID communication and profile sync.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Windows service imports (only available on Windows)
try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

from .hid_transport import HIDTransport, DeviceInfo
from .rgb import RGBController
from .keymap import KeyMap
from .profiles import ProfileManager


SERVICE_NAME = "RedragonController"
SERVICE_DISPLAY_NAME = "Redragon Keyboard Controller"
SERVICE_DESCRIPTION = "Background service for Redragon keyboard RGB & keymap management. Handles HID communication and profile synchronization."


class RedragonService(win32serviceutil.ServiceFramework):
    """Windows Service implementation."""

    _svc_name_ = SERVICE_NAME
    _svc_display_name_ = SERVICE_DISPLAY_NAME
    _svc_description_ = SERVICE_DESCRIPTION

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = False
        self.worker_thread = None
        self.transport = None
        self.rgb = None
        self.keymap = None
        self.profiles = None
        self._last_device_check = 0
        self._device_check_interval = 10  # seconds
        self._connection_retry_interval = 30  # seconds

    def SvcStop(self):
        """Called when service is stopping."""
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.is_running = False

        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=5)

        if self.transport:
            try:
                self.transport.disconnect()
            except Exception:
                pass

        win32event.SetEvent(self.hWaitStop)
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)

    def SvcDoRun(self):
        """Main service loop - must return quickly to avoid 1053 timeout."""
        # Report START_PENDING immediately
        self.ReportServiceStatus(win32service.SERVICE_START_PENDING)
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )

        self.is_running = True
        
        # Start background worker IMMEDIATELY (non-blocking)
        self.worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True
        )
        self.worker_thread.start()

        # Report RUNNING status - service is now "started" from SCM perspective
        self.ReportServiceStatus(win32service.SERVICE_RUNNING)
        servicemanager.LogInfoMsg("Redragon Controller Service started successfully")

        # Wait for stop signal (this blocks until SvcStop is called)
        win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE)

    def _connect_device(self):
        """Auto-discover and connect to Redragon device. Non-blocking, returns bool."""
        try:
            devices = HIDTransport.discover()
            if not devices:
                return False

            # Use first discovered device
            dev = devices[0]
            self.transport = HIDTransport(
                vendor_id=dev.vendor_id,
                product_id=dev.product_id,
                path=dev.path
            )
            self.transport.connect()

            self.rgb = RGBController(self.transport)
            self.keymap = KeyMap(self.transport)
            self.profiles = ProfileManager(self.transport, self.rgb, self.keymap)

            # Load default profile if exists
            self.profiles.load_profile("Default", from_onboard=False)

            servicemanager.LogInfoMsg(f"Connected to {self.transport.get_device_name()}")
            return True

        except Exception as e:
            servicemanager.LogErrorMsg(f"Device connection failed: {e}")
            self.transport = None
            self.rgb = None
            self.keymap = None
            self.profiles = None
            return False

    def _worker_loop(self):
        """Background loop: monitor device, sync profiles, keep connection alive."""
        # Initial connection attempt (non-blocking)
        self._connect_device()
        last_retry = time.time()

        while self.is_running:
            try:
                current_time = time.time()

                # Periodic device check / reconnect
                if not self.transport or not self.transport.is_connected():
                    # Only retry periodically to avoid spam
                    if current_time - last_retry >= self._connection_retry_interval:
                        last_retry = current_time
                        servicemanager.LogInfoMsg("Attempting device reconnect...")
                        self._connect_device()
                else:
                    # Device connected - could do periodic profile sync here
                    pass

                # Sleep a bit to avoid busy loop
                time.sleep(1)

            except Exception as e:
                servicemanager.LogErrorMsg(f"Worker loop error: {e}")
                time.sleep(5)


def install_service():
    """Install the Windows service."""
    if not HAS_WIN32:
        print("pywin32 not installed. Run: pip install pywin32")
        return False

    try:
        win32serviceutil.InstallService(
            __file__,
            SERVICE_NAME,
            SERVICE_DISPLAY_NAME,
            startType=win32service.SERVICE_AUTO_START,
            description=SERVICE_DESCRIPTION
        )
        print(f"Service '{SERVICE_DISPLAY_NAME}' installed successfully")
        print("Start it with: net start RedragonController")
        return True
    except Exception as e:
        print(f"Failed to install service: {e}")
        return False


def uninstall_service():
    """Uninstall the Windows service."""
    if not HAS_WIN32:
        print("pywin32 not installed")
        return False

    try:
        win32serviceutil.RemoveService(SERVICE_NAME)
        print(f"Service '{SERVICE_NAME}' uninstalled successfully")
        return True
    except Exception as e:
        print(f"Failed to uninstall service: {e}")
        return False


def start_service():
    """Start the Windows service."""
    if not HAS_WIN32:
        return False
    try:
        win32serviceutil.StartService(SERVICE_NAME)
        print("Service started")
        return True
    except Exception as e:
        print(f"Failed to start service: {e}")
        return False


def stop_service():
    """Stop the Windows service."""
    if not HAS_WIN32:
        return False
    try:
        win32serviceutil.StopService(SERVICE_NAME)
        print("Service stopped")
        return True
    except Exception as e:
        print(f"Failed to stop service: {e}")
        return False


def run_as_console():
    """Run as console application (for debugging)."""
    print("Running Redragon Controller in console mode...")
    print("Press Ctrl+C to stop")

    # Initialize
    devices = HIDTransport.discover()
    if devices:
        transport = HIDTransport(
            vendor_id=devices[0].vendor_id,
            product_id=devices[0].product_id,
            path=devices[0].path
        )
        transport.connect()
        rgb = RGBController(transport)
        keymap = KeyMap(transport)
        profiles = ProfileManager(transport, rgb, keymap)
        profiles.load_profile("Default", from_onboard=False)
        print(f"Connected to {transport.get_device_name()}")
    else:
        print("No Redragon device found")

    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")


def main():
    """Main entry point for windows service."""
    if not HAS_WIN32:
        print("This module requires Windows and pywin32")
        print("Run on Windows with: pip install pywin32")
        sys.exit(1)

    if len(sys.argv) == 1:
        # No arguments - run as service (called by SCM)
        win32serviceutil.HandleCommandLine(RedragonService)
    else:
        command = sys.argv[1].lower()
        if command == "install":
            install_service()
        elif command == "uninstall":
            uninstall_service()
        elif command == "start":
            start_service()
        elif command == "stop":
            stop_service()
        elif command == "console":
            run_as_console()
        elif command == "restart":
            stop_service()
            time.sleep(2)
            start_service()
        else:
            print(f"Unknown command: {command}")
            print("Usage: redragon-service [install|uninstall|start|stop|restart|console]")


if __name__ == "__main__":
    main()