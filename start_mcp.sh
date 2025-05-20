#!/bin/bash
#
# Quick start script for vbox-whonix MCP server
#

# Change to the script directory
cd "$(dirname "$0")"

# Activate the virtual environment
source venv/bin/activate

# Start the MCP server
echo "Starting Consolidated Whonix VirtualBox MCP server..."
nohup python consolidated_mcp_whonix.py > /tmp/vbox-whonix-mcp.log 2>&1 &

# Check if server started
sleep 2
if ps -p $! > /dev/null; then
  echo "Server started successfully with PID $!"
  echo "Logs being written to /tmp/vbox-whonix-mcp.log"
else
  echo "Server failed to start. Check logs at /tmp/vbox-whonix-mcp.log"
fi
