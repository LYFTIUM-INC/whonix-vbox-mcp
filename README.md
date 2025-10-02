# VirtualBox Whonix MCP Server

**Production-ready MCP server for managing Whonix VMs with browser automation through Tor.**

[![Version](https://img.shields.io/badge/version-0.7.0-blue.svg)](https://github.com/PreistlyPython/whonix-vbox-mcp)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Features

🔐 **Privacy-First Browser Automation**
- Intelligent search through anonymous engines (DuckDuckGo, SearX)
- Screenshot capture through Tor network
- Custom automation tasks with natural language
- Bulk operations with content truncation

🖥️ **VM Management**
- Start, stop, and reset Whonix VMs
- Snapshot management (create, restore, delete)
- VM state monitoring and control

🔒 **Secure File Transfer**
- Upload/download files with hash verification
- Chunked transfer for large files
- Directory listing and management

🌐 **Tor Integration**
- Connection monitoring and circuit changes
- Tor status reporting
- Automated Whonix VM orchestration

## Quick Start

### Prerequisites

- **VirtualBox** 7.0+ installed
- **Whonix VMs** (Gateway & Workstation) set up in VirtualBox
- **Python** 3.8+
- **Claude Desktop** or MCP-compatible client

### Installation

```bash
# Clone repository
git clone https://github.com/PreistlyPython/whonix-vbox-mcp.git
cd whonix-vbox-mcp

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env to set WHONIX_VM_PASSWORD
```

### Setup MCP

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on Mac):

```json
{
  "mcpServers": {
    "vbox-whonix": {
      "command": "python3",
      "args": ["/path/to/vbox-whonix/consolidated_mcp_whonix_with_file_transfer.py"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      }
    }
  }
}
```

Or use the included `.mcp.json`:
```bash
# Copy to Claude Desktop config location
cp .mcp.json ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

## MCP Tools (28 Available)

### 🌐 Browser Automation (5 tools)

| Tool | Description | Example Use |
|------|-------------|-------------|
| `browser_automation_status_check` | Check all browser components | System health monitoring |
| `browser_intelligent_search` | Search via DuckDuckGo/SearX | `"privacy news 2025"` |
| `browser_capture_page_screenshot` | Capture webpage through Tor | `https://example.onion` |
| `browser_bulk_screenshot_capture` | Capture multiple URLs | Batch website monitoring |
| `browser_custom_automation_task` | Execute custom tasks | `"extract headings"` |

### 🖥️ VM Management (6 tools)

- `list_vms` - List all VirtualBox VMs
- `get_vm_info` - Get detailed VM information
- `start_vm` - Start a VM (headless mode supported)
- `stop_vm` - Stop a VM (ACPI or force)
- `reset_vm` - Hard reset a VM
- `get_vbox_version` - Get VirtualBox version

### 🔐 Whonix & Tor (4 tools)

- `ensure_whonix_running` - Start both Gateway & Workstation
- `check_tor_connection` - Verify Tor connectivity
- `get_tor_status` - Detailed Tor service status
- `change_tor_circuit` - Request new Tor circuit

### 📸 Snapshots (4 tools)

- `create_snapshot` - Create VM snapshot with description
- `restore_snapshot` - Restore VM to snapshot
- `list_snapshots` - List all VM snapshots
- `delete_snapshot` - Delete a snapshot

### 📁 File Transfer (3 tools)

- `upload_file_to_vm` - Upload with hash verification
- `download_file_from_vm` - Download with hash verification
- `list_vm_directory` - List VM directory contents

### 🛠️ VM State (4 tools)

- `get_vm_state` - Detailed state including locks
- `resume_vm` - Resume paused VM
- `unlock_vm` - Unlock stuck VM session
- `discard_saved_state` - Discard saved state

### 🏗️ Whonix Management (2 tools)

- `create_whonix_workstation` - Create new Workstation VM
- `execute_vm_command` - Execute commands in VM

## Usage Examples

### Search Privately

```python
# Through MCP client (Claude Desktop)
Use browser_intelligent_search:
- Query: "cybersecurity tools 2025"
- Engine: duckduckgo
```

### Capture Dark Web Screenshot

```python
Use browser_capture_page_screenshot:
- URL: "https://www.torproject.org"
- Filename prefix: "tor_homepage"
```

### Manage VMs

```bash
# Start Whonix VMs
ensure_whonix_running()

# Create snapshot before testing
create_snapshot(vm_name="Whonix-Workstation-Xfce",
                snapshot_name="before_testing")

# Execute command
execute_vm_command(vm_name="Whonix-Workstation-Xfce",
                   command="apt update")
```

### Secure File Transfer

```python
# Upload file to VM
upload_file_to_vm(
    file_path="/local/path/script.py",
    vm_name="Whonix-Workstation-Xfce",
    vm_destination="/home/user/script.py"
)

# Verify with hash
download_file_from_vm(
    vm_path="/home/user/script.py",
    vm_name="Whonix-Workstation-Xfce",
    local_destination="/local/verify/script.py"
)
```

## Configuration

### Environment Variables (.env)

```bash
# VM Credentials
WHONIX_VM_PASSWORD=changeme

# VirtualBox Path (optional)
VBOXMANAGE_PATH=/usr/bin/VBoxManage
```

### Config File (config.ini) - Optional

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

## Architecture

```
vbox-whonix/
├── consolidated_mcp_whonix_with_file_transfer.py  # Main MCP server (v0.7.0)
├── browser_automation.py                           # Browser automation API
├── custom_automation_executor.py                   # Custom task execution
├── multi_engine_search.py                          # Multi-search engine support
├── file_transfer_service.py                        # Secure file transfer
├── virtualbox_service.py                           # VirtualBox operations
├── safe_context.py                                 # MCP context handling
├── config_loader.py                                # Configuration management
├── requirements.txt                                # Python dependencies
└── .env.example                                    # Environment template
```

## Troubleshooting

**VMs won't start**
```bash
# Check VirtualBox installation
VBoxManage --version

# Verify VM names
VBoxManage list vms

# Check for KVM conflicts (Linux)
sudo modprobe -r kvm_intel kvm
```

**Tor connection fails**
```bash
# Check Tor status
get_tor_status()

# Request new circuit
change_tor_circuit()

# Ensure Gateway is running
ensure_whonix_running()
```

**File transfer fails**
- Ensure VM is running and guest additions installed
- Check credentials in .env or config.ini
- Verify file paths are absolute

## Development

### Running Tests

```bash
# Test VM operations
python -m pytest tests/

# Test browser automation
python -c "from browser_automation import BrowserAPIv2; api = BrowserAPIv2(); print(api.status())"
```

### Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Credits

- Built on [MCP Framework](https://modelcontextprotocol.io)
- Whonix VMs by [Whonix Project](https://www.whonix.org)
- VirtualBox by [Oracle](https://www.virtualbox.org)

## Support

- **Issues**: [GitHub Issues](https://github.com/PreistlyPython/whonix-vbox-mcp/issues)
- **Documentation**: [Wiki](https://github.com/PreistlyPython/whonix-vbox-mcp/wiki)
- **Whonix Help**: [Whonix Forums](https://forums.whonix.org)

---

**Version 0.7.0** | Made with ❤️ for privacy enthusiasts
