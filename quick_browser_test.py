#!/usr/bin/env python3
"""Quick Browser API v2 Test"""

import subprocess
import json
import time

def test_mcp_function(function_name, *args):
    """Test single MCP function"""
    try:
        start_time = time.time()
        
        cmd = [
            'python3',
            '/home/dell/coding/mcp/vbox-whonix/consolidated_mcp_whonix_with_file_transfer.py',
            function_name,
            'Whonix-Workstation-Xfce',
            *args
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        duration = time.time() - start_time
        
        print(f"🔍 Testing: {function_name}")
        print(f"⏱️  Duration: {duration:.1f}s")
        print(f"🔄 Return Code: {result.returncode}")
        
        if result.stdout:
            print("📤 STDOUT:")
            lines = result.stdout.strip().split('\n')
            for line in lines[-10:]:  # Last 10 lines
                if line.strip():
                    print(f"   {line}")
        
        if result.stderr:
            print("📥 STDERR:")
            lines = result.stderr.strip().split('\n')
            for line in lines[-5:]:  # Last 5 lines
                if line.strip():
                    print(f"   {line}")
        
        print("-" * 50)
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"❌ {function_name} timed out after 60s")
        return False
    except Exception as e:
        print(f"💥 Error testing {function_name}: {e}")
        return False

def main():
    print("🚀 Quick Browser API v2 Test")
    print("=" * 50)
    
    tests = [
        ('browser_automation_status_check',),
        ('browser_intelligent_search', 'python tutorial'),
    ]
    
    for test_args in tests:
        test_mcp_function(*test_args)
        time.sleep(2)  # Brief pause between tests

if __name__ == '__main__':
    main()