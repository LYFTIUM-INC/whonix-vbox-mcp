#!/usr/bin/env python3

"""
Secure File Transfer Service for VirtualBox MCP
----------------------------------------------
This module provides secure file transfer capabilities between host and VM
without using shared folders, implementing chunked transfers and validation.
"""

import asyncio
import base64
import hashlib
import json
import os
import tempfile
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FileTransferService:
    """Service for secure file transfers between host and VirtualBox VMs."""
    
    def __init__(self, vbox_service, chunk_size: int = 4096):
        """
        Initialize the file transfer service.
        
        Args:
            vbox_service: VirtualBoxService instance for executing commands
            chunk_size: Size of chunks for file transfer (default: 4KB)
        """
        self.vbox_service = vbox_service
        self.chunk_size = chunk_size
        self.transfer_sessions = {}  # Track ongoing transfers
        
    async def _execute_in_vm(self, vm_name: str, command: str, username: str, password: str, ctx=None) -> Dict[str, Any]:
        """Execute a command in the VM and return the result."""
        guest_cmd = [
            "guestcontrol", vm_name,
            "run", "--username", username,
            "--password", password,
            "--wait-stdout", "--wait-stderr",
            "--", "/bin/bash", "-c", command
        ]
        return await self.vbox_service.run_command(guest_cmd, ctx)
    
    async def upload_file_chunked(self, 
                                 file_path: str, 
                                 vm_name: str, 
                                 vm_destination: str,
                                 username: str,
                                 password: str,
                                 ctx=None) -> Dict[str, Any]:
        """
        Upload a file to VM in chunks with progress reporting.
        
        Args:
            file_path: Path to the file on the host
            vm_name: Name of the target VM
            vm_destination: Destination path in the VM
            username: VM username
            password: VM password
            ctx: MCP context for progress reporting
            
        Returns:
            Dict with success status and details
        """
        if not os.path.exists(file_path):
            return {"success": False, "error": f"File not found: {file_path}"}
        
        file_size = os.path.getsize(file_path)
        file_hash = hashlib.sha256()
        
        # Create a temporary file in VM first
        temp_command = "mktemp /tmp/mcp_transfer_XXXXXX"
        temp_result = await self._execute_in_vm(vm_name, temp_command, username, password, ctx)
        
        if not temp_result["success"]:
            return {"success": False, "error": "Failed to create temporary file in VM"}
            
        temp_path = temp_result.get("stdout", "").strip()
        
        try:
            # Read and transfer file in chunks
            with open(file_path, 'rb') as f:
                chunk_num = 0
                total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
                
                while True:
                    chunk = f.read(self.chunk_size)
                    if not chunk:
                        break
                    
                    # Update hash
                    file_hash.update(chunk)
                    
                    # Encode chunk to base64 for safe transfer
                    encoded_chunk = base64.b64encode(chunk).decode('ascii')
                    
                    # Write chunk to temporary file in VM
                    command = f"echo '{encoded_chunk}' | base64 -d >> {temp_path}"
                    
                    result = await self._execute_in_vm(vm_name, command, username, password, ctx)
                    if not result["success"]:
                        # Clean up temp file
                        await self._execute_in_vm(vm_name, f"rm -f {temp_path}", username, password, ctx)
                        return {"success": False, "error": f"Failed to write chunk {chunk_num}"}
                    
                    chunk_num += 1
                    
                    # Report progress
                    if ctx and hasattr(ctx, 'progress'):
                        progress = int((chunk_num / total_chunks) * 100)
                        await ctx.progress(f"Uploading file: {progress}%", progress)
            
            # Move file to final destination
            move_command = f"mv {temp_path} {vm_destination}"
            move_result = await self._execute_in_vm(vm_name, move_command, username, password, ctx)
            
            if not move_result["success"]:
                await self._execute_in_vm(vm_name, f"rm -f {temp_path}", username, password, ctx)
                return {"success": False, "error": "Failed to move file to destination"}
            
            return {
                "success": True,
                "file_size": file_size,
                "chunks_transferred": chunk_num,
                "hash": file_hash.hexdigest(),
                "destination": vm_destination
            }
            
        except Exception as e:
            # Clean up temp file on error
            await self._execute_in_vm(vm_name, f"rm -f {temp_path}", username, password, ctx)
            return {"success": False, "error": f"Transfer failed: {str(e)}"}
    
    async def download_file_chunked(self,
                                  vm_path: str,
                                  vm_name: str,
                                  local_destination: str,
                                  username: str,
                                  password: str,
                                  ctx=None) -> Dict[str, Any]:
        """
        Download a file from VM in chunks with progress reporting.
        
        Args:
            vm_path: Path to the file in the VM
            vm_name: Name of the source VM
            local_destination: Destination path on the host
            username: VM username
            password: VM password
            ctx: MCP context for progress reporting
            
        Returns:
            Dict with success status and details
        """
        # First, check if file exists and get its size
        stat_command = f"stat -c '%s' {vm_path} 2>/dev/null"
        stat_result = await self._execute_in_vm(vm_name, stat_command, username, password, ctx)
        
        if not stat_result["success"] or not stat_result.get("stdout", "").strip():
            return {"success": False, "error": f"File not found in VM: {vm_path}"}
        
        try:
            file_size = int(stat_result.get("stdout", "").strip())
        except ValueError:
            return {"success": False, "error": "Failed to get file size"}
        
        # Create temporary file for download
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='wb')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            local_hash = hashlib.sha256()
            offset = 0
            chunk_num = 0
            total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
            
            with open(temp_path, 'wb') as f:
                while offset < file_size:
                    # Read chunk from VM file
                    read_size = min(self.chunk_size, file_size - offset)
                    read_command = f"dd if={vm_path} bs=1 skip={offset} count={read_size} 2>/dev/null | base64 -w 0"
                    
                    result = await self._execute_in_vm(vm_name, read_command, username, password, ctx)
                    
                    if not result["success"]:
                        return {"success": False, "error": f"Failed to read chunk at offset {offset}"}
                    
                    # Decode and write chunk
                    encoded_chunk = result.get("stdout", "").strip()
                    if not encoded_chunk:
                        break
                    
                    try:
                        chunk = base64.b64decode(encoded_chunk)
                        f.write(chunk)
                        local_hash.update(chunk)
                        offset += len(chunk)
                        chunk_num += 1
                        
                        # Report progress
                        if ctx and hasattr(ctx, 'progress'):
                            progress = int((chunk_num / total_chunks) * 100)
                            await ctx.progress(f"Downloading file: {progress}%", progress)
                            
                    except Exception as e:
                        return {"success": False, "error": f"Failed to decode chunk: {str(e)}"}
            
            # Move to final destination
            os.makedirs(os.path.dirname(local_destination), exist_ok=True)
            os.rename(temp_path, local_destination)
            
            return {
                "success": True,
                "file_size": file_size,
                "chunks_transferred": chunk_num,
                "hash": local_hash.hexdigest(),
                "destination": local_destination
            }
            
        except Exception as e:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            return {"success": False, "error": f"Download failed: {str(e)}"}
    
    async def list_vm_files(self,
                          directory: str,
                          vm_name: str,
                          username: str,
                          password: str,
                          recursive: bool = False,
                          ctx=None) -> Dict[str, Any]:
        """
        List files in a VM directory.
        
        Args:
            directory: Directory path in the VM
            vm_name: Name of the VM
            username: VM username
            password: VM password
            recursive: Whether to list recursively
            ctx: MCP context
            
        Returns:
            Dict with file listing
        """
        # Build ls command with appropriate options
        ls_options = "-la"
        if recursive:
            ls_options += "R"
        
        command = f"ls {ls_options} {directory} 2>/dev/null"
        result = await self._execute_in_vm(vm_name, command, username, password, ctx)
        
        if not result["success"]:
            return {"success": False, "error": "Failed to list directory"}
        
        return {
            "success": True,
            "directory": directory,
            "listing": result.get("stdout", ""),
            "recursive": recursive
        }
