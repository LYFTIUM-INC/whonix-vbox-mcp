#!/bin/bash
#
# Run script for consolidated Whonix VirtualBox MCP implementation
#

# Set environment variables
export USER=$(id -un)
export LOGNAME=$(id -un)
export HOME=$(eval echo ~$(id -un))

# Print environment info
echo "Environment:"
echo "USER=$USER"
echo "LOGNAME=$LOGNAME"
echo "HOME=$HOME"
echo "Effective UID=$(id -u)"
echo "Effective username=$(id -un)"

# Activate the virtual environment
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
fi

# Check VirtualBox installation
if command -v VBoxManage &> /dev/null; then
    echo "VirtualBox found: $(VBoxManage --version)"
else
    echo "WARNING: VirtualBox not found in PATH"
    
    # Try to find VBoxManage in common locations
    for path in "/usr/bin/VBoxManage" "/usr/local/bin/VBoxManage" "/opt/VirtualBox/VBoxManage"; do
        if [ -x "$path" ]; then
            echo "Found VBoxManage at: $path"
            export PATH="$(dirname $path):$PATH"
            echo "Added $(dirname $path) to PATH"
            break
        fi
    done
fi

# Check directory and permissions
echo "Checking file permissions..."
chmod +x consolidated_mcp_whonix.py
chmod +x virtualbox_service.py
chmod +x safe_context.py

# Start the MCP server
echo "Starting Consolidated Whonix VirtualBox MCP server..."
echo "----------------------------------------"
python consolidated_mcp_whonix.py
