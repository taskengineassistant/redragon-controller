"""
Command Line Interface
Main entry point for the redragon-controller CLI.
"""

import sys
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from .hid_transport import HIDTransport, DeviceInfo
from .rgb import RGBController, Color, RGBEffect, RGBZone, EffectSpeed, EffectDirection
from .keymap import KeyMap, KeyCode, KeyAction, KeyActionType, Macro
from .profiles import ProfileManager, Profile
from .protocol import Command


console = Console()


@click.group()
@click.option("--vendor-id", type=int, help="USB Vendor ID (hex)")
@click.option("--product-id", type=int, help="USB Product ID (hex)")
@click.option("--path", type=str, help="Device path")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, vendor_id, product_id, path, verbose):
    """Redragon Keyboard Controller - Cross-platform RGB & Key mapping control."""
    ctx.ensure_object(dict)
    ctx.obj["vendor_id"] = vendor_id
    ctx.obj["product_id"] = product_id
    ctx.obj["path"] = path.encode() if path else None
    ctx.obj["verbose"] = verbose
    
    # Initialize transport
    try:
        transport = HIDTransport(
            vendor_id=vendor_id,
            product_id=product_id,
            path=path.encode() if path else None
        )
        transport.connect()
        ctx.obj["transport"] = transport
        ctx.obj["rgb"] = RGBController(transport)
        ctx.obj["keymap"] = KeyMap(transport)
        ctx.obj["profiles"] = ProfileManager(transport, ctx.obj["rgb"], ctx.obj["keymap"])
        
        if verbose:
            console.print(f"[green]Connected to {transport.get_device_name()}[/green]")
    except Exception as e:
        console.print(f"[red]Failed to connect: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.pass_context
def discover(ctx):
    """Discover all connected Redragon keyboards."""
    devices = HIDTransport.discover()
    if not devices:
        console.print("[yellow]No Redragon keyboards found[/yellow]")
        return
    
    table = Table(title="Discovered Redragon Devices")
    table.add_column("Vendor ID", style="cyan")
    table.add_column("Product ID", style="cyan")
    table.add_column("Product", style="green")
    table.add_column("Serial", style="dim")
    table.add_column("Path", style="dim")
    
    for dev in devices:
        table.add_row(
            f"0x{dev.vendor_id:04x}",
            f"0x{dev.product_id:04x}",
            dev.product or "Unknown",
            dev.serial_number or "N/A",
            dev.path.decode() if dev.path else "N/A"
        )
    
    console.print(table)


@cli.group()
@click.pass_context
def rgb(ctx):
    """RGB lighting control commands."""
    pass


@rgb.command()
@click.argument("color")
@click.option("--zone", type=click.Choice(["all", "left", "right", "center", "wasd", "arrows", "function", "numbers", "custom"]), default="all")
@click.option("--brightness", type=int, default=255, help="Brightness 0-255")
@click.pass_context
def static(ctx, color, zone, brightness):
    """Set static color."""
    try:
        c = Color.from_hex(color)
        c.brightness = brightness
    except ValueError as e:
        console.print(f"[red]Invalid color: {e}[/red]")
        return
    
    zone_map = {
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
    
    rgb_ctrl = ctx.obj["rgb"]
    if rgb_ctrl.set_static_color(c, zone_map[zone]):
        console.print(f"[green]Set {zone} to {c.to_hex()}[/green]")
    else:
        console.print("[red]Failed to set color[/red]")


@rgb.command()
@click.argument("effect", type=click.Choice([e.name.lower() for e in RGBEffect]))
@click.option("--color", help="Base color (hex)")
@click.option("--speed", type=int, default=EffectSpeed.NORMAL)
@click.option("--direction", type=int, default=EffectDirection.LEFT_TO_RIGHT)
@click.option("--zone", type=click.Choice(["all", "left", "right", "center", "wasd", "arrows", "function", "numbers"]), default="all")
@click.pass_context
def effect(ctx, effect, color, speed, direction, zone):
    """Set built-in RGB effect."""
    rgb_ctrl = ctx.obj["rgb"]
    
    c = Color.from_hex(color) if color else None
    eff = RGBEffect[effect.upper()]
    zone_map = {
        "all": RGBZone.ALL, "left": RGBZone.LEFT, "right": RGBZone.RIGHT,
        "center": RGBZone.CENTER, "wasd": RGBZone.WASD, "arrows": RGBZone.ARROWS,
        "function": RGBZone.FUNCTION_ROW, "numbers": RGBZone.NUMBER_ROW,
    }
    
    if rgb_ctrl.set_effect(eff, c, speed, direction, zone_map[zone]):
        console.print(f"[green]Set effect: {effect}[/green]")
    else:
        console.print("[red]Failed to set effect[/red]")


@rgb.command()
@click.pass_context
def off(ctx):
    """Turn off all RGB lighting."""
    if ctx.obj["rgb"].off():
        console.print("[green]RGB turned off[/green]")
    else:
        console.print("[red]Failed to turn off RGB[/red]")


@rgb.command()
@click.argument("level", type=int)
@click.pass_context
def brightness(ctx, level):
    """Set global brightness (0-255)."""
    level = max(0, min(255, level))
    if ctx.obj["rgb"].set_brightness(level):
        console.print(f"[green]Brightness set to {level}[/green]")
    else:
        console.print("[red]Failed to set brightness[/red]")


@rgb.command()
@click.pass_context
def status(ctx):
    """Show current RGB status."""
    state = ctx.obj["rgb"].get_state()
    if state:
        table = Table(title="Current RGB State")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        table.add_row("Effect", RGBEffect(state["effect"]).name)
        table.add_row("Speed", str(state["speed"]))
        table.add_row("Direction", str(state["direction"]))
        table.add_row("Brightness", str(state["brightness"]))
        console.print(table)
    else:
        console.print("[yellow]Could not query device state[/yellow]")


@cli.group()
@click.pass_context
def keymap(ctx):
    """Key mapping and macro commands."""
    pass


@keymap.command()
@click.argument("from_key")
@click.argument("to_key")
@click.option("--layer", type=int, default=0)
@click.pass_context
def map(ctx, from_key, to_key, layer):
    """Remap a key to another key."""
    try:
        keycode = KeyCode[to_key] if to_key.upper() in KeyCode.__members__ else int(to_key, 0)
    except (KeyError, ValueError):
        console.print(f"[red]Invalid key: {to_key}[/red]")
        return
    
    action = KeyAction(KeyActionType.KEYCODE, bytes([keycode]))
    if ctx.obj["keymap"].remap_key(from_key, action, layer):
        console.print(f"[green]Mapped {from_key} -> {to_key}[/green]")
    else:
        console.print("[red]Failed to remap key[/red]")


@keymap.command()
@click.argument("key")
@click.option("--layer", type=int, default=0)
@click.pass_context
def disable(ctx, key, layer):
    """Disable a key."""
    action = KeyAction(KeyActionType.NONE)
    if ctx.obj["keymap"].remap_key(key, action, layer):
        console.print(f"[green]Disabled {key}[/green]")
    else:
        console.print("[red]Failed to disable key[/red]")


@keymap.command()
@click.argument("key")
@click.argument("layer_index", type=int)
@click.option("--momentary/--toggle", default=True)
@click.option("--layer", type=int, default=0)
@click.pass_context
def layer_key(ctx, key, layer_index, momentary, layer):
    """Set a key to switch layers."""
    if ctx.obj["keymap"].set_layer_key(key, layer_index, momentary, layer):
        console.print(f"[green]Set {key} to layer {layer_index} ({'momentary' if momentary else 'toggle'})[/green]")
    else:
        console.print("[red]Failed to set layer key[/red]")


@keymap.command()
@click.option("--layer", type=int, default=0)
@click.pass_context
def show(ctx, layer):
    """Show current keymap for a layer."""
    keymap_obj = ctx.obj["keymap"]
    keymap_obj.active_layer = layer
    km = keymap_obj.get_keymap(layer)
    
    table = Table(title=f"Keymap - Layer {layer}")
    table.add_column("Key", style="cyan")
    table.add_column("Action", style="green")
    table.add_column("Data", style="dim")
    
    for key_idx, action in km.items():
        key_name = next((k for k, v in keymap_obj._key_index_map.items() if v == key_idx), f"key_{key_idx}")
        table.add_row(key_name, action.action_type.name, action.data.hex() if action.data else "")
    
    console.print(table)


@keymap.command()
@click.pass_context
def reset(ctx):
    """Reset keymap to factory defaults."""
    if Confirm.ask("Reset all key mappings to defaults?"):
        if ctx.obj["keymap"].reset_to_default():
            console.print("[green]Keymap reset to defaults[/green]")
        else:
            console.print("[red]Failed to reset keymap[/red]")


@cli.group()
@click.pass_context
def profile(ctx):
    """Profile management commands."""
    pass


@profile.command()
@click.argument("name")
@click.option("--slot", type=int, default=0, help="Onboard slot (0-4)")
@click.option("--no-onboard", is_flag=True, help="Don't save to onboard memory")
@click.option("--no-local", is_flag=True, help="Don't save to local file")
@click.pass_context
def save(ctx, name, slot, no_onboard, no_local):
    """Save current configuration as a profile."""
    profiles = ctx.obj["profiles"]
    profile = profiles.create_profile(name, slot)
    
    if profiles.save_profile(profile, to_onboard=not no_onboard, to_local=not no_local):
        console.print(f"[green]Saved profile: {name}[/green]")
    else:
        console.print("[red]Failed to save profile[/red]")


@profile.command()
@click.argument("name")
@click.option("--onboard/--local", default=False, help="Load from onboard slot")
@click.pass_context
def load(ctx, name, onboard):
    """Load a profile."""
    profiles = ctx.obj["profiles"]
    profile = profiles.load_profile(name, from_onboard=onboard)
    if profile:
        console.print(f"[green]Loaded profile: {name}[/green]")
    else:
        console.print(f"[red]Profile not found: {name}[/red]")


@profile.command()
@click.pass_context
def list(ctx):
    """List all saved profiles."""
    profiles = ctx.obj["profiles"]
    profile_list = profiles.list_profiles()
    
    if not profile_list:
        console.print("[yellow]No profiles saved[/yellow]")
        return
    
    table = Table(title="Saved Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Slot", style="dim")
    table.add_column("Effect", style="green")
    table.add_column("Color", style="magenta")
    table.add_column("Modified", style="dim")
    table.add_column("Tags", style="yellow")
    
    for p in profile_list:
        table.add_row(
            p["name"], str(p["slot"]), p["effect"], p["color"],
            p["modified"][:10], ", ".join(p["tags"])
        )
    
    console.print(table)


@profile.command()
@click.argument("name")
@click.option("--onboard/--local", default=False)
@click.pass_context
def delete(ctx, name, onboard):
    """Delete a profile."""
    profiles = ctx.obj["profiles"]
    if profiles.delete_profile(name, from_onboard=onboard, from_local=not onboard):
        console.print(f"[green]Deleted profile: {name}[/green]")
    else:
        console.print("[red]Failed to delete profile[/red]")


@profile.command()
@click.argument("name")
@click.argument("export_path", type=click.Path(path_type=Path))
@click.pass_context
def export(ctx, name, export_path):
    """Export a profile to a file."""
    profiles = ctx.obj["profiles"]
    if profiles.export_profile(name, export_path):
        console.print(f"[green]Exported {name} to {export_path}[/green]")
    else:
        console.print("[red]Export failed[/red]")


@profile.command()
@click.argument("import_path", type=click.Path(exists=True, path_type=Path))
@click.pass_context
def import_profile(ctx, import_path):
    """Import a profile from a file."""
    profiles = ctx.obj["profiles"]
    profile = profiles.import_profile(import_path)
    if profile:
        console.print(f"[green]Imported profile: {profile.name}[/green]")
    else:
        console.print("[red]Import failed[/red]")


@cli.command()
@click.pass_context
def info(ctx):
    """Show device information."""
    transport = ctx.obj["transport"]
    info = transport.device_info
    
    if info:
        panel = Panel(
            f"[bold]Device:[/bold] {transport.get_device_name()}\n"
            f"[bold]Vendor ID:[/bold] 0x{info.vendor_id:04x}\n"
            f"[bold]Product ID:[/bold] 0x{info.product_id:04x}\n"
            f"[bold]Manufacturer:[/bold] {info.manufacturer}\n"
            f"[bold]Product:[/bold] {info.product}\n"
            f"[bold]Serial:[/bold] {info.serial_number}",
            title="Device Info"
        )
        console.print(panel)


@cli.command()
@click.pass_context
def interactive(ctx):
    """Start interactive mode."""
    console.print(Panel("[bold cyan]Redragon Controller Interactive Mode[/bold cyan]\nType 'help' for commands, 'exit' to quit"))
    
    while True:
        try:
            cmd = Prompt.ask("[cyan]redragon>[/cyan]").strip()
            if cmd in ("exit", "quit", "q"):
                break
            elif cmd in ("help", "h", "?"):
                console.print("Commands: discover, rgb, keymap, profile, info, exit")
            elif cmd:
                # Parse and execute
                try:
                    ctx.invoke(cli, *cmd.split(), standalone_mode=False)
                except SystemExit:
                    pass
                except Exception as e:
                    console.print(f"[red]Error: {e}[/red]")
        except (KeyboardInterrupt, EOFError):
            break
    
    console.print("[yellow]Goodbye![/yellow]")


def main():
    cli(obj={})


if __name__ == "__main__":
    main()