#!/usr/bin/env python3

"""
Consolidated Whonix VirtualBox MCP Module with Enhanced Web Automation
---------------------------------------------------------------------
This module provides comprehensive tools for managing Whonix VMs in VirtualBox through MCP.
Includes advanced web automation, browser control, and security tools.

Version 0.6.0 - Added Enhanced Web Automation Capabilities:
- JavaScript execution in isolated browser environments
- Screenshot capture and visual automation
- Intelligent form filling and DOM interaction
- Session management for complex web workflows
- AI-assisted content extraction and analysis
"""

import asyncio
import os
import sys
import logging
import json
import time
import base64
import re
import shlex
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from mcp.server.fastmcp import FastMCP, Context

# Set up logging FIRST before any usage
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("whonix_mcp.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import our services
from virtualbox_service import VirtualBoxService
from safe_context import SafeContext
from file_transfer_service import FileTransferService

# Import enhanced web automation services
try:
    from enhanced_web_automation_mcp import EnhancedWebAutomationService
    from advanced_form_automation_mcp import AdvancedFormAutomationService
    WEB_AUTOMATION_AVAILABLE = True
    logger.info("Web automation services loaded successfully")
except ImportError as e:
    logger.warning(f"Web automation services not available: {e}")
    WEB_AUTOMATION_AVAILABLE = False

# Define version
VERSION = "0.6.0"  # Added Enhanced Web Automation capabilities

# Initialize FastMCP server
mcp = FastMCP("vbox-whonix", version=VERSION)

# Load configuration
CONFIG = {
    "virtualbox": {
        "vboxmanage_path": "/usr/bin/VBoxManage"
    },
    "whonix": {
        "gateway_vm": "Whonix-Gateway-Xfce",
        "workstation_vm": "Whonix-Workstation-Xfce",
        "default_username": "user",
        "default_password": os.getenv("WHONIX_VM_PASSWORD", "")
    },
    "tor": {
        "socks_port": 9050,
        "control_port": 9051
    }
}

# Try to import user config
try:
    from config_loader import ConfigLoader
    config_loader = ConfigLoader()
    
    # Update configuration with user settings
    for section in CONFIG:
        for key in CONFIG[section]:
            CONFIG[section][key] = config_loader.get(
                section, key, CONFIG[section][key])
    
    logger.info("Loaded configuration from config_loader")
except ImportError:
    logger.warning("No config_loader.py found, using defaults")
except Exception as e:
    logger.error(f"Failed to load configuration: {e}")

# Initialize the VirtualBox service
vbox_service = VirtualBoxService(CONFIG["virtualbox"]["vboxmanage_path"])

# Initialize the file transfer service
file_transfer_service = FileTransferService(vbox_service)

# Helper function to clean VBoxManage output
def clean_vbox_output(raw_output):
    """Remove verbose VBoxManage output and extract just the command result"""
    if not raw_output:
        return ""
    
    # Try to extract just JSON if present
    json_match = re.search(r'\{[\s\S]*\}', raw_output)
    if json_match:
        return json_match.group(0)
    
    # Otherwise return the cleaned output without VBox noise
    lines = raw_output.split('\n')
    cleaned = []
    
    for line in lines:
        # Skip VBoxManage verbose output
        if any(skip in line for skip in [
            "Wait result", "Executing:", "Creating guest session",
            "Starting guest process", "Process terminated",
            "Exit code=", "Closing guest session", "Successfully started",
            "arg[", "Image :", "[GFX"
        ]):
            continue
        
        # Keep actual output lines
        if line.strip():
            cleaned.append(line)
    
    return '\n'.join(cleaned).strip()

# Initialize enhanced web automation services
if WEB_AUTOMATION_AVAILABLE:
    web_automation_service = EnhancedWebAutomationService()
    form_automation_service = AdvancedFormAutomationService()
    logger.info("Enhanced web automation services initialized")
else:
    web_automation_service = None
    form_automation_service = None
    logger.warning("Enhanced web automation services not available")

# Helper function to check if VirtualBox is installed
async def check_virtualbox_installed(ctx=None) -> bool:
    """
    Check if VirtualBox is installed and accessible.
    
    Args:
        ctx: MCP context for reporting progress
        
    Returns:
        bool: True if VirtualBox is installed, False otherwise
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VBoxManage exists
    if not os.path.exists(vbox_service.vboxmanage_path):
        await safe_ctx.error(f"VBoxManage not found at {vbox_service.vboxmanage_path}")
        return False
    
    # Try to get VirtualBox version
    result = await vbox_service.run_command(["--version"], ctx)
    
    if not result["success"]:
        await safe_ctx.error("Failed to get VirtualBox version")
        return False
    
    return True


# MCP Tool: List all VirtualBox VMs
@mcp.tool()
async def list_vms(ctx: Context = None) -> str:
    """
    List all VirtualBox VMs installed on the system.
    
    Returns:
        A formatted list of all VMs with their properties.
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info("Listing VirtualBox VMs...")
    
    # Get list of VMs
    vms = await vbox_service.get_vm_list(ctx)
    
    if not vms:
        return "No VirtualBox VMs found."
    
    # Format output
    output = "VirtualBox Virtual Machines:\n" + "=" * 30 + "\n\n"
    
    for vm in vms:
        output += f"VM: {vm['name']}\n"
        output += f"UUID: {vm.get('uuid', 'Unknown')}\n"
        output += f"State: {vm.get('VMState', 'Unknown')}\n"
        output += f"RAM: {vm.get('memory', 'Unknown')} MB\n"
        output += f"OS Type: {vm.get('ostype', 'Unknown')}\n\n"
    
    return output


# MCP Tool: Start a VirtualBox VM
@mcp.tool()
async def start_vm(ctx: Context = None, vm_name: str = "", headless: bool = True) -> str:
    """
    Start a VirtualBox VM.
    
    Args:
        vm_name: Name of the VM to start
        headless: Whether to start the VM in headless mode (default: True)
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Starting VM: {vm_name}")
    
    # Start the VM
    result = await vbox_service.start_vm(vm_name, headless, ctx)
    
    if result["success"]:
        return f"Successfully started VM: {vm_name}"
    else:
        error_msg = result.get("error", result.get("stderr", "Unknown error"))
        return f"Failed to start VM: {vm_name}. Error: {error_msg}"


# MCP Tool: Stop a VirtualBox VM
@mcp.tool()
async def stop_vm(ctx: Context = None, vm_name: str = "", force: bool = False) -> str:
    """
    Stop a VirtualBox VM.
    
    Args:
        vm_name: Name of the VM to stop
        force: Whether to force power off instead of ACPI shutdown (default: False)
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Stopping VM: {vm_name}")
    
    # Stop the VM
    result = await vbox_service.stop_vm(vm_name, force, ctx)
    
    if result["success"]:
        if "message" in result:
            return result["message"]
        return f"Successfully {'powered off' if force else 'sent shutdown signal to'} VM: {vm_name}"
    else:
        error_msg = result.get("error", result.get("stderr", "Unknown error"))
        return f"Failed to stop VM: {vm_name}. Error: {error_msg}"


# MCP Tool: Reset a VirtualBox VM
@mcp.tool()
async def reset_vm(ctx: Context = None, vm_name: str = "") -> str:
    """
    Reset a VirtualBox VM (hard reset).
    
    Args:
        vm_name: Name of the VM to reset
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Resetting VM: {vm_name}")
    
    # Reset the VM
    result = await vbox_service.run_command(["controlvm", vm_name, "reset"], ctx)
    
    if result["success"]:
        return f"Successfully reset VM: {vm_name}"
    else:
        error_msg = result.get("error", result.get("stderr", "Unknown error"))
        return f"Failed to reset VM: {vm_name}. Error: {error_msg}"

# MCP Tool: Get detailed VM information
@mcp.tool()
async def get_vm_info(ctx: Context = None, vm_name: str = "") -> str:
    """
    Get detailed information about a VM.
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        Detailed VM information
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Getting info for VM: {vm_name}")
    
    # Get VM info
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM not found: {vm_name}"
    
    # Format output
    output = f"Information for VM: {vm_name}\n" + "=" * 30 + "\n\n"
    
    # Organize output by categories
    categories = {
        "General": ["name", "UUID", "ostype", "VMState", "cpus", "memory"],
        "Storage": ["SATA", "IDE", "SCSI", "hardwareuuid"],
        "Network": ["macaddress1", "macaddress2", "nic1", "nic2", "intnet1", "intnet2"],
        "Other": []  # Will contain all other keys
    }
    
    # Group properties by category
    categorized_properties = {cat: [] for cat in categories}
    
    for key, value in vm_info.items():
        assigned = False
        for cat, props in categories.items():
            if key in props or any(key.startswith(prop) for prop in props):
                categorized_properties[cat].append((key, value))
                assigned = True
                break
        
        if not assigned and key != "is_running":  # Skip our custom property
            categorized_properties["Other"].append((key, value))
    
    # Format by category
    for cat, props in categorized_properties.items():
        if props:
            output += f"{cat}:\n"
            for key, value in sorted(props):
                output += f"  {key}: {value}\n"
            output += "\n"
    
    return output


# MCP Tool: Create a new Whonix Workstation VM
@mcp.tool()
async def create_whonix_workstation(ctx: Context = None, name: str = "", memory_mb: int = 2048, disk_size_mb: int = 20000) -> str:
    """
    Create a new Whonix Workstation VM based on the Whonix template.
    
    Args:
        name: Name for the new VM
        memory_mb: RAM in MB (default: 2048)
        disk_size_mb: Disk size in MB (default: 20000)
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Creating new Whonix Workstation VM: {name}")
    
    # Check if a VM with this name already exists
    existing_vms = await vbox_service.get_vm_list(ctx)
    for vm in existing_vms:
        if vm["name"] == name:
            await safe_ctx.error(f"VM with name '{name}' already exists")
            return f"VM with name '{name}' already exists. Please choose a different name."
    
    # Check if Whonix template VM exists
    template_found = False
    template_name = ""
    for vm in existing_vms:
        if "Whonix-Workstation" in vm["name"]:
            template_found = True
            template_name = vm["name"]
            template_vm = vm
            break
    
    if not template_found:
        return f"Whonix Workstation template VM not found. Please ensure you have installed Whonix first."
    
    # Check if template VM is running or in saved state, if so we need to stop it first
    if template_vm.get("VMState") in ["running", "saved"]:
        await safe_ctx.info(f"Template VM is {template_vm.get('VMState')}. Powering off before cloning.")
        
        # Force power off to ensure clean state for cloning
        stop_result = await vbox_service.stop_vm(template_name, force=True, ctx=ctx)
        
        if not stop_result["success"]:
            error_msg = stop_result.get("stderr", stop_result.get("error", "Unknown error"))
            return f"Failed to power off template VM: {error_msg}"
        
        # Wait for the VM to fully stop
        await asyncio.sleep(5)
        
        # Check that it's really powered off
        template_info = await vbox_service.get_vm_info(template_name, ctx)
        if template_info.get("VMState") != "poweroff":
            return f"Failed to power off template VM completely. Please try again or stop it manually."
    
    # Try to unlock media before cloning (to resolve common issues)
    await safe_ctx.info("Attempting to unlock any locked media...")
    await vbox_service.run_command(["mediaunregister", "--type", "dvd"], ctx)
    await vbox_service.run_command(["mediaunregister", "--type", "disk"], ctx)
    
    await safe_ctx.progress("Creating VM...", 10)
    
    # Try using linked clones (faster and uses less disk space)
    await safe_ctx.info("Attempting to create a linked clone...")
    clone_result = await vbox_service.run_command([
        "clonevm", template_name,
        "--name", name,
        "--register",
        "--mode", "machine",
        "--options", "link"
    ], ctx)
    
    # If linked clone fails, try regular clone
    if not clone_result["success"]:
        await safe_ctx.info("Linked clone failed, trying full clone...")
        clone_result = await vbox_service.run_command([
            "clonevm", template_name,
            "--name", name,
            "--register"
        ], ctx)
    
    # If both clone methods fail, try export/import
    if not clone_result["success"]:
        await safe_ctx.info("Clone methods failed. Trying alternative method: Export/Import...")
        
        # Export to OVA
        temp_ova = f"/tmp/{template_name}.ova"
        export_result = await vbox_service.run_command([
            "export", template_name,
            "--output", temp_ova
        ], ctx)
        
        if not export_result["success"]:
            error_msg = clone_result.get("stderr", clone_result.get("error", "Unknown error"))
            diagnostic = vbox_service.get_error_diagnostics(error_msg)
            if diagnostic:
                return f"Failed to clone VM via both methods. Error: {error_msg}\n\nDiagnostic: {diagnostic}"
            else:
                return f"Failed to clone VM via both methods. Error: {error_msg}"
        
        # Import with new name
        import_result = await vbox_service.run_command([
            "import", temp_ova,
            "--vsys", "0", 
            "--vmname", name
        ], ctx)
        
        # Clean up
        try:
            os.remove(temp_ova)
        except Exception as e:
            await safe_ctx.warning(f"Failed to remove temporary OVA file: {e}")
            
        if not import_result["success"]:
            error_msg = import_result.get("stderr", import_result.get("error", "Unknown error"))
            return f"Failed to import VM: {error_msg}"
    
    await safe_ctx.progress("Configuring VM settings...", 50)
    
    # Configure memory
    memory_result = await vbox_service.run_command(["modifyvm", name, "--memory", str(memory_mb)], ctx)
    if not memory_result["success"]:
        await safe_ctx.warning(f"Failed to set memory to {memory_mb}MB. Using default.")
    
    # Configure networking for Whonix
    nic_result = await vbox_service.run_command(["modifyvm", name, "--nic1", "intnet"], ctx)
    if not nic_result["success"]:
        await safe_ctx.warning("Failed to configure network adapter. Check VM settings manually.")
    
    intnet_result = await vbox_service.run_command(["modifyvm", name, "--intnet1", "Whonix"], ctx)
    if not intnet_result["success"]:
        await safe_ctx.warning("Failed to configure internal network. Check VM settings manually.")
    
    await safe_ctx.progress("VM created successfully", 100)
    
    return f"Successfully created Whonix Workstation VM: {name}"

# MCP Tool: Check if Tor connection is working
@mcp.tool()
async def check_tor_connection(ctx: Context = None) -> str:
    """
    Check if Tor connection is working properly.
    
    Returns:
        Status of the Tor connection
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info("Checking Tor connection...")
    
    # Check if Whonix Gateway is running
    gateway_vm = CONFIG["whonix"]["gateway_vm"]
    gateway_info = await vbox_service.get_vm_info(gateway_vm, ctx)
    
    if not gateway_info:
        return f"Whonix Gateway VM '{gateway_vm}' not found. Please ensure it is installed."
    
    if not gateway_info.get("is_running", False):
        return f"Whonix Gateway VM '{gateway_vm}' is not running. Please start it first."
    
    # Try to execute command to check Tor status in the Gateway VM
    cmd = [
        "guestcontrol", gateway_vm, 
        "run", "--username", CONFIG["whonix"]["default_username"], 
        "--password", CONFIG["whonix"]["default_password"],
        "--", "/usr/bin/timeout", "5", "/usr/bin/systemctl", "is-active", "tor"
    ]
    
    result = await vbox_service.run_command(cmd, ctx)
    
    if result["success"] and "active" in result.get("stdout", ""):
        await safe_ctx.info("Tor service is active")
        
        # Try to check actual connectivity
        check_cmd = [
            "guestcontrol", gateway_vm, 
            "run", "--username", CONFIG["whonix"]["default_username"], 
            "--password", CONFIG["whonix"]["default_password"],
            "--", "/usr/bin/curl", "--socks5", "127.0.0.1:9050", 
            "--connect-timeout", "10", "https://check.torproject.org/"
        ]
        
        check_result = await vbox_service.run_command(check_cmd, ctx)
        
        if check_result["success"] and "Congratulations" in check_result.get("stdout", ""):
            return "Tor connection is working properly! You are connected to the Tor network."
        else:
            return "Tor service is running but connection check failed. The VM might not have internet connectivity."
    else:
        return "Tor service is not active in the Whonix Gateway. Please check the Gateway configuration."


# MCP Tool: Execute a command inside a VM
@mcp.tool()
async def execute_vm_command(ctx: Context = None, vm_name: str = "", command: str = "", 
                           username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Execute a command inside a running VM.
    
    Args:
        vm_name: Name of the VM
        command: Command to execute
        username: Username for guest credentials (default: from config)
        password: Password for guest credentials (default: from config)
    
    Returns:
        Command execution result
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Executing command in VM '{vm_name}': {command}")
    
    # Use default credentials if not provided
    if username is None:
        username = CONFIG["whonix"]["default_username"]
    if password is None:
        password = CONFIG["whonix"]["default_password"]
    
    # Check if VM is running
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    if not vm_info.get("is_running", False):
        return f"VM '{vm_name}' is not running. Please start it first."
    
    # Check if Guest Additions are installed and running
    guest_additions_running = vm_info.get("GuestAdditionsRunLevel", "0") != "0"
    if not guest_additions_running:
        return f"Guest Additions are not running in VM '{vm_name}'. Please install and enable Guest Additions."
    
    # Dictionary of common commands and their full paths
    common_paths = {
        "systemctl": "/bin/systemctl",
        "ls": "/bin/ls",
        "cat": "/bin/cat",
        "grep": "/bin/grep",
        "ps": "/bin/ps",
        "cd": "/bin/cd",
        "pwd": "/bin/pwd",
        "mkdir": "/bin/mkdir",
        "rm": "/bin/rm",
        "cp": "/bin/cp",
        "mv": "/bin/mv",
        "bash": "/bin/bash",
        "sudo": "/usr/bin/sudo",
        "curl": "/usr/bin/curl",
        "wget": "/usr/bin/wget"
    }
    
    # Split the command into parts and replace with full paths for common commands
    cmd_parts = command.split()
    if cmd_parts and cmd_parts[0] in common_paths:
        cmd_parts[0] = common_paths[cmd_parts[0]]
    
    # If command still doesn't contain a path (no /) and isn't empty, try to use bash
    if cmd_parts and "/" not in cmd_parts[0]:
        # Use a bash wrapper for commands without full paths
        cmd_parts = ["/bin/bash", "-c", command]
    
    # Build the guestcontrol command
    guest_cmd = [
        "guestcontrol", vm_name, 
        "run", "--username", username, 
        "--password", password,
        # Removed --verbose to reduce output size
        "--"
    ] + cmd_parts
    
    result = await vbox_service.run_command(guest_cmd, ctx)
    
    if result["success"]:
        output = result.get("stdout", "").strip()
        # Clean the output to reduce token usage
        cleaned_output = clean_vbox_output(output)
        return cleaned_output if cleaned_output else "Command executed successfully"
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        
        # Provide helpful troubleshooting info for common errors
        if "No such file or directory" in error_msg:
            return (f"Failed to execute command. The specified command or executable was not found in the VM.\n\n"
                   f"Error: {error_msg}\n\n"
                   f"Try specifying the full path to the command executable.")
        elif "authentication" in error_msg.lower() or "password" in error_msg.lower():
            return (f"Failed to execute command due to authentication issues.\n\n"
                   f"Error: {error_msg}\n\n"
                   f"Try a command that doesn't require sudo privileges.")
        else:
            # Include any diagnostics from the VirtualBoxService
            diagnostics = result.get("diagnostics", "")
            if diagnostics:
                return f"Failed to execute command. Error: {error_msg}\n\nDiagnostics: {diagnostics}"
            else:    
                return f"Failed to execute command. Error: {error_msg}"

# MCP Tool: Get VirtualBox version
@mcp.tool()
async def get_vbox_version(ctx: Context = None) -> str:
    """
    Get VirtualBox version information.
    
    Returns:
        VirtualBox version details
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not os.path.exists(vbox_service.vboxmanage_path):
        return f"VBoxManage not found at {vbox_service.vboxmanage_path}"
    
    await safe_ctx.info("Getting VirtualBox version...")
    
    # Get version
    result = await vbox_service.run_command(["--version"], ctx)
    
    if not result["success"]:
        error_msg = result.get("error", result.get("stderr", "Unknown error"))
        return f"Failed to get VirtualBox version. Error: {error_msg}"
    
    version = result.get("stdout", "").strip()
    
    # Get more details
    ext_result = await vbox_service.run_command(["list", "extpacks"], ctx)
    
    output = f"VirtualBox Version: {version}\n\n"
    
    if ext_result["success"]:
        output += "Installed Extension Packs:\n"
        ext_packs = ext_result.get("stdout", "")
        
        if "Extension Packs: 0" in ext_packs:
            output += "  None\n"
        else:
            for line in ext_packs.splitlines():
                if line.strip():
                    output += f"  {line.strip()}\n"
    
    return output


# MCP Tool: Change Tor Circuit
@mcp.tool()
async def change_tor_circuit(ctx: Context = None) -> str:
    """
    Request a new Tor circuit in Whonix Gateway.
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info("Requesting new Tor circuit...")
    
    # Get VM name from config
    gateway_vm = CONFIG["whonix"]["gateway_vm"]
    
    # Check if Gateway VM exists and is running
    gateway_info = await vbox_service.get_vm_info(gateway_vm, ctx)
    
    if not gateway_info:
        return f"Whonix Gateway VM '{gateway_vm}' not found. Please ensure it is installed."
    
    if not gateway_info.get("is_running", False):
        return f"Whonix Gateway VM '{gateway_vm}' is not running. Please start it first."
    
    # Try multiple methods to change the Tor circuit
    methods = [
        # Method 1: Using tor-ctrl-circuit
        [
            "guestcontrol", gateway_vm, "run", "--username", CONFIG["whonix"]["default_username"], 
            "--password", CONFIG["whonix"]["default_password"], "--verbose", "--", "/usr/bin/tor-ctrl-circuit", "new"
        ],
        
        # Method 2: Using polipo to restart
        [
            "guestcontrol", gateway_vm, "run", "--username", CONFIG["whonix"]["default_username"], 
            "--password", CONFIG["whonix"]["default_password"], "--verbose", "--", "/bin/bash", "-c",
            "/usr/bin/service polipo restart || echo 'Polipo not found or could not restart'"
        ],
        
        # Method 3: Direct SIGHUP to Tor
        [
            "guestcontrol", gateway_vm, "run", "--username", CONFIG["whonix"]["default_username"], 
            "--password", CONFIG["whonix"]["default_password"], "--verbose", "--", "/bin/bash", "-c", 
            "pkill -SIGHUP -x tor || echo 'Failed to send SIGHUP to Tor'"
        ],
        
        # Method 4: Using stream isolation via torsocks and curl
        [
            "guestcontrol", gateway_vm, "run", "--username", CONFIG["whonix"]["default_username"], 
            "--password", CONFIG["whonix"]["default_password"], "--verbose", "--", "/bin/bash", "-c", 
            "torsocks curl -s https://check.torproject.org/ > /dev/null 2>&1 && echo 'Circuit potentially changed via stream isolation'"
        ],
        
        # Method 5: Original method as fallback
        [
            "guestcontrol", gateway_vm, "run", "--username", CONFIG["whonix"]["default_username"],
            "--password", CONFIG["whonix"]["default_password"], "--verbose", "--", "/bin/bash", "-c", 
            "sudo -u debian-tor tor-reload || systemctl restart tor"
        ]
    ]
    
    success = False
    for i, method in enumerate(methods):
        await safe_ctx.info(f"Trying method {i+1} to change Tor circuit...")
        result = await vbox_service.run_command(method, ctx)
        
        if result["success"]:
            await safe_ctx.info(f"Method {i+1} executed successfully")
            success = True
            
            # Verify the Tor connection is still working
            check_cmd = [
                "guestcontrol", gateway_vm, 
                "run", "--username", CONFIG["whonix"]["default_username"], 
                "--password", CONFIG["whonix"]["default_password"], "--verbose",
                "--", "/usr/bin/curl", "--socks5", "127.0.0.1:9050", 
                "--connect-timeout", "10", "https://check.torproject.org/"
            ]
            
            check_result = await vbox_service.run_command(check_cmd, ctx)
            
            if check_result["success"] and "Congratulations" in check_result.get("stdout", ""):
                # Wait a moment to ensure the circuit is fully established
                await asyncio.sleep(3)
                return f"Successfully changed Tor circuit using method {i+1}. Tor connection is working properly."
        
        # If we've tried all methods and reached here, continue to the next method
    
    if success:
        # If at least one method was successful but verification failed
        return "A method to change the Tor circuit executed successfully, but we couldn't verify if Tor is still working correctly."
    else:
        # All methods failed
        return "Failed to change Tor circuit. None of the attempted methods worked. The Tor circuit control commands might not be available or require different permissions."
        
        # Note: You may need to manually log into the Whonix Gateway VM and run 'sudo service tor restart' to change the circuit.

# MCP Tool: Ensure both Whonix Gateway and Workstation VMs are running
@mcp.tool()
async def ensure_whonix_running(ctx: Context = None) -> str:
    """
    Ensure both Whonix Gateway and Workstation VMs are running.
    
    Returns:
        Status of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info("Ensuring Whonix VMs are running...")
    
    # Get VM names from config
    gateway_vm = CONFIG["whonix"]["gateway_vm"]
    workstation_vm = CONFIG["whonix"]["workstation_vm"]
    
    # Check if VMs exist
    gateway_info = await vbox_service.get_vm_info(gateway_vm, ctx)
    workstation_info = await vbox_service.get_vm_info(workstation_vm, ctx)
    
    if not gateway_info:
        return f"Whonix Gateway VM '{gateway_vm}' not found. Please ensure it is installed."
    
    if not workstation_info:
        return f"Whonix Workstation VM '{workstation_vm}' not found. Please ensure it is installed."
    
    # Start Gateway if not running
    if not gateway_info.get("is_running", False):
        await safe_ctx.info(f"Starting Whonix Gateway VM '{gateway_vm}'...")
        gateway_result = await vbox_service.start_vm(gateway_vm, True, ctx)
        
        if not gateway_result["success"]:
            error_msg = gateway_result.get("error", gateway_result.get("stderr", "Unknown error"))
            return f"Failed to start Whonix Gateway VM. Error: {error_msg}"
        
        # Wait for Gateway to boot
        await safe_ctx.info("Waiting for Whonix Gateway to boot...")
        await asyncio.sleep(30)
    
    # Start Workstation if not running
    if not workstation_info.get("is_running", False):
        await safe_ctx.info(f"Starting Whonix Workstation VM '{workstation_vm}'...")
        workstation_result = await vbox_service.start_vm(workstation_vm, True, ctx)
        
        if not workstation_result["success"]:
            error_msg = workstation_result.get("error", workstation_result.get("stderr", "Unknown error"))
            return f"Failed to start Whonix Workstation VM. Error: {error_msg}"
    
    return "Both Whonix Gateway and Workstation VMs are running."


# MCP Tool: Get detailed Tor status from Whonix Gateway
@mcp.tool()
async def get_tor_status(ctx: Context = None) -> str:
    """
    Get detailed Tor status from Whonix Gateway.
    
    Returns:
        Detailed Tor status information
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info("Getting Tor status from Whonix Gateway...")
    
    # Get VM name from config
    gateway_vm = CONFIG["whonix"]["gateway_vm"]
    
    # Check if Gateway VM exists and is running
    gateway_info = await vbox_service.get_vm_info(gateway_vm, ctx)
    
    if not gateway_info:
        return f"Whonix Gateway VM '{gateway_vm}' not found. Please ensure it is installed."
    
    if not gateway_info.get("is_running", False):
        return f"Whonix Gateway VM '{gateway_vm}' is not running. Please start it first."
    
    # Execute command to get Tor status
    status_cmd = [
        "guestcontrol", gateway_vm,
        "run", "--username", CONFIG["whonix"]["default_username"],
        "--password", CONFIG["whonix"]["default_password"],
        "--", "/usr/bin/systemctl", "status", "tor"
    ]
    
    result = await vbox_service.run_command(status_cmd, ctx)
    
    if not result["success"]:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to get Tor status. Error: {error_msg}"
    
    status_output = result.get("stdout", "")
    
    # Check if Tor is running
    tor_running = "active (running)" in status_output
    
    # Format the output
    output = "Tor Status in Whonix Gateway:\n" + "=" * 30 + "\n\n"
    output += f"Tor Service: {'RUNNING' if tor_running else 'NOT RUNNING'}\n\n"
    
    # Get additional Tor info if running
    if tor_running:
        # Get Tor circuit info
        await safe_ctx.info("Getting Tor circuit info...")
        
        circuit_cmd = [
            "guestcontrol", gateway_vm,
            "run", "--username", CONFIG["whonix"]["default_username"],
            "--password", CONFIG["whonix"]["default_password"],
            "--", "/usr/bin/curl", "--socks5", "127.0.0.1:9050",
            "--connect-timeout", "10", "https://check.torproject.org/"
        ]
        
        circuit_result = await vbox_service.run_command(circuit_cmd, ctx)
        
        if circuit_result["success"]:
            circuit_output = circuit_result.get("stdout", "")
            tor_working = "Congratulations" in circuit_output
            
            output += f"Tor Connectivity: {'WORKING' if tor_working else 'NOT WORKING'}\n"
            output += f"Internet Access: {'YES' if tor_working else 'NO'}\n\n"
        
        # Get Tor logs
        await safe_ctx.info("Getting Tor logs...")
        
        logs_cmd = [
            "guestcontrol", gateway_vm,
            "run", "--username", CONFIG["whonix"]["default_username"],
            "--password", CONFIG["whonix"]["default_password"],
            "--", "/usr/bin/journalctl", "-n", "10", "-u", "tor"
        ]
        
        logs_result = await vbox_service.run_command(logs_cmd, ctx)
        
        if logs_result["success"]:
            logs_output = logs_result.get("stdout", "")
            
            output += "Recent Tor Logs:\n"
            output += "---------------\n"
            output += logs_output + "\n\n"
    
    # Add the full service status
    output += "Full Tor Service Status:\n"
    output += "----------------------\n"
    output += status_output
    
    return output

# MCP Tool: Create a snapshot
@mcp.tool()
async def create_snapshot(ctx: Context = None, vm_name: str = "", snapshot_name: str = "", description: str = "") -> str:
    """
    Create a snapshot of a VM.
    
    Args:
        vm_name: Name of the VM
        snapshot_name: Name for the snapshot
        description: Description of the snapshot (optional)
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Creating snapshot '{snapshot_name}' for VM: {vm_name}")
    
    # Check if VM exists
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    # Create the snapshot
    cmd = ["snapshot", vm_name, "take", snapshot_name]
    if description:
        cmd.extend(["--description", description])
    
    result = await vbox_service.run_command(cmd, ctx)
    
    if result["success"]:
        return f"Successfully created snapshot '{snapshot_name}' for VM: {vm_name}"
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to create snapshot. Error: {error_msg}"


# MCP Tool: Restore a snapshot
@mcp.tool()
async def restore_snapshot(ctx: Context = None, vm_name: str = "", snapshot_name: str = "") -> str:
    """
    Restore a VM to a previous snapshot.
    
    Args:
        vm_name: Name of the VM
        snapshot_name: Name of the snapshot to restore
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Restoring VM '{vm_name}' to snapshot: {snapshot_name}")
    
    # Check if VM exists
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    # Check if VM is running (need to stop it first)
    if vm_info.get("is_running", False):
        await safe_ctx.info(f"VM '{vm_name}' is running, powering off first...")
        
        stop_result = await vbox_service.stop_vm(vm_name, True, ctx)
        
        if not stop_result["success"]:
            error_msg = stop_result.get("stderr", stop_result.get("error", "Unknown error"))
            return f"Failed to power off VM before restoring snapshot. Error: {error_msg}"
        
        # Give it a moment to fully power off
        await asyncio.sleep(2)
    
    # Restore the snapshot
    result = await vbox_service.run_command(["snapshot", vm_name, "restore", snapshot_name], ctx)
    
    if result["success"]:
        return f"Successfully restored VM '{vm_name}' to snapshot: {snapshot_name}"
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to restore snapshot. Error: {error_msg}"


# MCP Tool: List snapshots
@mcp.tool()
async def list_snapshots(ctx: Context = None, vm_name: str = "") -> str:
    """
    List all snapshots for a VM.
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        List of snapshots
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Listing snapshots for VM: {vm_name}")
    
    # Check if VM exists
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    # List snapshots
    result = await vbox_service.run_command(["snapshot", vm_name, "list"], ctx)
    
    if not result["success"]:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to list snapshots. Error: {error_msg}"
    
    snapshot_output = result.get("stdout", "")
    
    if "does not have any snapshots" in snapshot_output or not snapshot_output.strip():
        return f"VM '{vm_name}' does not have any snapshots."
    
    output = f"Snapshots for VM '{vm_name}':\n" + "=" * 30 + "\n\n"
    output += snapshot_output
    
    return output


# MCP Tool: Delete a snapshot
@mcp.tool()
async def delete_snapshot(ctx: Context = None, vm_name: str = "", snapshot_name: str = "") -> str:
    """
    Delete a snapshot of a VM.
    
    Args:
        vm_name: Name of the VM
        snapshot_name: Name of the snapshot to delete
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Deleting snapshot '{snapshot_name}' for VM: {vm_name}")
    
    # Check if VM exists
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    # Delete the snapshot
    result = await vbox_service.run_command(["snapshot", vm_name, "delete", snapshot_name], ctx)
    
    if result["success"]:
        return f"Successfully deleted snapshot '{snapshot_name}' for VM: {vm_name}"
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to delete snapshot. Error: {error_msg}"


# MCP Tool: Upload file to VM in chunks
@mcp.tool()
async def upload_file_to_vm(ctx: Context = None, 
                           file_path: str = "", 
                           vm_name: str = "", 
                           vm_destination: str = "",
                           username: Optional[str] = None,
                           password: Optional[str] = None) -> str:
    """
    Upload a file to VM in secure chunks without using shared folders.
    
    Args:
        file_path: Path to the file on the host
        vm_name: Name of the target VM
        vm_destination: Destination path in the VM
        username: VM username (default: from config)
        password: VM password (default: from config)
    
    Returns:
        Result of the upload operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    # Use default credentials if not provided
    if username is None:
        username = CONFIG["whonix"]["default_username"]
    if password is None:
        password = CONFIG["whonix"]["default_password"]
    
    await safe_ctx.info(f"Uploading file {file_path} to VM {vm_name}:{vm_destination}")
    
    # Check if VM is running
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    if not vm_info.get("is_running", False):
        return f"VM '{vm_name}' is not running. Please start it first."
    
    # Perform the upload
    result = await file_transfer_service.upload_file_chunked(
        file_path, vm_name, vm_destination, username, password, ctx
    )
    
    if result["success"]:
        return (f"Successfully uploaded file to VM:\n\n"
                f"File: {file_path}\n"
                f"Destination: {vm_destination}\n"
                f"Size: {result['file_size']} bytes\n"
                f"Chunks: {result['chunks_transferred']}\n"
                f"Hash: {result['hash']}")
    else:
        return f"Failed to upload file: {result['error']}"


# MCP Tool: Download file from VM in chunks
@mcp.tool()
async def download_file_from_vm(ctx: Context = None,
                               vm_path: str = "",
                               vm_name: str = "",
                               local_destination: str = "",
                               username: Optional[str] = None,
                               password: Optional[str] = None) -> str:
    """
    Download a file from VM in secure chunks without using shared folders.
    
    Args:
        vm_path: Path to the file in the VM
        vm_name: Name of the source VM
        local_destination: Destination path on the host
        username: VM username (default: from config)
        password: VM password (default: from config)
    
    Returns:
        Result of the download operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    # Use default credentials if not provided
    if username is None:
        username = CONFIG["whonix"]["default_username"]
    if password is None:
        password = CONFIG["whonix"]["default_password"]
    
    await safe_ctx.info(f"Downloading file from VM {vm_name}:{vm_path} to {local_destination}")
    
    # Check if VM is running
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    if not vm_info.get("is_running", False):
        return f"VM '{vm_name}' is not running. Please start it first."
    
    # Perform the download
    result = await file_transfer_service.download_file_chunked(
        vm_path, vm_name, local_destination, username, password, ctx
    )
    
    if result["success"]:
        return (f"Successfully downloaded file from VM:\n\n"
                f"Source: {vm_path}\n"
                f"Destination: {local_destination}\n"
                f"Size: {result['file_size']} bytes\n"
                f"Chunks: {result['chunks_transferred']}\n"
                f"Hash: {result['hash']}")
    else:
        return f"Failed to download file: {result['error']}"


# MCP Tool: List files in VM directory
@mcp.tool()
async def list_vm_directory(ctx: Context = None,
                           directory: str = "/home/user",
                           vm_name: str = "",
                           recursive: bool = False,
                           username: Optional[str] = None,
                           password: Optional[str] = None) -> str:
    """
    List files in a VM directory.
    
    Args:
        directory: Directory path in the VM (default: /home/user)
        vm_name: Name of the VM
        recursive: Whether to list recursively
        username: VM username (default: from config)
        password: VM password (default: from config)
    
    Returns:
        Directory listing
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    # Use default credentials if not provided
    if username is None:
        username = CONFIG["whonix"]["default_username"]
    if password is None:
        password = CONFIG["whonix"]["default_password"]
    
    await safe_ctx.info(f"Listing directory {directory} in VM {vm_name}")
    
    # Check if VM is running
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    if not vm_info.get("is_running", False):
        return f"VM '{vm_name}' is not running. Please start it first."
    
    # List the directory
    result = await file_transfer_service.list_vm_files(
        directory, vm_name, username, password, recursive, ctx
    )
    
    if result["success"]:
        mode = "recursive" if recursive else "non-recursive"
        return (f"Directory listing ({mode}) for {directory}:\n\n"
                f"{result['listing']}")
    else:
        return f"Failed to list directory: {result['error']}"

# MCP Tool: Resume a paused VM
@mcp.tool()
async def resume_vm(ctx: Context = None, vm_name: str = "") -> str:
    """
    Resume a paused VM.
    
    Args:
        vm_name: Name of the VM to resume
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Resuming VM: {vm_name}")
    
    # Check if VM exists and get its state
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    vm_state = vm_info.get("VMState", "unknown")
    
    if vm_state == "running":
        return f"VM '{vm_name}' is already running."
    elif vm_state != "paused":
        return f"VM '{vm_name}' is in state '{vm_state}'. Can only resume paused VMs."
    
    # Try to resume the VM
    result = await vbox_service.run_command(["controlvm", vm_name, "resume"], ctx)
    
    if result["success"]:
        return f"Successfully resumed VM: {vm_name}"
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        
        # If regular resume fails, try to unlock and resume
        if "locked" in error_msg.lower() or "invalid object state" in error_msg.lower():
            await safe_ctx.warning("VM appears to have a locked session. Attempting to discard saved state...")
            
            # Try discarding saved state (less destructive than reset)
            discard_result = await vbox_service.run_command(["discardstate", vm_name], ctx)
            
            if discard_result["success"]:
                return f"Successfully discarded saved state for VM: {vm_name}. You can now start it normally."
            else:
                return (f"Failed to resume VM: {vm_name}. Error: {error_msg}\n\n"
                       f"The VM session appears to be locked. You may need to:\n"
                       f"1. Close VirtualBox GUI if it's open\n"
                       f"2. Use 'unlock_vm' tool to force unlock\n"
                       f"3. Use 'reset_vm' tool as a last resort")
        else:
            return f"Failed to resume VM: {vm_name}. Error: {error_msg}"

# MCP Tool: Unlock a VM session
@mcp.tool()
async def unlock_vm(ctx: Context = None, vm_name: str = "", force: bool = False) -> str:
    """
    Unlock a VM session that appears to be locked.
    
    Args:
        vm_name: Name of the VM to unlock
        force: Whether to force unlock even if it might cause data loss
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Unlocking VM session: {vm_name}")
    
    # Check if VM exists
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    vm_state = vm_info.get("VMState", "unknown")
    
    # Try different methods to unlock the VM
    methods_tried = []
    
    # Method 1: Try to discard the current state (for paused/saved VMs)
    if vm_state in ["paused", "saved"]:
        await safe_ctx.info("Attempting to discard saved/paused state...")
        discard_result = await vbox_service.run_command(["discardstate", vm_name], ctx)
        methods_tried.append("discard state")
        
        if discard_result["success"]:
            return f"Successfully unlocked VM '{vm_name}' by discarding saved state. VM is now powered off and can be started."
    
    # Method 2: Try to power off the VM
    if vm_state in ["running", "paused", "stuck"]:
        await safe_ctx.info("Attempting to power off VM...")
        poweroff_result = await vbox_service.run_command(["controlvm", vm_name, "poweroff"], ctx)
        methods_tried.append("power off")
        
        if poweroff_result["success"]:
            return f"Successfully unlocked VM '{vm_name}' by powering it off."
    
    # Method 3: Force unlock if requested
    if force:
        await safe_ctx.warning("Force unlocking VM (may cause data loss)...")
        
        # Try emergency stop
        emergency_result = await vbox_service.run_command(
            ["startvm", vm_name, "--type", "emergencystop"], ctx
        )
        methods_tried.append("emergency stop")
        
        if emergency_result["success"]:
            return f"Successfully force unlocked VM '{vm_name}' using emergency stop."
        
        # As a last resort, try to unregister and re-register
        await safe_ctx.warning("Attempting to unregister and re-register VM...")
        
        # Get the VM config file path
        config_file = vm_info.get("CfgFile", "")
        
        if config_file:
            # Unregister VM (keeping files)
            unreg_result = await vbox_service.run_command(["unregistervm", vm_name], ctx)
            
            if unreg_result["success"]:
                # Re-register VM
                reg_result = await vbox_service.run_command(["registervm", config_file], ctx)
                methods_tried.append("unregister/re-register")
                
                if reg_result["success"]:
                    return f"Successfully unlocked VM '{vm_name}' by re-registering it."
    
    # If we get here, none of the methods worked
    return (f"Failed to unlock VM '{vm_name}'. Current state: {vm_state}\n"
           f"Methods tried: {', '.join(methods_tried)}\n\n"
           f"Suggestions:\n"
           f"1. Close VirtualBox GUI if it's open\n"
           f"2. Check for any VBoxSVC processes and kill them\n"
           f"3. Try 'unlock_vm' with force=True (may cause data loss)\n"
           f"4. Restart VirtualBox service: sudo systemctl restart virtualbox\n"
           f"5. As last resort, reboot the host machine")

# MCP Tool: Get detailed VM state
@mcp.tool()
async def get_vm_state(ctx: Context = None, vm_name: str = "") -> str:
    """
    Get detailed state information about a VM including lock status.
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        Detailed state information
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Getting detailed state for VM: {vm_name}")
    
    # Get VM info
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    # Get basic state
    vm_state = vm_info.get("VMState", "unknown")
    session_name = vm_info.get("SessionName", "none")
    session_pid = vm_info.get("SessionPid", "none")
    
    # Check for lock file
    config_file = vm_info.get("CfgFile", "")
    lock_file = config_file.replace(".vbox", ".vbox-prev") if config_file else ""
    
    # Build detailed state report
    output = f"VM State Details for '{vm_name}':\n" + "=" * 40 + "\n\n"
    output += f"Current State: {vm_state}\n"
    output += f"Session Name: {session_name}\n"
    output += f"Session PID: {session_pid}\n"
    
    if vm_state == "paused":
        output += "\nVM is PAUSED. Options:\n"
        output += "- Use 'resume_vm' to resume execution\n"
        output += "- Use 'stop_vm' with force=True to power off\n"
        output += "- Use 'unlock_vm' if session appears locked\n"
    elif vm_state == "saved":
        output += "\nVM is in SAVED state. Options:\n"
        output += "- Use 'start_vm' to restore and run\n"
        output += "- Use 'discard_saved_state' to discard and start fresh\n"
    elif vm_state == "running":
        output += "\nVM is RUNNING normally.\n"
    elif vm_state == "poweroff":
        output += "\nVM is POWERED OFF. Use 'start_vm' to start.\n"
    elif vm_state == "aborted":
        output += "\nVM was ABORTED. Options:\n"
        output += "- Use 'start_vm' to start normally\n"
        output += "- Use 'restore_snapshot' to restore to a previous state\n"
    
    # Check for common issues
    if session_name != "none" and vm_state == "poweroff":
        output += "\n⚠️ WARNING: VM appears powered off but has an active session!\n"
        output += "This may indicate a locked or stuck session.\n"
        output += "Try using 'unlock_vm' tool to fix this.\n"
    
    return output

# MCP Tool: Discard saved state
@mcp.tool()
async def discard_saved_state(ctx: Context = None, vm_name: str = "") -> str:
    """
    Discard the saved state of a VM (useful for stuck paused/saved VMs).
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
    # Check if VirtualBox is installed
    if not await check_virtualbox_installed(ctx):
        return "VirtualBox not found. Please ensure VirtualBox is installed and VBoxManage is in your PATH."
    
    await safe_ctx.info(f"Discarding saved state for VM: {vm_name}")
    
    # Check if VM exists and get its state
    vm_info = await vbox_service.get_vm_info(vm_name, ctx)
    
    if not vm_info:
        return f"VM '{vm_name}' not found."
    
    vm_state = vm_info.get("VMState", "unknown")
    
    if vm_state not in ["paused", "saved"]:
        return f"VM '{vm_name}' is in state '{vm_state}'. Can only discard saved state for paused or saved VMs."
    
    # Discard the saved state
    result = await vbox_service.run_command(["discardstate", vm_name], ctx)
    
    if result["success"]:
        return f"Successfully discarded saved state for VM: {vm_name}. VM is now powered off and can be started fresh."
    else:
        error_msg = result.get("stderr", result.get("error", "Unknown error"))
        return f"Failed to discard saved state. Error: {error_msg}"

# ==============================================================================
# ENHANCED WEB AUTOMATION TOOLS (v0.6.0)
# ==============================================================================

@mcp.tool()
async def setup_enhanced_browser_environment(
    ctx: Context = None,
    vm_name: str = ""
) -> str:
    """
    Setup comprehensive browser automation environment with all dependencies.
    
    Installs Node.js, Playwright, Firefox, Chromium, ImageMagick, and other
    required tools for advanced web automation in the specified VM.
    
    Args:
        vm_name: Name of the VM to setup (default: Whonix-Workstation-Xfce)
    
    Returns:
        JSON string with setup results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Setting up enhanced browser environment in VM: {vm_name}")
    
    try:
        result = await web_automation_service.setup_browser_environment(vm_name)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def execute_javascript_on_webpage(
    ctx: Context = None,
    url: str = "",
    javascript_code: str = "",
    vm_name: str = "",
    browser: str = "firefox",
    headless: bool = True
) -> str:
    """
    Execute JavaScript code on a webpage and return results.
    
    Args:
        url: URL of the webpage to load
        javascript_code: JavaScript code to execute
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        browser: Browser to use (firefox or chromium)
        headless: Whether to run in headless mode
    
    Returns:
        JSON string with execution results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Executing JavaScript on {url} in VM: {vm_name}")
    
    try:
        result = await web_automation_service.execute_javascript(
            vm_name, url, javascript_code, browser, headless
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def capture_webpage_screenshot(
    ctx: Context = None,
    url: str = "",
    vm_name: str = "",
    selector: str = "",
    full_page: bool = True,
    browser: str = "firefox"
) -> str:
    """
    Capture screenshot of webpage or specific element.
    
    Args:
        url: URL of the webpage to screenshot
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        selector: CSS selector for specific element (empty for full page)
        full_page: Whether to capture full page
        browser: Browser to use (firefox or chromium)
    
    Returns:
        JSON string with screenshot data (base64 encoded)
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Capturing screenshot of {url} in VM: {vm_name}")
    
    try:
        result = await web_automation_service.capture_screenshot(
            vm_name, url, selector if selector else None, full_page, browser
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def interact_with_webpage_elements(
    ctx: Context = None,
    url: str = "",
    interactions: str = "[]",
    vm_name: str = "",
    browser: str = "firefox"
) -> str:
    """
    Perform DOM interactions like clicking, typing, selecting.
    
    Args:
        url: URL of the webpage
        interactions: JSON string of interaction list
                     [{"action": "click", "selector": "#button", "wait": 1000}, ...]
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        browser: Browser to use (firefox or chromium)
    
    Returns:
        JSON string with interaction results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Performing DOM interactions on {url} in VM: {vm_name}")
    
    try:
        interaction_list = json.loads(interactions)
        result = await web_automation_service.interact_with_dom(
            vm_name, url, interaction_list, browser
        )
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid interactions JSON"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def analyze_webpage_form_structure(
    ctx: Context = None,
    url: str = "",
    vm_name: str = ""
) -> str:
    """
    Analyze webpage forms and identify fillable fields with their purposes.
    
    Args:
        url: URL of the webpage with forms
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
    
    Returns:
        JSON string with form analysis results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not form_automation_service:
        return json.dumps({"success": False, "error": "Form automation service not available"})
    
    await safe_ctx.info(f"Analyzing form structure on {url} in VM: {vm_name}")
    
    try:
        result = await form_automation_service.analyze_form_structure(vm_name, url)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def fill_webpage_form_intelligently(
    ctx: Context = None,
    url: str = "",
    form_data: str = "{}",
    vm_name: str = "",
    submit: bool = False
) -> str:
    """
    Intelligently fill webpage forms based on field detection.
    
    Args:
        url: URL of the webpage with form
        form_data: JSON string of form data {"email": "test@example.com", ...}
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        submit: Whether to submit the form after filling
    
    Returns:
        JSON string with form filling results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not form_automation_service:
        return json.dumps({"success": False, "error": "Form automation service not available"})
    
    await safe_ctx.info(f"Filling form on {url} in VM: {vm_name}")
    
    try:
        data = json.loads(form_data)
        result = await form_automation_service.fill_form_intelligently(vm_name, url, data, submit)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid form data JSON"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def detect_webpage_visual_elements(
    ctx: Context = None,
    url: str = "",
    vm_name: str = "",
    element_types: str = "buttons,links,forms,images,inputs"
) -> str:
    """
    Detect and locate visual elements on webpage.
    
    Args:
        url: URL of the webpage to analyze
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        element_types: Comma-separated list of element types to detect
    
    Returns:
        JSON string with detected elements and their properties
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not form_automation_service:
        return json.dumps({"success": False, "error": "Form automation service not available"})
    
    await safe_ctx.info(f"Detecting visual elements on {url} in VM: {vm_name}")
    
    try:
        types_list = [t.strip() for t in element_types.split(",")]
        result = await form_automation_service.detect_visual_elements(vm_name, url, types_list)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def extract_webpage_content_with_ai(
    ctx: Context = None,
    url: str = "",
    extraction_prompt: str = "",
    vm_name: str = "",
    include_screenshot: bool = True
) -> str:
    """
    Extract and analyze webpage content using AI-assisted methods.
    
    Args:
        url: URL of the webpage to analyze
        extraction_prompt: Description of what to extract
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        include_screenshot: Whether to include screenshot in analysis
    
    Returns:
        JSON string with extracted content and analysis
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Extracting content from {url} in VM: {vm_name}")
    
    try:
        result = await web_automation_service.extract_content_with_ai(
            vm_name, url, extraction_prompt, include_screenshot
        )
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def manage_persistent_web_session(
    ctx: Context = None,
    session_id: str = "",
    action: str = "create",
    vm_name: str = "",
    session_data: str = "{}"
) -> str:
    """
    Manage persistent web sessions with cookies and state.
    
    Args:
        session_id: Unique identifier for the session
        action: Action to perform (create, load, update, delete)
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        session_data: JSON string of session data for create/update actions
    
    Returns:
        JSON string with session management results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not web_automation_service:
        return json.dumps({"success": False, "error": "Web automation service not available"})
    
    await safe_ctx.info(f"Managing web session {session_id} ({action}) in VM: {vm_name}")
    
    try:
        data = json.loads(session_data) if session_data != "{}" else None
        result = await web_automation_service.manage_web_session(
            vm_name, session_id, action, data
        )
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid session data JSON"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

@mcp.tool()
async def perform_visual_webpage_automation(
    ctx: Context = None,
    url: str = "",
    automation_steps: str = "[]",
    vm_name: str = ""
) -> str:
    """
    Perform complex visual automation workflows on webpage.
    
    Args:
        url: URL of the webpage
        automation_steps: JSON string of automation steps
                         [{"action": "click_text", "target": "Login", "wait": 1000}, ...]
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
    
    Returns:
        JSON string with automation results
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    if not form_automation_service:
        return json.dumps({"success": False, "error": "Form automation service not available"})
    
    await safe_ctx.info(f"Performing visual automation on {url} in VM: {vm_name}")
    
    try:
        steps = json.loads(automation_steps)
        result = await form_automation_service.perform_visual_automation(vm_name, url, steps)
        return json.dumps(result, indent=2)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "error": "Invalid automation steps JSON"})
    except Exception as e:
        return json.dumps({"success": False, "error": str(e)})

# ==============================================================================
# END ENHANCED WEB AUTOMATION TOOLS
# ==============================================================================

# ==============================================================================
# SPECIALIZED BROWSER AUTOMATION TOOLS
# These tools directly interface with the deployed browser automation framework
# ==============================================================================

@mcp.tool()
async def browser_intelligent_search(
    ctx: Context = None,
    search_query: str = "",
    vm_name: str = "",
    search_engine: str = "duckduckgo"
) -> str:
    """
    Perform intelligent search operation with natural language processing.
    
    This tool uses the deployed browser automation framework to:
    - Process natural language search queries
    - Execute searches through anonymous engines  
    - Capture screenshots of results
    - Return structured JSON with results and screenshots
    
    Args:
        search_query: Natural language search query (e.g., "find cybersecurity news")
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        search_engine: Search engine to use (duckduckgo, searx)
    
    Returns:
        JSON string with search results, screenshot path, and metadata
    """
    safe_ctx = SafeContext(ctx)
    
    if not search_query:
        return json.dumps({"success": False, "error": "Search query is required"})
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    await safe_ctx.info(f"Executing intelligent search: '{search_query}' in VM: {vm_name}")
    
    try:
        # Use the secure browser automation API v2.0 - NO STRING INTERPOLATION
        # Build command arguments safely
        command_args = [
            "python3",
            "/home/user/browser_automation/browser_api_v2.py",
            "search",
            search_query,
            "10"  # max results
        ]
        # Join arguments with proper escaping
        command = shlex.join(command_args)
        
        result = await execute_vm_command(
            ctx,
            vm_name, 
            command,
            CONFIG["whonix"]["default_username"],
            CONFIG["whonix"]["default_password"]
        )
        
        await safe_ctx.success(f"Search completed for: {search_query}")
        return result
        
    except Exception as e:
        error_msg = f"Browser search failed: {str(e)}"
        await safe_ctx.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


@mcp.tool()
async def browser_capture_page_screenshot(
    ctx: Context = None,
    target_url: str = "",
    vm_name: str = "",
    filename_prefix: str = ""
) -> str:
    """
    Capture high-quality screenshot of any webpage through Tor.
    
    This tool uses the deployed browser automation framework to:
    - Navigate to URLs through Tor network
    - Capture full-page screenshots
    - Save with timestamp and metadata
    - Return file details and success status
    
    Args:
        target_url: URL to capture (e.g., "https://example.com")  
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        filename_prefix: Optional prefix for screenshot filename
        
    Returns:
        JSON string with screenshot details, file size, and path
    """
    safe_ctx = SafeContext(ctx)
    
    if not target_url:
        return json.dumps({"success": False, "error": "Target URL is required"})
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    await safe_ctx.info(f"Capturing screenshot of: {target_url} in VM: {vm_name}")
    
    try:
        # Use the secure browser automation API v2.0 - NO STRING INTERPOLATION
        # Build command arguments safely
        command_args = [
            "python3",
            "/home/user/browser_automation/browser_api_v2.py",
            "capture",
            target_url
        ]
        # Add optional filename prefix if provided
        if filename_prefix:
            command_args.append(filename_prefix)
        
        # Join arguments with proper escaping
        command = shlex.join(command_args)
        
        result = await execute_vm_command(
            ctx,
            vm_name,
            command, 
            CONFIG["whonix"]["default_username"],
            CONFIG["whonix"]["default_password"]
        )
        
        await safe_ctx.success(f"Screenshot captured for: {target_url}")
        return result
        
    except Exception as e:
        error_msg = f"Screenshot capture failed: {str(e)}"
        await safe_ctx.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


@mcp.tool()
async def browser_automation_status_check(
    ctx: Context = None,
    vm_name: str = ""
) -> str:
    """
    Check the status and readiness of browser automation framework.
    
    This tool verifies:
    - Browser automation framework deployment
    - Available components and scripts
    - System readiness for browser operations
    - Tor connectivity status
    
    Args:
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        
    Returns:
        JSON string with deployment status and component information
    """
    safe_ctx = SafeContext(ctx)
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    await safe_ctx.info(f"Checking browser automation status in VM: {vm_name}")
    
    try:
        # Check browser automation status using secure API v2.0
        # Build command arguments safely
        command_args = [
            "python3",
            "/home/user/browser_automation/browser_api_v2.py",
            "status"
        ]
        # Join arguments with proper escaping
        command = shlex.join(command_args)
        
        result = await execute_vm_command(
            ctx,
            vm_name,
            command,
            CONFIG["whonix"]["default_username"], 
            CONFIG["whonix"]["default_password"]
        )
        
        await safe_ctx.success("Browser automation status check completed")
        return result
        
    except Exception as e:
        error_msg = f"Status check failed: {str(e)}"
        await safe_ctx.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


@mcp.tool()
async def browser_bulk_screenshot_capture(
    ctx: Context = None,
    url_list: str = "",
    vm_name: str = "",
    batch_name: str = ""
) -> str:
    """
    Capture screenshots of multiple URLs in a single operation.
    
    This tool processes multiple URLs efficiently:
    - Batch processing for efficiency
    - Individual success/failure tracking
    - Consolidated results reporting
    - Organized file management
    
    Args:
        url_list: Comma-separated list of URLs to capture
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)  
        batch_name: Optional name for this batch operation
        
    Returns:
        JSON string with batch results and individual screenshot details
    """
    safe_ctx = SafeContext(ctx)
    
    if not url_list:
        return json.dumps({"success": False, "error": "URL list is required"})
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    urls = [url.strip() for url in url_list.split(',') if url.strip()]
    
    if not urls:
        return json.dumps({"success": False, "error": "No valid URLs provided"})
    
    await safe_ctx.info(f"Starting bulk screenshot capture of {len(urls)} URLs in VM: {vm_name}")
    
    results = []
    
    try:
        for i, url in enumerate(urls, 1):
            await safe_ctx.info(f"Processing URL {i}/{len(urls)}: {url}")
            
            # Use the secure browser automation API v2.0 - NO STRING INTERPOLATION
            # Build command arguments safely
            command_args = [
                "python3",
                "/home/user/browser_automation/browser_api_v2.py",
                "capture",
                url
            ]
            # Join arguments with proper escaping
            command = shlex.join(command_args)
            
            result = await execute_vm_command(
                ctx,
                vm_name,
                command,
                CONFIG["whonix"]["default_username"],
                CONFIG["whonix"]["default_password"]
            )
            
            # Parse result and add to batch
            try:
                # Result is already cleaned by execute_vm_command
                if result.startswith('{'):
                    parsed_result = json.loads(result)
                else:
                    # Not JSON, but command may have succeeded
                    parsed_result = {
                        "success": "error" not in result.lower(),
                        "output": result[:200]
                    }
                
                parsed_result['batch_index'] = i
                parsed_result['url'] = url
                parsed_result['batch_name'] = batch_name or f"batch_{int(time.time())}"
                results.append(parsed_result)
            except Exception as e:
                results.append({
                    "success": False, 
                    "url": url, 
                    "batch_index": i,
                    "error": f"Failed to parse: {str(e)}"
                })
        
        # Compile batch results
        successful = sum(1 for r in results if r.get('success', False))
        batch_result = {
            "success": True,
            "batch_name": batch_name or f"batch_{int(time.time())}",
            "total_urls": len(urls),
            "successful_captures": successful,
            "failed_captures": len(urls) - successful,
            "results": results
        }
        
        await safe_ctx.success(f"Bulk screenshot completed: {successful}/{len(urls)} successful")
        return json.dumps(batch_result, indent=2)
        
    except Exception as e:
        error_msg = f"Bulk screenshot operation failed: {str(e)}"
        await safe_ctx.error(error_msg)
        return json.dumps({"success": False, "error": error_msg, "partial_results": results})


@mcp.tool()
async def browser_custom_automation_task(
    ctx: Context = None,
    task_description: str = "",
    target_url: str = "",
    vm_name: str = "",
    custom_parameters: Optional[str] = None
) -> str:
    """
    Execute custom browser automation tasks with flexible parameters.
    
    This tool enables:
    - Custom automation workflows
    - Flexible parameter passing
    - Task-specific browser operations
    - Extensible automation capabilities
    
    Args:
        task_description: Description of the automation task to perform
        target_url: Optional URL to operate on
        vm_name: Name of the VM (default: Whonix-Workstation-Xfce)
        custom_parameters: JSON string of custom parameters for the task
        
    Returns:
        JSON string with task execution results and output data
    """
    safe_ctx = SafeContext(ctx)
    
    if not task_description:
        return json.dumps({"success": False, "error": "Task description is required"})
    
    if not vm_name:
        vm_name = CONFIG["whonix"]["workstation_vm"]
    
    await safe_ctx.info(f"Executing custom automation task: '{task_description}' in VM: {vm_name}")
    
    try:
        # Parse parameters safely, handling None and various input types
        try:
            if custom_parameters is None:
                params = {}
            elif isinstance(custom_parameters, str):
                params = json.loads(custom_parameters) if custom_parameters.strip() not in ["", "{}"] else {}
            elif isinstance(custom_parameters, dict):
                params = custom_parameters
            else:
                params = {}
        except Exception:
            params = {}
        
        # Route based on task description or parameters
        if "version" in task_description.lower():
            command_args = ["firefox", "--version"]
        elif "search" in task_description.lower():
            # Route to search operation using secure API
            search_query = params.get('query', target_url or task_description)
            command_args = [
                "python3",
                "/home/user/browser_automation/browser_api_v2.py",
                "search",
                search_query
            ]
        elif "screenshot" in task_description.lower() and target_url:
            # Route to screenshot operation using secure API
            command_args = [
                "python3",
                "/home/user/browser_automation/browser_api_v2.py",
                "capture",
                target_url
            ]
        else:
            # Default to status check using secure API
            command_args = [
                "python3",
                "/home/user/browser_automation/browser_api_v2.py",
                "status"
            ]
        
        # Join arguments with proper escaping to prevent injection
        command = shlex.join(command_args)
        
        result = await execute_vm_command(
            ctx,
            vm_name,
            command,
            CONFIG["whonix"]["default_username"],
            CONFIG["whonix"]["default_password"]  
        )
        
        # Enhance result with task context
        try:
            # Try to parse as JSON first
            if result.startswith('{'):
                parsed_result = json.loads(result)
                parsed_result['task_description'] = task_description
                parsed_result['custom_parameters'] = params
            else:
                # Not JSON, wrap in response
                parsed_result = {
                    "success": True,
                    "task_description": task_description,
                    "custom_parameters": params,
                    "output": result
                }
            result = json.dumps(parsed_result, indent=2)
        except:
            pass  # Return original result if parsing fails
        
        await safe_ctx.success(f"Custom automation task completed: {task_description}")
        return result
        
    except Exception as e:
        error_msg = f"Custom automation task failed: {str(e)}"
        await safe_ctx.error(error_msg)
        return json.dumps({
            "success": False, 
            "error": error_msg,
            "task_description": task_description
        })

# ==============================================================================
# END SPECIALIZED BROWSER AUTOMATION TOOLS
# ==============================================================================

# Main function to run the server
if __name__ == "__main__":
    logger.info("Starting Consolidated Whonix VirtualBox MCP server")
    
    # Print configuration information
    print(f"Starting Whonix VirtualBox MCP server v{VERSION}")
    print(f"Using VBoxManage at: {vbox_service.vboxmanage_path}")
    print(f"Whonix Gateway VM: {CONFIG['whonix']['gateway_vm']}")
    print(f"Whonix Workstation VM: {CONFIG['whonix']['workstation_vm']}")
    
    try:
        # Run the server
        mcp.run()
    except KeyboardInterrupt:
        print("\nShutting down Whonix VirtualBox MCP server...")
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        print(f"Error: {e}")
