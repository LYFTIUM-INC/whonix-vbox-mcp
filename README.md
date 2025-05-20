# Whonix VirtualBox MCP Module

An MCP module for managing Whonix VMs in VirtualBox.

## Overview

This module provides tools for:
- Managing Whonix VMs in VirtualBox
- Checking Tor connection status
- Executing commands in Whonix VMs
- Creating and managing VM snapshots
- Automating Whonix setup and configuration

## Requirements

- **VirtualBox**: The module requires VirtualBox to be installed and accessible.
- **Whonix VMs**: Whonix Gateway and Workstation VMs must be installed in VirtualBox.
- **Python 3.7+**: Required for asyncio support.
- **MCP Framework**: This module integrates with the MCP framework.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/vbox-whonix.git
   cd vbox-whonix
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure the module (optional):
   - Create a `config.ini` file to customize VM names, paths, etc.
   - Or modify the defaults in `mcp_whonix.py`

## Configuration

The default configuration assumes:
- VBoxManage is located at `/usr/bin/VBoxManage`
- Whonix Gateway VM is named `Whonix-Gateway-Xfce`
- Whonix Workstation VM is named `Whonix-Workstation-Xfce`
- Default VM username/password: `user/changeme`

To customize these settings, create a `config.ini` file:

```ini
[virtualbox]
vboxmanage_path = /usr/bin/VBoxManage

[whonix]
gateway_vm = Whonix-Gateway-Xfce
workstation_vm = Whonix-Workstation-Xfce
default_username = user
default_password = changeme

[tor]
socks_port = 9050
control_port = 9051
```

## Usage

### Starting the MCP Server

```bash
python mcp_whonix.py
```

### Available Tools

#### System Tools

- `system_status`: Check the status of dependencies and Whonix VMs
- `get_vbox_version`: Get VirtualBox version information

#### VM Management

- `list_vms`: List all VirtualBox VMs
- `start_vm`: Start a VM
- `stop_vm`: Stop a VM
- `reset_vm`: Reset a VM
- `get_vm_info`: Get detailed VM information

#### Whonix-Specific Tools

- `create_whonix_workstation`: Create a new Whonix Workstation VM
- `check_tor_connection`: Check if Tor connection is working
- `get_tor_status`: Get detailed Tor status
- `change_tor_circuit`: Request a new Tor circuit
- `ensure_whonix_running`: Ensure both Whonix Gateway and Workstation VMs are running
- `execute_vm_command`: Execute a command inside a VM

#### Snapshot Management

- `create_snapshot`: Create a snapshot of a VM
- `restore_snapshot`: Restore a VM to a previous snapshot
- `list_snapshots`: List all snapshots for a VM
- `delete_snapshot`: Delete a snapshot

## Error Handling

The module includes robust error handling and dependency checking:
- Automatic verification of VirtualBox installation
- VM existence and state checks
- Graceful handling of missing context attributes
- Detailed error reporting with suggestions

## Troubleshooting

If you encounter issues:

1. **VirtualBox Not Found**:
   - Ensure VirtualBox is installed
   - Check that the VBoxManage path is correct in your configuration

2. **Whonix VMs Not Found**:
   - Verify Whonix VMs are installed in VirtualBox
   - Check that VM names match your configuration

3. **Command Execution Errors**:
   - Verify VM credentials in your configuration
   - Check that the VM is running

4. **Tor Connection Issues**:
   - Ensure Tor is running in the Whonix Gateway
   - Check network connectivity in the VM

## License

This project is licensed under the MIT License - see the LICENSE file for details.
