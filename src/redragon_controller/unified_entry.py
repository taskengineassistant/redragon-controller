"""
Unified Entry Point - Single EXE for all modes:
- GUI/Tray App (default, double-click)
- Windows Service (--service or started by SCM)
- CLI (subcommands: rgb, keymap, macro, profile, etc.)
"""

import sys
import os
import argparse

# Add src to path for frozen executable
if getattr(sys, 'frozen', False):
    # Running as PyInstaller bundle
    import sysconfig
    sys.path.insert(0, sys._MEIPASS)


def run_gui():
    """Run the GUI/Tray application."""
    from .tray_app import main as tray_main
    return tray_main()


def run_service():
    """Run as Windows Service."""
    from .windows_service import main as service_main
    # Pass remaining args to service main
    sys.argv = [sys.argv[0]] + sys.argv[2:]  # Remove 'redragon' and 'service'
    return service_main()


def run_cli():
    """Run CLI commands."""
    from .cli import main as cli_main
    # Pass remaining args to CLI
    sys.argv = [sys.argv[0]] + sys.argv[1:]  # Remove 'redragon'
    return cli_main()


def main():
    parser = argparse.ArgumentParser(
        prog="redragon",
        description="Redragon Keyboard Controller - GUI, Service & CLI in one",
        add_help=False
    )
    
    parser.add_argument(
        "mode",
        nargs="?",
        choices=["gui", "service", "cli"],
        default="gui",
        help="Run mode (default: gui)"
    )
    
    parser.add_argument(
        "-h", "--help",
        action="store_true",
        help="Show help"
    )
    
    # Parse just the first argument to determine mode
    args, remaining = parser.parse_known_args()
    
    # Help requested
    if args.help or (args.mode == "cli" and (not remaining or "-h" in remaining or "--help" in remaining)):
        if args.mode == "cli":
            # Show CLI help
            sys.argv = ["redragon"] + remaining + ["--help"]
            run_cli()
        else:
            # Show general help
            print("Redragon Keyboard Controller")
            print("=============================")
            print()
            print("Usage: redragon [MODE] [ARGS...]")
            print()
            print("Modes:")
            print("  gui      Start GUI with system tray (default, double-click)")
            print("  service  Run as Windows Service (install/start/stop/console)")
            print("  cli      Command-line interface (rgb, keymap, macro, profile)")
            print()
            print("Examples:")
            print("  redragon                    # Start GUI/Tray app")
            print("  redragon gui                # Same as above")
            print("  redragon service install    # Install Windows service")
            print("  redragon service start      # Start service")
            print("  redragon service console    # Run service in console (debug)")
            print("  redragon cli --help         # Show CLI commands")
            print("  redragon cli rgb --help     # RGB subcommands")
            print("  redragon cli profile list   # List profiles")
            print()
            print("Shortcuts (without 'cli' prefix):")
            print("  redragon rgb color ff0000   # Set color to red")
            print("  redragon profile save my    # Save current as 'my'")
        return 0
    
    # Route to appropriate mode
    if args.mode == "gui":
        return run_gui()
    elif args.mode == "service":
        return run_service()
    elif args.mode == "cli":
        return run_cli()
    else:
        # Default: GUI
        return run_gui()


if __name__ == "__main__":
    sys.exit(main())