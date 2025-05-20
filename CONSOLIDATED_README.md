# Consolidated Whonix VirtualBox MCP Module

This is a completely revised and consolidated implementation of the Whonix VirtualBox MCP module that addresses the Context object issues and properly implements async handling throughout the codebase.

## Key Improvements

1. **Proper Async Context Handling**: Fixed the `Context` object handling by using an async-compatible `SafeContext` wrapper that properly awaits context methods.

2. **Consistent Parameter Order**: All tool methods now have the `ctx` parameter as the first parameter with proper defaults.

3. **Robust Error Handling**: Enhanced error handling with proper async error reporting.

4. **Simplified Structure**: Consolidated code structure that eliminates duplication and redundancy.

5. **Complete Async Implementation**: All methods are now properly async with proper `await` calls.

## Usage

### Quick Start

1. Make sure the script is executable:
   ```bash
   chmod +x consolidated_mcp_whonix.py
   ```

2. Run the server using the provided script:
   ```bash
   ./run_consolidated.sh
   ```

### MCP Inspector Setup

To use with MCP Inspector:

1. Configure the connection:
   - Transport Type: STDIO
   - Command: python
   - Arguments: /path/to/consolidated_mcp_whonix.py
   - (Optional) Environment Variables: Add any needed environment variables

2. Connect and use the available tools

## Available Tools

The module provides the following tools:

- **list_vms**: List all VirtualBox VMs
- **start_vm**: Start a VM
- **stop_vm**: Stop a VM
- **reset_vm**: Reset a VM
- **get_vm_info**: Get detailed VM information
- **create_whonix_workstation**: Create a new Whonix Workstation VM
- **check_tor_connection**: Check Tor connectivity
- **execute_vm_command**: Run commands inside a VM
- **get_vbox_version**: Get VirtualBox version info
- **ensure_whonix_running**: Ensure Whonix VMs are running
- **get_tor_status**: Get detailed Tor status
- **change_tor_circuit**: Request a new Tor circuit
- **create_snapshot**: Create a VM snapshot
- **restore_snapshot**: Restore a VM snapshot
- **list_snapshots**: List VM snapshots
- **delete_snapshot**: Delete a VM snapshot

## Configuration

The module uses the following default configuration, which can be customized by creating a `config.ini` file:

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

## Troubleshooting

If you encounter any issues:

1. Check the log file: `whonix_mcp.log`
2. Ensure VirtualBox is installed and accessible
3. Verify your VM names match the configuration
4. Check VirtualBox permissions

## Previous Issues Fixed

This implementation fixes the following issues from the original code:

1. **Context Object Error**: The `'Context' object has no attribute 'progress'` error is fixed by properly implementing the async `SafeContext` class.

2. **Async Method Calls**: All context methods are now properly awaited.

3. **Parameter Consistency**: All tool methods now have consistent parameter ordering.

4. **Error Handling**: Improved error handling and reporting.
