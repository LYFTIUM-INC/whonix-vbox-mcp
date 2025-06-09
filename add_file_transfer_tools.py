#!/usr/bin/env python3

"""
Add File Transfer Tools to Consolidated MCP Module
-------------------------------------------------
This script adds secure file transfer capabilities to the existing MCP server.
"""

# This file contains the MCP tool definitions to add to consolidated_mcp_whonix.py

FILE_TRANSFER_TOOLS = '''

# Import the file transfer service
from file_transfer_service import FileTransferService

# Initialize the file transfer service
file_transfer_service = FileTransferService(vbox_service)

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
        return (f"Successfully uploaded file to VM:\\n\\n"
                f"File: {file_path}\\n"
                f"Destination: {vm_destination}\\n"
                f"Size: {result['file_size']} bytes\\n"
                f"Chunks: {result['chunks_transferred']}\\n"
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
        return (f"Successfully downloaded file from VM:\\n\\n"
                f"Source: {vm_path}\\n"
                f"Destination: {local_destination}\\n"
                f"Size: {result['file_size']} bytes\\n"
                f"Chunks: {result['chunks_transferred']}\\n"
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
        return (f"Directory listing ({mode}) for {directory}:\\n\\n"
                f"{result['listing']}")
    else:
        return f"Failed to list directory: {result['error']}"
'''

if __name__ == "__main__":
    print("File transfer tools code has been generated.")
    print("To integrate these tools into consolidated_mcp_whonix.py:")
    print("1. Add 'from file_transfer_service import FileTransferService' to imports")
    print("2. Add 'file_transfer_service = FileTransferService(vbox_service)' after vbox_service initialization")
    print("3. Add the tool functions to the main file")
