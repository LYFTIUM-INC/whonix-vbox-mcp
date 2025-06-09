#!/usr/bin/env python3

"""
Test script for the secure file transfer functionality
"""

import asyncio
from file_transfer_service import FileTransferService
from virtualbox_service import VirtualBoxService

async def test_file_transfer():
    """Test the file transfer service"""
    
    # Initialize services
    vbox_service = VirtualBoxService("/usr/bin/VBoxManage")
    file_transfer = FileTransferService(vbox_service)
    
    # Test parameters
    vm_name = "Whonix-AI-Dev-Kali"
    username = "user"
    password = "changeme"
    
    print("Testing File Transfer Service")
    print("=" * 30)
    
    # Test 1: List files in VM
    print("\n1. Testing list_vm_files...")
    result = await file_transfer.list_vm_files(
        "/home/user",
        vm_name,
        username,
        password,
        recursive=False
    )
    
    if result["success"]:
        print(f"✓ Successfully listed directory")
        print(f"  Files found: {result['listing'][:200]}...")
    else:
        print(f"✗ Failed: {result['error']}")
    
    # Test 2: Upload a small test file
    print("\n2. Testing upload_file_chunked...")
    
    # Create a test file
    test_content = "This is a test file for secure MCP file transfer.\n" * 100
    test_file = "/tmp/mcp_test_upload.txt"
    
    with open(test_file, 'w') as f:
        f.write(test_content)
    
    result = await file_transfer.upload_file_chunked(
        test_file,
        vm_name,
        "/home/user/mcp_test_file.txt",
        username,
        password
    )
    
    if result["success"]:
        print(f"✓ Successfully uploaded file")
        print(f"  Size: {result['file_size']} bytes")
        print(f"  Chunks: {result['chunks_transferred']}")
        print(f"  Hash: {result['hash']}")
    else:
        print(f"✗ Failed: {result['error']}")
    
    # Test 3: Download the file back
    print("\n3. Testing download_file_chunked...")
    
    result = await file_transfer.download_file_chunked(
        "/home/user/mcp_test_file.txt",
        vm_name,
        "/tmp/mcp_test_download.txt",
        username,
        password
    )
    
    if result["success"]:
        print(f"✓ Successfully downloaded file")
        print(f"  Size: {result['file_size']} bytes")
        print(f"  Chunks: {result['chunks_transferred']}")
        print(f"  Hash: {result['hash']}")
        
        # Verify content
        with open("/tmp/mcp_test_download.txt", 'r') as f:
            downloaded_content = f.read()
        
        if downloaded_content == test_content:
            print("✓ File content verified - matches original!")
        else:
            print("✗ File content mismatch!")
    else:
        print(f"✗ Failed: {result['error']}")
    
    print("\n" + "=" * 30)
    print("File transfer tests completed!")

if __name__ == "__main__":
    # Check if VM is running first
    print("Note: Make sure the Whonix-AI-Dev-Kali VM is running before testing.")
    print("You can start it with: VBoxManage startvm Whonix-AI-Dev-Kali --type headless")
    input("\nPress Enter to continue with tests...")
    
    asyncio.run(test_file_transfer())
