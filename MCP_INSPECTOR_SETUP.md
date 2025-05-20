# Setting Up Whonix VirtualBox MCP with MCP Inspector

This guide explains how to set up and run the Whonix VirtualBox MCP module using the MCP Inspector interface.

## Prerequisites

1. VirtualBox must be installed on your system
2. Python 3.7+ with pip
3. MCP Inspector installed

## Installation

1. Clone or download the Whonix VirtualBox MCP module:
   ```bash
   git clone https://github.com/yourusername/vbox-whonix.git
   cd vbox-whonix
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. Make sure all script files are executable:
   ```bash
   chmod +x improved_mcp_whonix.py
   chmod +x virtualbox_service.py
   chmod +x safe_context.py
   ```

## Running with MCP Inspector

MCP Inspector allows you to connect to MCP modules and interact with them through a graphical interface. Here's how to set it up:

### Option 1: Running the Server First

1. Start the MCP server:
   ```bash
   cd /path/to/vbox-whonix
   source venv/bin/activate
   python improved_mcp_whonix.py
   ```

2. Open MCP Inspector and configure:
   - Transport Type: STDIO
   - Command: python
   - Arguments: /path/to/vbox-whonix/improved_mcp_whonix.py
   - Click "Connect"

### Option 2: Direct Launch from MCP Inspector

1. Open MCP Inspector
2. Configure the connection:
   - Transport Type: STDIO
   - Command: python
   - Arguments: /full/path/to/vbox-whonix/improved_mcp_whonix.py
   - (Optional) Environment Variables: Click to expand and add any needed environment variables
   - Click "Connect"

## Available Tools

Once connected, you'll see the available tools in the MCP Inspector interface:

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

## Using MCP Inspector with Whonix VMs

### Example 1: List All VMs

1. Select the "list_vms" tool from the dropdown
2. Click "Execute"
3. The results will be displayed in the output panel

### Example 2: Start a VM

1. Select the "start_vm" tool from the dropdown
2. Enter parameters:
   - vm_name: "Whonix-Gateway-Xfce" (or your VM name)
   - headless: true or false
3. Click "Execute"

### Example 3: Create a New Whonix Workstation

1. Select the "create_whonix_workstation" tool
2. Enter parameters:
   - name: "My-Whonix-Workstation"
   - memory_mb: 2048
   - disk_size_mb: 20000
3. Click "Execute"

## Troubleshooting

### Common Issues

1. **"Connection refused" or "Failed to connect"**:
   - Make sure the server is running
   - Check that you're using the correct path in the Arguments field

2. **"VirtualBox not found"**:
   - Ensure VirtualBox is installed and in your PATH
   - You can specify the VBoxManage path in a config.ini file

3. **"Module not found" errors**:
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check that you're running from the correct directory

4. **"Permission denied" errors**:
   - Make sure script files are executable: `chmod +x *.py`
   - Check that you have permission to access VirtualBox

### Logs

Log files are created in the module directory to help with troubleshooting:
- `whonix_mcp.log`: Main server log file
- `server.log`: Additional server logs

## Creating a Configuration File

You can customize the module by creating a `config.ini` file in the module directory:

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

## Advanced: MCP Inspector Environment Variables

You can set necessary environment variables in MCP Inspector by clicking on "Environment Variables" and adding key-value pairs:

- `DISPLAY`: For GUI applications (e.g., `DISPLAY=:0.0`)
- `PATH`: To include the path to VBoxManage
- `PYTHONPATH`: If needed for custom module imports

These variables can help ensure the module runs correctly in the MCP Inspector environment.
