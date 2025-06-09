# Secure File Transfer for VirtualBox MCP

## Overview

This implementation provides secure file transfer capabilities between the host system and VirtualBox VMs without using shared folders, addressing the security concerns of direct filesystem linkage.

## Security Benefits

1. **No Shared Folders**: Eliminates the attack vector of shared folders that directly link host and VM filesystems
2. **Chunked Transfer**: Files are transferred in small chunks (4KB by default) through VirtualBox Guest Control
3. **Base64 Encoding**: Binary data is safely encoded for transfer through command execution
4. **Integrity Verification**: SHA256 hashes ensure file integrity
5. **Temporary Files**: Uses temporary files with cleanup on failure
6. **No Persistent Connection**: Each transfer is isolated with no persistent filesystem link

## Architecture

```
Host System                    VirtualBox VM
    |                              |
    |  MCP Server                  |
    |      |                       |
    |  FileTransferService         |
    |      |                       |
    |  VBoxManage guestcontrol     |
    |      |                       |
    +------|------[Transfer]-------+
           |                       |
       No shared                Guest
       filesystem              filesystem
```

## Available Tools

### 1. upload_file_to_vm
Upload files from host to VM in secure chunks.

**Parameters:**
- `file_path`: Path to the file on the host
- `vm_name`: Name of the target VM
- `vm_destination`: Destination path in the VM
- `username`: VM username (optional, uses config default)
- `password`: VM password (optional, uses config default)

**Example:**
```python
result = await upload_file_to_vm(
    file_path="/home/user/script.sh",
    vm_name="Whonix-AI-Dev-Kali",
    vm_destination="/home/user/scripts/script.sh"
)
```

### 2. download_file_from_vm
Download files from VM to host in secure chunks.

**Parameters:**
- `vm_path`: Path to the file in the VM
- `vm_name`: Name of the source VM
- `local_destination`: Destination path on the host
- `username`: VM username (optional)
- `password`: VM password (optional)

**Example:**
```python
result = await download_file_from_vm(
    vm_path="/home/user/data/results.txt",
    vm_name="Whonix-AI-Dev-Kali",
    local_destination="/tmp/vm_results.txt"
)
```

### 3. list_vm_directory
List files in a VM directory.

**Parameters:**
- `directory`: Directory path in the VM
- `vm_name`: Name of the VM
- `recursive`: Whether to list recursively
- `username`: VM username (optional)
- `password`: VM password (optional)

**Example:**
```python
result = await list_vm_directory(
    directory="/home/user/projects",
    vm_name="Whonix-AI-Dev-Kali",
    recursive=True
)
```

## Implementation Details

### Chunk Size
- Default: 4096 bytes (4KB)
- Configurable through FileTransferService initialization
- Smaller chunks = more secure but slower
- Larger chunks = faster but may hit command length limits

### Transfer Process

1. **Upload**:
   - Create temporary file in VM
   - Read host file in chunks
   - Encode each chunk to base64
   - Transfer via guestcontrol command
   - Move to final destination
   - Verify integrity

2. **Download**:
   - Check file exists and get size
   - Read VM file in chunks using dd
   - Encode to base64 for transfer
   - Decode and write to temporary file
   - Move to final destination
   - Verify integrity

### Error Handling
- Automatic cleanup of temporary files on failure
- Progress reporting for long transfers
- Detailed error messages
- Hash verification for integrity

## Testing

Run the test script to verify functionality:

```bash
cd /home/dell/coding/mcp/vbox-whonix
python3 test_file_transfer.py
```

## Limitations

1. **Speed**: Slower than shared folders due to encoding/decoding overhead
2. **Command Length**: Very large chunks may exceed VBoxManage command limits
3. **Guest Additions Required**: VM must have Guest Additions installed and running
4. **Authentication**: Requires valid VM credentials

## Future Enhancements

1. **Compression**: Add optional compression for faster transfers
2. **Resume Support**: Allow resuming interrupted transfers
3. **Batch Operations**: Transfer multiple files efficiently
4. **Encryption**: Add optional encryption layer for sensitive files
5. **Progress Callbacks**: More detailed progress reporting

## Security Considerations

1. **Credentials**: VM credentials are passed through VBoxManage
2. **Temporary Files**: Ensure /tmp is not on a shared filesystem
3. **File Permissions**: Uploaded files get default permissions (644)
4. **Path Validation**: Implement path sanitization to prevent directory traversal

## Integration

To use the secure file transfer in your MCP server:

1. Import the service:
   ```python
   from file_transfer_service import FileTransferService
   ```

2. Initialize after VirtualBox service:
   ```python
   file_transfer_service = FileTransferService(vbox_service)
   ```

3. Add the MCP tools to your server

The implementation is already integrated in `consolidated_mcp_whonix_with_file_transfer.py`.
