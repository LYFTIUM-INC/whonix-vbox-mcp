#!/usr/bin/env python3
"""Direct VM Browser API Test"""

import subprocess
import json
import time

def execute_vm_command(command):
    """Execute command directly in VM"""
    try:
        start_time = time.time()
        
        cmd = [
            'VBoxManage', 'guestcontrol', 'Whonix-Workstation-Xfce',
            '--username', 'user', '--password', 'changeme',
            'run', '--exe', '/bin/bash',
            '--', '-c', command
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        duration = time.time() - start_time
        
        return {
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'duration': 120,
            'error': 'Timeout after 120s'
        }
    except Exception as e:
        return {
            'success': False,
            'duration': 0,
            'error': str(e)
        }

def test_browser_api_status():
    """Test browser API v2 status"""
    print("🔍 Testing Browser API v2 Status")
    
    command = "cd /home/user/browser_automation && python3 browser_api_v2.py status"
    result = execute_vm_command(command)
    
    print(f"⏱️  Duration: {result['duration']:.1f}s")
    print(f"✅ Success: {result['success']}")
    
    if result.get('stdout'):
        print("📤 Output:")
        try:
            # Try to parse JSON
            data = json.loads(result['stdout'])
            print(f"   API Version: {data.get('version', 'Unknown')}")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Components: {len(data.get('components', {}))}")
            components = data.get('components', {})
            for name, info in components.items():
                status = info.get('status', 'unknown')
                print(f"     • {name}: {status}")
        except:
            # Print raw output
            for line in result['stdout'].strip().split('\n')[:10]:
                if line.strip():
                    print(f"   {line}")
    
    if result.get('stderr'):
        print("📥 Errors:")
        for line in result['stderr'].strip().split('\n')[:5]:
            if line.strip():
                print(f"   {line}")
    
    print("-" * 50)
    return result['success']

def test_enhanced_search():
    """Test enhanced search API"""
    print("🔍 Testing Enhanced Search API")
    
    command = "cd /home/user/browser_automation && python3 browser_api_v2.py search 'python tutorial' 3"
    result = execute_vm_command(command)
    
    print(f"⏱️  Duration: {result['duration']:.1f}s")
    print(f"✅ Success: {result['success']}")
    
    if result.get('stdout'):
        print("📤 Search Results:")
        try:
            # Try to parse JSON
            data = json.loads(result['stdout'])
            print(f"   Query: {data.get('query', 'N/A')}")
            print(f"   Total Results: {data.get('total', 0)}")
            print(f"   Success: {data.get('success', False)}")
            
            results = data.get('results', [])
            if results:
                print(f"   First Result:")
                first = results[0]
                print(f"     Title: {first.get('title', 'N/A')[:50]}...")
                print(f"     URL: {first.get('href', 'N/A')[:50]}...")
            else:
                print("   No results returned")
        except:
            # Print raw output
            for line in result['stdout'].strip().split('\n')[:10]:
                if line.strip():
                    print(f"   {line}")
    
    if result.get('stderr'):
        print("📥 Errors:")
        for line in result['stderr'].strip().split('\n')[:5]:
            if line.strip():
                print(f"   {line}")
    
    print("-" * 50)
    return result['success']

def test_stealth_browser():
    """Test stealth browser"""
    print("🔍 Testing Stealth Browser")
    
    command = "cd /home/user/browser_automation && python3 stealth_browser.py request 'https://httpbin.org/get'"
    result = execute_vm_command(command)
    
    print(f"⏱️  Duration: {result['duration']:.1f}s")
    print(f"✅ Success: {result['success']}")
    
    if result.get('stdout'):
        print("📤 Stealth Request:")
        try:
            # Try to parse JSON
            data = json.loads(result['stdout'])
            print(f"   Success: {data.get('success', False)}")
            print(f"   Status Code: {data.get('status_code', 0)}")
            print(f"   Response Time: {data.get('response_time', 0):.2f}s")
            print(f"   Content Size: {data.get('content_size', 0)} bytes")
            print(f"   User Agent: {data.get('user_agent', 'Unknown')[:60]}...")
        except:
            # Print raw output
            for line in result['stdout'].strip().split('\n')[:10]:
                if line.strip():
                    print(f"   {line}")
    
    if result.get('stderr'):
        print("📥 Errors:")
        for line in result['stderr'].strip().split('\n')[:5]:
            if line.strip():
                print(f"   {line}")
    
    print("-" * 50)
    return result['success']

def main():
    print("🚀 Direct VM Browser API Testing")
    print("=" * 60)
    
    # Check if files exist
    print("📁 Checking Deployed Files")
    command = "ls -la /home/user/browser_automation/*.py | head -10"
    result = execute_vm_command(command)
    
    if result['success'] and result['stdout']:
        files = result['stdout'].strip().split('\n')
        print(f"   Found {len(files)} Python files:")
        for file_line in files[:7]:  # Show first 7
            if '.py' in file_line:
                filename = file_line.split()[-1].split('/')[-1]
                print(f"     ✓ {filename}")
    else:
        print("   ❌ Could not list files")
    
    print("-" * 60)
    
    # Run tests
    tests = [
        ("Browser API v2 Status", test_browser_api_status),
        ("Enhanced Search", test_enhanced_search),
        ("Stealth Browser", test_stealth_browser)
    ]
    
    results = []
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
        time.sleep(2)  # Brief pause
    
    # Summary
    print("=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests successful!")
    else:
        print("⚠️  Some tests failed - check logs above")

if __name__ == '__main__':
    main()