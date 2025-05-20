#!/usr/bin/env python3

"""
VirtualBox Service - Core functionality for VirtualBox management
This module handles all VBoxManage command execution and VM operations
"""

import asyncio
import subprocess
import os
import shutil
import logging
import json
import re
from typing import List, Dict, Any, Optional, Union, Tuple

from safe_context import SafeContext

class VirtualBoxService:
    """Service for interacting with VirtualBox and managing VMs."""
    
    def get_error_diagnostics(self, error_msg: str) -> str:
        """Generate diagnostic information for common VirtualBox errors."""
        
        diagnostics = ""
        
        if "VBOX_E_INVALID_OBJECT_STATE" in error_msg and "lock" in error_msg:
            diagnostics = (
                "This error occurs when VirtualBox can't access a disk because it's in use or locked.\n"
                "Possible solutions:\n"
                "1. Make sure the VM is completely powered off\n"
                "2. Try running 'VBoxManage mediaunregister --type disk' to unlock media\n"
                "3. Restart the VirtualBox service\n"
                "4. In extreme cases, rebooting the host system"
            )
        elif "command not found" in error_msg:
            diagnostics = (
                "The command couldn't be found in the guest VM.\n"
                "Make sure Guest Additions are installed and:\n"
                "1. Use absolute paths for commands (e.g., /bin/ls instead of ls)\n"
                "2. Check if the command exists in the guest VM\n"
                "3. Try executing the command through a shell (e.g., /bin/bash -c 'command')"
            )
        elif "authentication required" in error_msg.lower():
            diagnostics = (
                "This operation requires elevated privileges in the guest OS.\n"
                "Possible solutions:\n"
                "1. Try a different command that doesn't require sudo\n"
                "2. Configure passwordless sudo in the guest VM\n"
                "3. Log into the VM directly and run the command from there"
            )
        
        return diagnostics
    
    def __init__(self, vboxmanage_path: str = "/usr/bin/VBoxManage"):
        """
        Initialize the VirtualBox service.
        
        Args:
            vboxmanage_path: Path to the VBoxManage executable
        """
        self.vboxmanage_path = vboxmanage_path
        self.logger = logging.getLogger("VirtualBoxService")
        
        # Detect VBoxManage path if not provided
        if not os.path.exists(self.vboxmanage_path):
            detected_path = self._detect_vboxmanage_path()
            if detected_path:
                self.logger.info(f"Auto-detected VBoxManage path: {detected_path}")
                self.vboxmanage_path = detected_path
    
    def _detect_vboxmanage_path(self) -> Optional[str]:
        """
        Attempt to detect the VBoxManage executable path.
        
        Returns:
            str: Path to VBoxManage if found, None otherwise
        """
        # Common paths to check
        common_paths = [
            "/usr/bin/VBoxManage",
            "/usr/local/bin/VBoxManage",
            "/opt/VirtualBox/VBoxManage",
            # Windows paths
            "C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe",
            "C:\\Program Files (x86)\\Oracle\\VirtualBox\\VBoxManage.exe"
        ]
        
        # Try which command first (Unix/Linux)
        try:
            result = subprocess.run(
                ["which", "VBoxManage"], 
                capture_output=True, 
                text=True,
                timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
            
        # Check common paths
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        # Check in PATH
        for path_dir in os.environ.get("PATH", "").split(os.pathsep):
            potential_path = os.path.join(path_dir, "VBoxManage")
            if os.path.exists(potential_path):
                return potential_path
                
        return None
    
    async def run_command(self, args: List[str], ctx=None) -> Dict[str, Any]:
        """
        Run a VBoxManage command and return the result.
        
        Args:
            args: List of arguments to pass to VBoxManage
            ctx: MCP context for reporting progress
            
        Returns:
            dict: Command execution result
        """
        safe_ctx = SafeContext(ctx)
        
        if not os.path.exists(self.vboxmanage_path):
            error_msg = f"VBoxManage not found at {self.vboxmanage_path}"
            await safe_ctx.error(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "command": f"{self.vboxmanage_path} {' '.join(args)}"
            }
        
        cmd = [self.vboxmanage_path] + args
        cmd_str = " ".join(cmd)
        
        await safe_ctx.info(f"Running VBoxManage command: {' '.join(args)}")
        await safe_ctx.progress("Executing VBoxManage command...", 10)
        
        try:
            # Add timeout to prevent command hanging indefinitely
            process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                ),
                timeout=60  # 60 second timeout
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=120  # 2 minute timeout for long operations
            )
            
            stdout_str = stdout.decode('utf-8', errors='replace').strip()
            stderr_str = stderr.decode('utf-8', errors='replace').strip()
            return_code = process.returncode
            
            await safe_ctx.progress("Command completed", 100)
            
            if return_code != 0:
                await safe_ctx.error(f"Command failed: {stderr_str}")
                # Add diagnostic info
                diagnostics = self.get_error_diagnostics(stderr_str)
                return {
                    "success": False,
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                    "return_code": return_code,
                    "command": cmd_str,
                    "diagnostics": diagnostics
                }
            
            return {
                "success": True,
                "stdout": stdout_str,
                "stderr": stderr_str,
                "return_code": return_code,
                "command": cmd_str
            }
        except asyncio.TimeoutError:
            await safe_ctx.error("Command timed out")
            return {
                "success": False,
                "error": "Command timed out after 120 seconds",
                "command": cmd_str
            }
        except Exception as e:
            error_msg = f"Error running VBoxManage command: {str(e)}"
            self.logger.error(error_msg)
            await safe_ctx.error(error_msg)
            
            return {
                "success": False,
                "error": str(e),
                "command": cmd_str
            }
    
    async def get_vm_list(self, ctx=None) -> List[Dict[str, Any]]:
        """
        Get list of all VMs.
        
        Args:
            ctx: MCP context for reporting progress
            
        Returns:
            list: List of VM information dictionaries
        """
        safe_ctx = SafeContext(ctx)
        await safe_ctx.info("Retrieving list of VMs...")
        
        result = await self.run_command(["list", "vms"], ctx)
        
        if not result["success"]:
            await safe_ctx.error("Failed to list VMs")
            return []
            
        vms = []
        for line in result["stdout"].splitlines():
            # Parse VM info (format: "VM Name" {UUID})
            match = re.search(r'"([^"]+)"\s+\{([^}]+)\}', line)
            if match:
                name, uuid = match.groups()
                vms.append({
                    "name": name,
                    "uuid": uuid
                })
        
        # Get additional info for each VM
        await safe_ctx.progress("Retrieving VM details...", 50)
        
        detailed_vms = []
        for vm in vms:
            try:
                vm_info = await self.get_vm_info(vm["name"], ctx)
                if vm_info:
                    detailed_vms.append({**vm, **vm_info})
                else:
                    detailed_vms.append(vm)
            except Exception as e:
                self.logger.error(f"Error getting info for VM {vm['name']}: {e}")
                detailed_vms.append(vm)
        
        await safe_ctx.progress("VM list retrieved", 100)
        return detailed_vms
    
    async def get_vm_info(self, vm_name: str, ctx=None) -> Dict[str, Any]:
        """
        Get detailed information about a VM.
        
        Args:
            vm_name: Name of the VM
            ctx: MCP context for reporting progress
            
        Returns:
            dict: VM information
        """
        safe_ctx = SafeContext(ctx)
        await safe_ctx.info(f"Getting info for VM: {vm_name}")
        
        result = await self.run_command(["showvminfo", vm_name, "--machinereadable"], ctx)
        
        if not result["success"]:
            await safe_ctx.error(f"Failed to get info for VM {vm_name}")
            return {}
            
        info = {}
        for line in result["stdout"].splitlines():
            if '=' in line:
                key, value = line.split('=', 1)
                # Remove quotes from values
                value = value.strip('"')
                info[key] = value
        
        # Add running state
        info["is_running"] = info.get("VMState") == "running"
        
        return info
    
    async def start_vm(self, vm_name: str, headless: bool = True, ctx=None) -> Dict[str, Any]:
        """
        Start a VM.
        
        Args:
            vm_name: Name of the VM to start
            headless: Whether to start in headless mode
            ctx: MCP context for reporting progress
            
        Returns:
            dict: Result of the operation
        """
        safe_ctx = SafeContext(ctx)
        await safe_ctx.info(f"Starting VM: {vm_name}")
        
        # Check if VM exists
        vm_info = await self.get_vm_info(vm_name, ctx)
        if not vm_info:
            await safe_ctx.error(f"VM '{vm_name}' not found")
            return {"success": False, "error": f"VM '{vm_name}' not found"}
        
        # Check if VM is already running
        if vm_info.get("is_running", False):
            await safe_ctx.info(f"VM '{vm_name}' is already running")
            return {"success": True, "message": f"VM '{vm_name}' is already running"}
        
        # Start VM
        cmd = ["startvm", vm_name]
        if headless:
            cmd.append("--type=headless")
        
        result = await self.run_command(cmd, ctx)
        
        if result["success"]:
            await safe_ctx.info(f"Successfully started VM '{vm_name}'")
        
        return result
    
    async def stop_vm(self, vm_name: str, force: bool = False, ctx=None) -> Dict[str, Any]:
        """
        Stop a VM.
        
        Args:
            vm_name: Name of the VM to stop
            force: Whether to force power off
            ctx: MCP context for reporting progress
            
        Returns:
            dict: Result of the operation
        """
        safe_ctx = SafeContext(ctx)
        await safe_ctx.info(f"Stopping VM: {vm_name}")
        
        # Check if VM exists and is running
        vm_info = await self.get_vm_info(vm_name, ctx)
        if not vm_info:
            await safe_ctx.error(f"VM '{vm_name}' not found")
            return {"success": False, "error": f"VM '{vm_name}' not found"}
        
        if not vm_info.get("is_running", False):
            await safe_ctx.info(f"VM '{vm_name}' is not running")
            return {"success": True, "message": f"VM '{vm_name}' is not running"}
        
        # Stop VM
        cmd = ["controlvm", vm_name]
        if force:
            cmd.append("poweroff")
        else:
            cmd.append("acpipowerbutton")
        
        result = await self.run_command(cmd, ctx)
        
        if result["success"]:
            await safe_ctx.info(f"Successfully {'powered off' if force else 'sent shutdown signal to'} VM '{vm_name}'")
        
        return result
    
    async def create_whonix_workstation(self, 
                                       name: str, 
                                       memory_mb: int = 2048, 
                                       disk_size_mb: int = 20000, 
                                       ctx=None) -> Dict[str, Any]:
        """
        Create a new Whonix Workstation VM.
        
        Args:
            name: Name for the new VM
            memory_mb: Memory in MB
            disk_size_mb: Disk size in MB
            ctx: MCP context for reporting progress
            
        Returns:
            dict: Result of the operation
        """
        safe_ctx = SafeContext(ctx)
        await safe_ctx.info(f"Creating new Whonix Workstation VM: {name}")
        
        # Check if a VM with this name already exists
        existing_vms = await self.get_vm_list(ctx)
        for vm in existing_vms:
            if vm["name"] == name:
                await safe_ctx.error(f"VM with name '{name}' already exists")
                return {"success": False, "error": f"VM with name '{name}' already exists"}
        
        # Check if Whonix template VM exists
        template_found = False
        for vm in existing_vms:
            if "Whonix-Workstation" in vm["name"]:
                template_found = True
                template_name = vm["name"]
                template_vm = vm
                break
        
        if not template_found:
            await safe_ctx.error("Whonix Workstation template VM not found")
            return {"success": False, "error": "Whonix Workstation template VM not found"}
        
        # Check if template VM is running or in saved state, if so we need to stop it first
        if template_vm.get("VMState") in ["running", "saved"]:
            await safe_ctx.info(f"Template VM is {template_vm.get('VMState')}. Powering off before cloning.")
            
            # Force power off to ensure clean state for cloning
            stop_result = await self.stop_vm(template_name, force=True, ctx=ctx)
            
            if not stop_result["success"]:
                error_msg = stop_result.get("stderr", stop_result.get("error", "Unknown error"))
                return {"success": False, "error": f"Failed to power off template VM: {error_msg}"}
            
            # Wait for the VM to fully stop
            await asyncio.sleep(5)
            
            # Verify it's powered off
            template_info = await self.get_vm_info(template_name, ctx)
            if template_info.get("VMState") != "poweroff":
                return {"success": False, "error": "Failed to power off template VM completely"}
        
        # Try to unlock media before cloning
        await safe_ctx.info("Attempting to unlock any locked media...")
        await self.run_command(["mediaunregister", "--type", "dvd"], ctx)
        await self.run_command(["mediaunregister", "--type", "disk"], ctx)
        
        await safe_ctx.progress("Creating VM...", 10)
        
        # Try using linked clones (faster and uses less disk space)
        await safe_ctx.info("Attempting to create a linked clone...")
        clone_result = await self.run_command([
            "clonevm", template_name,
            "--name", name,
            "--register",
            "--mode", "machine",
            "--options", "link"
        ], ctx)
        
        # If linked clone fails, try regular clone
        if not clone_result["success"]:
            await safe_ctx.info("Linked clone failed, trying full clone...")
            clone_result = await self.run_command([
                "clonevm", template_name,
                "--name", name,
                "--register"
            ], ctx)
        
        # If both clone methods fail, try export/import
        if not clone_result["success"]:
            await safe_ctx.info("Clone methods failed. Trying alternative method: Export/Import...")
            
            # Export to OVA
            temp_ova = f"/tmp/{template_name}.ova"
            export_result = await self.run_command([
                "export", template_name,
                "--output", temp_ova
            ], ctx)
            
            if not export_result["success"]:
                return {"success": False, "error": f"Failed to clone VM via both methods: {clone_result.get('stderr', '')}"}
            
            # Import with new name
            import_result = await self.run_command([
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
                return {"success": False, "error": f"Failed to import VM: {import_result.get('stderr', '')}"}
        
        await safe_ctx.progress("Configuring VM settings...", 50)
        
        # Configure memory
        memory_result = await self.run_command(["modifyvm", name, "--memory", str(memory_mb)], ctx)
        if not memory_result["success"]:
            await safe_ctx.warning(f"Failed to set memory to {memory_mb}MB. Using default.")
        
        # Configure networking for Whonix
        nic_result = await self.run_command(["modifyvm", name, "--nic1", "intnet"], ctx)
        if not nic_result["success"]:
            await safe_ctx.warning("Failed to configure network adapter. Check VM settings manually.")
        
        intnet_result = await self.run_command(["modifyvm", name, "--intnet1", "Whonix"], ctx)
        if not intnet_result["success"]:
            await safe_ctx.warning("Failed to configure internal network. Check VM settings manually.")
        
        await safe_ctx.progress("VM created successfully", 100)
        
        return {
            "success": True,
            "message": f"Whonix Workstation VM '{name}' created successfully",
            "vm_name": name
        }
