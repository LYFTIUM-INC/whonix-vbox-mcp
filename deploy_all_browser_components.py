#!/usr/bin/env python3
"""
Deploy All Browser API v2 Components to VM
Rapid deployment script for testing
"""

import subprocess
import time
import os

def upload_file_to_vm(file_path, vm_destination):
    """Upload file to VM using VBoxManage"""
    try:
        # Copy file to VM
        cmd = [
            'VBoxManage', 'guestcontrol', 'Whonix-Workstation-Xfce',
            '--username', 'user', '--password', 'changeme',
            'copyto', '--target-directory', '/home/user/browser_automation/',
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Uploaded: {os.path.basename(file_path)}")
            return True
        else:
            print(f"❌ Failed to upload {file_path}: {result.stderr}")
            return False
    except Exception as e:
        print(f"💥 Error uploading {file_path}: {e}")
        return False

def main():
    print("🚀 Deploying Browser API v2 Components to VM")
    print("=" * 50)
    
    # Create browser_automation directory in VM
    try:
        cmd = [
            'VBoxManage', 'guestcontrol', 'Whonix-Workstation-Xfce',
            '--username', 'user', '--password', 'changeme',
            'mkdir', '--parents', '/home/user/browser_automation'
        ]
        subprocess.run(cmd, capture_output=True)
        print("📁 Created /home/user/browser_automation directory")
    except:
        print("📁 Directory may already exist")
    
    # Files to deploy
    files_to_deploy = [
        'browser_api_v2.py',
        'enhanced_search_api.py',
        'form_handler.py',
        'session_manager.py',
        'stealth_browser.py',
        'content_extractor.py',
        'parallel_processor.py'
    ]
    
    # Deploy each file
    successful_uploads = 0
    total_files = len(files_to_deploy)
    
    for file_name in files_to_deploy:
        file_path = f"/home/dell/coding/mcp/vbox-whonix/{file_name}"
        if os.path.exists(file_path):
            if upload_file_to_vm(file_path, f"/home/user/browser_automation/{file_name}"):
                successful_uploads += 1
        else:
            print(f"❌ File not found: {file_path}")
    
    print("=" * 50)
    print(f"📊 Deployment Summary:")
    print(f"   ✅ Successful: {successful_uploads}/{total_files}")
    print(f"   ❌ Failed: {total_files - successful_uploads}/{total_files}")
    
    if successful_uploads == total_files:
        print("🎉 All components deployed successfully!")
        
        # Install dependencies
        print("\n🔧 Installing Python dependencies...")
        cmd = [
            'VBoxManage', 'guestcontrol', 'Whonix-Workstation-Xfce',
            '--username', 'user', '--password', 'changeme',
            'run', '--exe', '/usr/bin/python3',
            '--', '-m', 'pip', 'install', '--user', '--break-system-packages',
            'duckduckgo-search', 'beautifulsoup4', 'html2text', 'requests[socks]'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Dependencies installed successfully!")
        else:
            print(f"⚠️ Dependency installation may have issues: {result.stderr}")
        
        return True
    else:
        print("❌ Deployment incomplete!")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)