#!/usr/bin/env python3
"""
Tray App Entry Point for PyInstaller
Uses absolute imports to work as standalone executable.
"""

import sys
import os

# Add src to path for absolute imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from redragon_controller.tray_app import main

if __name__ == "__main__":
    main()