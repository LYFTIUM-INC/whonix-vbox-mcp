# Whonix VirtualBox MCP - Setup Guide

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)

A fully functional, stable MCP (Model Context Protocol) module for managing Whonix VMs in VirtualBox with comprehensive cross-platform support.

## Overview

This MCP module provides:
- **VirtualBox Management**: Start, stop, create, and manage VMs
- **Whonix Integration**: Specialized tools for Whonix Gateway and Workstation VMs
- **Tor Control**: Check Tor status, change circuits, and monitor connectivity
- **Snapshot Management**: Create, restore, list, and delete VM snapshots
- **Cross-platform Support**: Works on macOS, Windows, and Linux

## Prerequisites

### 1. System Requirements

- **Python 3.7 or higher**
- **VirtualBox 6.0 or higher**
- **Whonix VMs** (Gateway and Workstation)
- **Git** (for installation and updates)

### 2. VirtualBox Installation

#### macOS
```bash
# Option 1: Download from VirtualBox website
# https://www.virtualbox.org/wiki/Downloads

# Option 2: Using Homebrew
brew install --cask virtualbox
```

#### Windows
1. Download VirtualBox from: https://www.virtualbox.org/wiki/Downloads
2. Run the installer as Administrator
3. Ensure VirtualBox is added to your PATH

#### Ubuntu/Debian
```bash
# Update package lists
sudo apt update

# Install VirtualBox
sudo apt install virtualbox virtualbox-ext-pack

# Add your user to the vboxusers group
sudo usermod -a -G vboxusers $USER

# Log out and back in for group changes to take effect
```

#### CentOS/RHEL/Fedora
```bash
# Enable VirtualBox repository
sudo dnf install -y wget
wget -q https://www.virtualbox.org/download/oracle_vbox.asc -O- | sudo rpm --import -

# Install VirtualBox
sudo dnf install VirtualBox-7.0

# Add your user to the vboxusers group
sudo usermod -a -G vboxusers $USER
```

### 3. Whonix Installation

Download and import Whonix VMs:

1. Visit [Whonix Downloads](https://www.whonix.org/wiki/Download)
2. Download both Whonix Gateway and Workstation OVA files
3. Import them into VirtualBox:
   ```bash
   # Import Whonix Gateway
   VBoxManage import Whonix-Gateway-*.ova
   
   # Import Whonix Workstation
   VBoxManage import Whonix-Workstation-*.ova
   ```

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/whonix-vbox-mcp.git
cd whonix-vbox-mcp
```

### 2. Platform-Specific Setup

#### macOS Setup

```bash
# Install Python dependencies
python3 -m pip install --upgrade pip

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Configure VBoxManage path (if needed)
echo 'export PATH="/Applications/VirtualBox.app/Contents/MacOS:$PATH"' >> ~/.bash_profile
source ~/.bash_profile
```

#### Windows Setup

```powershell
# Open PowerShell as Administrator

# Install Python dependencies
python -m pip install --upgrade pip

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install requirements
pip install -r requirements.txt

# Add VirtualBox to PATH (if not already done)
# Add "C:\Program Files\Oracle\VirtualBox" to your system PATH
```

#### Ubuntu/Linux Setup

```bash
# Install Python and pip if needed
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Ensure VBoxManage is in PATH
which VBoxManage
# If not found, add to PATH or create symlink:
# sudo ln -s /usr/bin/VBoxManage /usr/local/bin/VBoxManage
```

## Configuration

### 1. Basic Configuration

The MCP module uses sensible defaults but can be customized:

Create a `config.ini` file in the project root:

```ini
[virtualbox]
vboxmanage_path = /usr/bin/VBoxManage  # or C:\Program Files\Oracle\VirtualBox\VBoxManage.exe on Windows

[whonix]
gateway_vm = Whonix-Gateway-Xfce
workstation_vm = Whonix-Workstation-Xfce
default_username = user
default_password = changeme

[tor]
socks_port = 9050
control_port = 9051
```

### 2. Path Configuration by Platform

#### macOS Paths
```ini
[virtualbox]
vboxmanage_path = /Applications/VirtualBox.app/Contents/MacOS/VBoxManage
```

#### Windows Paths
```ini
[virtualbox]
vboxmanage_path = C:\Program Files\Oracle\VirtualBox\VBoxManage.exe
```

#### Linux Paths
```ini
[virtualbox]
vboxmanage_path = /usr/bin/VBoxManage
```

## Running the MCP Server

### 1. Manual Start

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the MCP server
python consolidated_mcp_whonix.py
```

### 2. Using the Start Script

```bash
# Make the script executable (Linux/macOS)
chmod +x start_mcp.sh

# Run the script
./start_mcp.sh
```

### 3. Windows Batch File

Create `start_mcp.bat`:
```batch
@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python consolidated_mcp_whonix.py
pause
```

## Testing the Installation

### 1. Quick Test

```bash
# Activate environment
source venv/bin/activate

# Test VirtualBox connection
python -c "
from virtualbox_service import VirtualBoxService
import asyncio

async def test():
    service = VirtualBoxService()
    result = await service.run_command(['--version'])
    print(f'VirtualBox test: {result}')

asyncio.run(test())
"
```

### 2. Full Integration Test

```bash
# Run the built-in test
python -c "
import asyncio
from consolidated_mcp_whonix import check_virtualbox_installed, list_vms

async def test():
    print('Testing VirtualBox...')
    if await check_virtualbox_installed():
        print('✓ VirtualBox is working')
        vms = await list_vms()
        print(f'Found VMs: {vms}')
    else:
        print('✗ VirtualBox test failed')

asyncio.run(test())
"
```

## Claude Desktop Integration

### 1. Locate Claude Desktop Configuration

#### macOS
```bash
~/Library/Application Support/Claude/claude_desktop_config.json
```

#### Windows
```bash
%APPDATA%\Claude\claude_desktop_config.json
```

#### Linux
```bash
~/.config/Claude/claude_desktop_config.json
```

### 2. Add MCP Configuration

Add this to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "whonix-vbox": {
      "command": "python",
      "args": ["/path/to/whonix-vbox-mcp/consolidated_mcp_whonix.py"],
      "env": {
        "PATH": "/path/to/whonix-vbox-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin"
      }
    }
  }
}
```

### 3. Platform-Specific Configurations

#### macOS Configuration
```json
{
  "mcpServers": {
    "whonix-vbox": {
      "command": "/usr/bin/python3",
      "args": ["/Users/username/whonix-vbox-mcp/consolidated_mcp_whonix.py"],
      "env": {
        "PATH": "/Users/username/whonix-vbox-mcp/venv/bin:/usr/local/bin:/usr/bin:/bin:/Applications/VirtualBox.app/Contents/MacOS"
      }
    }
  }
}
```

#### Windows Configuration
```json
{
  "mcpServers": {
    "whonix-vbox": {
      "command": "C:\\Users\\username\\whonix-vbox-mcp\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\username\\whonix-vbox-mcp\\consolidated_mcp_whonix.py"],
      "env": {
        "PATH": "C:\\Program Files\\Oracle\\VirtualBox;C:\\Windows\\System32;C:\\Windows"
      }
    }
  }
}
```

## Security Considerations

### 1. Access Controls

- **VM Credentials**: Change default Whonix passwords
- **File Permissions**: Ensure config files are not world-readable
- **Network Isolation**: Whonix VMs should use internal networking

### 2. Secure Configuration

```bash
# Set proper permissions on config files
chmod 600 config.ini

# Create a dedicated user for MCP operations (optional)
sudo useradd -r -s /bin/false mcp-whonix
```

### 3. Tor Security

- Always use Whonix for Tor operations
- Never bypass Whonix's built-in security features
- Regularly update Whonix VMs

## Troubleshooting

### Common Issues

#### 1. VirtualBox Not Found
```bash
# Check if VBoxManage is accessible
which VBoxManage
# or
VBoxManage --version
```

**Solution**: Add VirtualBox to your PATH or update the config file.

#### 2. Permission Denied
```bash
# Add user to vboxusers group (Linux)
sudo usermod -a -G vboxusers $USER
```

**Solution**: Log out and back in for group changes to take effect.

#### 3. Python Module Import Errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

#### 4. Whonix VMs Not Starting
```bash
# Check VM status
VBoxManage showvminfo "Whonix-Gateway-Xfce" | grep State
```

**Solution**: Ensure sufficient system resources and no conflicting applications.

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export MCP_DEBUG=true

# Or modify the script directly
python consolidated_mcp_whonix.py --debug
```

### Log Files

Check these log files for errors:
- `whonix_mcp.log` - Main application log
- `server.log` - MCP server log
- `vbox_whonix_server.log` - VirtualBox operations log

## Available MCP Tools

The following tools are available when the MCP server is running:

### VM Management
- `list_vms` - List all VirtualBox VMs
- `start_vm` - Start a VM
- `stop_vm` - Stop a VM
- `reset_vm` - Reset a VM
- `get_vm_info` - Get detailed VM information

### Whonix-Specific
- `create_whonix_workstation` - Create a new Whonix Workstation VM
- `ensure_whonix_running` - Ensure both Gateway and Workstation are running
- `execute_vm_command` - Execute commands inside VMs

### Tor Management
- `check_tor_connection` - Check if Tor is working
- `get_tor_status` - Get detailed Tor status
- `change_tor_circuit` - Request a new Tor circuit

### Snapshot Management
- `create_snapshot` - Create a VM snapshot
- `restore_snapshot` - Restore to a previous snapshot
- `list_snapshots` - List all snapshots
- `delete_snapshot` - Delete a snapshot

### System Information
- `get_vbox_version` - Get VirtualBox version information

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/whonix-vbox-mcp.git
cd whonix-vbox-mcp

# Create development environment
python3 -m venv dev-venv
source dev-venv/bin/activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8 mypy

# Run tests
pytest

# Format code
black .

# Type checking
mypy .
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run code formatting and linting
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/yourusername/whonix-vbox-mcp/issues)
- **Discussions**: [Community discussions](https://github.com/yourusername/whonix-vbox-mcp/discussions)
- **Wiki**: [Additional documentation](https://github.com/yourusername/whonix-vbox-mcp/wiki)

## Acknowledgments

- [Whonix Project](https://www.whonix.org/) for the anonymous operating system
- [VirtualBox](https://www.virtualbox.org/) for the virtualization platform
- [MCP Protocol](https://modelcontextprotocol.io/) for the communication standard
- [FastMCP](https://github.com/jlowin/fastmcp) for the Python MCP framework

---

**Status**: Fully Functional Stable MCP ✅

Last Updated: May 19, 2025
Version: 0.4.0
