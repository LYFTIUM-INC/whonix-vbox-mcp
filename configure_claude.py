#!/usr/bin/env python3

import os
import json
import argparse
import subprocess
import sys
from pathlib import Path

def get_absolute_path(rel_path):
    """Convert relative path to absolute path."""
    return os.path.abspath(rel_path)

def find_claude_config_path():
    """Find Claude Desktop config path based on platform."""
    home = Path.home()
    
    if sys.platform == "darwin":  # macOS
        return home / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    elif sys.platform == "win32":  # Windows
        return home / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
    else:  # Linux
        return home / ".config" / "Claude" / "claude_desktop_config.json"

def update_claude_config(server_path, server_name="vbox-whonix"):
    """Update Claude Desktop config to include the VirtualBox-Whonix MCP server."""
    config_path = find_claude_config_path()
    server_abs_path = get_absolute_path(server_path)
    
    # Create config directory if it doesn't exist
    config_dir = config_path.parent
    if not config_dir.exists():
        print(f"Creating config directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # Load existing config or create new one
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                print(f"Loaded existing config from {config_path}")
        except json.JSONDecodeError:
            print(f"Error parsing config file {config_path}, creating new config")
            config = {}
    else:
        print(f"No existing config found at {config_path}, creating new config")
        config = {}
    
    # Initialize mcpServers section if it doesn't exist
    if "mcpServers" not in config:
        config["mcpServers"] = {}
    
    # Get Python path from venv if it exists
    python_path = "./venv/bin/python"
    if os.path.exists(python_path):
        python_path = get_absolute_path(python_path)
    else:
        python_path = "python3"  # Fall back to system Python
    
    # Add our server to the config
    config["mcpServers"][server_name] = {
        "command": python_path,
        "args": [server_abs_path]
    }
    
    # Write the updated config
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)
        print(f"Updated Claude config at {config_path}")
    
    print(f"\nAdded {server_name} MCP server to Claude Desktop configuration")
    print(f"Command: {python_path} {server_abs_path}")

def main():
    parser = argparse.ArgumentParser(description="Configure Claude Desktop for VirtualBox-Whonix MCP Server")
    parser.add_argument("--server-path", default="enhanced_server.py", help="Path to the server script")
    parser.add_argument("--server-name", default="vbox-whonix", help="Name for the MCP server in Claude config")
    args = parser.parse_args()
    
    print("VirtualBox-Whonix MCP Server Configuration for Claude Desktop")
    print("===========================================================")
    
    # Get script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    # Default server path
    server_path = args.server_path
    if not os.path.exists(server_path):
        print(f"Error: Server script not found at {server_path}")
        return 1
    
    # Update Claude config
    update_claude_config(server_path, args.server_name)
    
    print("\nConfiguration complete!")
    print("Please restart Claude Desktop to apply the changes.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
