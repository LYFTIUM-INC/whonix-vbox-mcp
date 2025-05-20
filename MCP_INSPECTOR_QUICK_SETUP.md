# MCP Inspector Quick Setup Guide

To set up the Whonix VirtualBox MCP module with MCP Inspector, follow these steps:

## 1. Launch MCP Inspector

First, start the MCP Inspector application you see in the screenshot.

## 2. Configure Connection Settings

Enter the following settings in the MCP Inspector interface:

- **Transport Type**: STDIO
- **Command**: python
- **Arguments**: /home/dell/coding/mcp/vbox-whonix/improved_mcp_whonix.py

## 3. Environment Variables (Optional)

Click on "Environment Variables" and add the following if needed:

```
PYTHONPATH=/home/dell/coding/mcp/vbox-whonix
PATH=/usr/bin:/usr/local/bin:/bin:/usr/sbin:/sbin:/opt/VirtualBox
```

## 4. Connect

Click the "Connect" button to establish the connection.

## 5. Available Tools

Once connected, you'll be able to use the following tools:

- **list_vms**: List all VirtualBox VMs
- **start_vm**: Start a VM (params: vm_name, headless)
- **stop_vm**: Stop a VM (params: vm_name, force)
- **reset_vm**: Reset a VM (params: vm_name)
- **get_vm_info**: Get VM details (params: vm_name)
- **create_whonix_workstation**: Create a new Whonix VM (params: name, memory_mb, disk_size_mb)
- **check_tor_connection**: Check Tor connectivity
- **execute_vm_command**: Run commands in a VM (params: vm_name, command, username, password)
- **get_vbox_version**: Get VirtualBox version
- **ensure_whonix_running**: Ensure Whonix VMs are running

## Troubleshooting

If you encounter issues:

1. Make sure VirtualBox is installed and accessible
2. Check that all Python dependencies are installed
3. Verify the correct paths in the Arguments field
4. Check the logs for specific error messages

### Common Errors and Solutions

#### TypeError: The @tool decorator was used incorrectly

This error occurs when the tool decorator is used without parentheses. In the MCP framework, you must always use `@mcp.tool()` instead of `@mcp.tool`. The fix is to add parentheses to all tool decorators in your code.

#### AttributeError: 'FastMCP' object has no attribute 'serve'

The correct method to start the server is `mcp.run()`, not `mcp.serve()`. Make sure you're using `run()` in your main function.

#### ImportError: No module named 'mcp'

This means the MCP package is not installed in your Python environment. Fix it by running:
```bash
pip install mcp-core
```

#### VBoxManage not found

This occurs when VirtualBox is not installed or not in your PATH. You can specify the correct path to VBoxManage in a config.ini file:
```ini
[virtualbox]
vboxmanage_path = /path/to/VBoxManage
```
