#!/bin/bash

# Quick start script for Whonix VirtualBox MCP
# This script activates the virtual environment and starts the MCP server

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "Starting Whonix VirtualBox MCP..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Installing dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if VirtualBox is accessible
echo "Checking VirtualBox installation..."
if ! command -v VBoxManage &> /dev/null; then
    echo "WARNING: VBoxManage not found in PATH"
    echo "Please ensure VirtualBox is installed and VBoxManage is accessible"
fi

# Start the MCP server
echo "Starting MCP server..."
exec python consolidated_mcp_whonix.py
