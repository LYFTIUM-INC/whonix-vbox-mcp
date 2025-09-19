#!/usr/bin/env python3
"""
VM Session Management Tools for VBox-Whonix MCP
------------------------------------------------
Additional tools for managing paused VMs and locked sessions.
"""

import asyncio
from typing import Optional
from mcp.server.fastmcp import Context
from safe_context import SafeContext

async def resume_vm(vbox_service, CONFIG, ctx: Context = None, vm_name: str = "") -> str:
    """
    Resume a paused VM.
    
    Args:
        vm_name: Name of the VM to resume
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
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
            await safe_ctx.warning("VM appears to have a locked session. Attempting to unlock...")
            
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


async def unlock_vm(vbox_service, CONFIG, ctx: Context = None, vm_name: str = "", force: bool = False) -> str:
    """
    Unlock a VM session that appears to be locked.
    
    Args:
        vm_name: Name of the VM to unlock
        force: Whether to force unlock even if it might cause data loss
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
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
    
    # Method 2: Try to power off the VM (if it's stuck in a running state)
    if vm_state in ["running", "paused", "stuck"]:
        await safe_ctx.info("Attempting to power off VM...")
        poweroff_result = await vbox_service.run_command(["controlvm", vm_name, "poweroff"], ctx)
        methods_tried.append("power off")
        
        if poweroff_result["success"]:
            return f"Successfully unlocked VM '{vm_name}' by powering it off."
    
    # Method 3: Force unlock using startvm with emergency stop
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


async def get_vm_state(vbox_service, CONFIG, ctx: Context = None, vm_name: str = "") -> str:
    """
    Get detailed state information about a VM including lock status.
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        Detailed state information
    """
    safe_ctx = SafeContext(ctx)
    
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


async def discard_saved_state(vbox_service, CONFIG, ctx: Context = None, vm_name: str = "") -> str:
    """
    Discard the saved state of a VM (useful for stuck paused/saved VMs).
    
    Args:
        vm_name: Name of the VM
    
    Returns:
        Result of the operation
    """
    safe_ctx = SafeContext(ctx)
    
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