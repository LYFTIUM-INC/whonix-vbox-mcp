#!/usr/bin/env python3
"""
Browser Automation Upgrade Test Suite
Comprehensive testing of all enhanced browser automation features
"""

import json
import subprocess
import time
import os
import sys
from typing import Dict, List, Any

class BrowserUpgradeTestSuite:
    def __init__(self):
        """Initialize test suite"""
        self.vm_name = "Whonix-Workstation-Xfce"
        self.test_results = []
        self.start_time = time.time()
        
        # Test URLs (safe test sites)
        self.test_urls = [
            "https://httpbin.org/get",  # Simple HTTP testing
            "https://httpbin.org/forms/post",  # Form testing
            "https://example.com",  # Basic site
            "https://www.wikipedia.org",  # Complex site
            "https://duckduckgo.com"  # Search engine
        ]
        
        # Test queries
        self.test_queries = [
            "python programming",
            "web scraping tutorial",
            "tor browser security"
        ]
    
    def log_result(self, test_name: str, success: bool, details: Dict = None, error: str = None):
        """Log test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'timestamp': time.time(),
            'details': details or {},
            'error': error
        }
        self.test_results.append(result)
        
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status} {test_name}")
        if error:
            print(f"    Error: {error}")
        if details:
            print(f"    Details: {json.dumps(details, indent=2)}")
    
    def run_vm_command(self, command: str, timeout: int = 60) -> Dict:
        """Execute command in VM"""
        try:
            cmd = [
                'python3', '/home/dell/coding/mcp/vbox-whonix/consolidated_mcp_whonix.py',
                'execute_vm_command',
                self.vm_name,
                command
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {'success': False, 'error': 'Invalid JSON response'}
            else:
                return {
                    'success': False, 
                    'error': result.stderr or 'Command failed',
                    'stdout': result.stdout
                }
                
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': f'Command timeout after {timeout}s'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def test_python_module_imports(self):
        """Test that all enhanced modules import correctly"""
        modules = [
            'enhanced_search_api',
            'form_handler', 
            'session_manager',
            'stealth_browser',
            'content_extractor',
            'parallel_processor',
            'browser_api_v2'
        ]
        
        for module in modules:
            cmd = f"cd /home/user/browser_automation && python3 -c 'import {module}; print(\"OK\")'"
            result = self.run_vm_command(cmd)
            
            success = result.get('success', False) and 'OK' in result.get('stdout', '')
            self.log_result(f"Import {module}", success, 
                          {'module': module}, 
                          result.get('error') if not success else None)
    
    def test_enhanced_search_api(self):
        """Test enhanced search functionality"""
        for query in self.test_queries[:2]:  # Test first 2 queries
            cmd = f"cd /home/user/browser_automation && python3 enhanced_search_api.py '{query}' 5"
            result = self.run_vm_command(cmd, timeout=120)
            
            success = False
            details = {}
            
            if result.get('success'):
                try:
                    output = json.loads(result.get('stdout', '{}'))
                    success = output.get('success', False) and len(output.get('results', [])) > 0
                    details = {
                        'results_count': len(output.get('results', [])),
                        'query': query,
                        'total_time': output.get('response_time', 0)
                    }
                except:
                    success = False
            
            self.log_result(f"Enhanced Search: {query[:20]}...", success, details,
                          result.get('error') if not success else None)
    
    def test_stealth_browser(self):
        """Test stealth browser functionality"""
        test_url = "https://httpbin.org/user-agent"
        
        cmd = f"cd /home/user/browser_automation && python3 stealth_browser.py request '{test_url}'"
        result = self.run_vm_command(cmd, timeout=90)
        
        success = False
        details = {}
        
        if result.get('success'):
            try:
                output = json.loads(result.get('stdout', '{}'))
                success = output.get('success', False) and output.get('status_code', 0) == 200
                details = {
                    'status_code': output.get('status_code'),
                    'response_time': output.get('response_time'),
                    'content_length': output.get('content_length', 0),
                    'user_agent_detected': 'Mozilla' in output.get('content_preview', '')
                }
            except:
                success = False
        
        self.log_result("Stealth Browser Request", success, details,
                      result.get('error') if not success else None)
    
    def test_content_extractor(self):
        """Test content extraction capabilities"""
        # First get some HTML content
        test_url = "https://example.com"
        
        # Fetch content using stealth browser
        cmd = f"cd /home/user/browser_automation && python3 stealth_browser.py request '{test_url}'"
        fetch_result = self.run_vm_command(cmd, timeout=90)
        
        if not fetch_result.get('success'):
            self.log_result("Content Extractor", False, {}, "Failed to fetch test content")
            return
        
        # Save content to temp file and extract
        cmd = """cd /home/user/browser_automation && python3 -c "
import json
import stealth_browser
browser = stealth_browser.StealthBrowser()
result = browser.make_stealth_request('https://example.com')
if result['success']:
    with open('/tmp/test_content.html', 'w') as f:
        f.write(result['content'])
    print('Content saved')
else:
    print('Failed to fetch')
" """
        
        save_result = self.run_vm_command(cmd, timeout=60)
        
        if save_result.get('success') and 'Content saved' in save_result.get('stdout', ''):
            # Now test extraction
            extract_cmd = "cd /home/user/browser_automation && python3 content_extractor.py /tmp/test_content.html"
            extract_result = self.run_vm_command(extract_cmd, timeout=60)
            
            success = False
            details = {}
            
            if extract_result.get('success'):
                try:
                    output = json.loads(extract_result.get('stdout', '{}'))
                    success = output.get('success', False)
                    if success:
                        extracted = output.get('extracted', {})
                        details = {
                            'title_found': bool(extracted.get('metadata', {}).get('title')),
                            'links_found': len(extracted.get('links', [])),
                            'text_length': len(extracted.get('text', '')),
                            'forms_found': len(extracted.get('forms', []))
                        }
                except:
                    success = False
            
            self.log_result("Content Extractor", success, details,
                          extract_result.get('error') if not success else None)
        else:
            self.log_result("Content Extractor", False, {}, "Failed to save test content")
    
    def test_session_manager(self):
        """Test session management functionality"""
        session_id = f"test_session_{int(time.time())}"
        
        # Create session
        cmd = f"cd /home/user/browser_automation && python3 session_manager.py create {session_id}"
        create_result = self.run_vm_command(cmd, timeout=60)
        
        success = False
        details = {'session_id': session_id}
        
        if create_result.get('success'):
            try:
                output = json.loads(create_result.get('stdout', '{}'))
                success = output.get('success', False)
                
                if success:
                    # Test session request
                    req_cmd = f"cd /home/user/browser_automation && python3 session_manager.py request {session_id} https://httpbin.org/get"
                    req_result = self.run_vm_command(req_cmd, timeout=90)
                    
                    if req_result.get('success'):
                        try:
                            req_output = json.loads(req_result.get('stdout', '{}'))
                            details['request_success'] = req_output.get('success', False)
                            details['status_code'] = req_output.get('status_code', 0)
                        except:
                            details['request_success'] = False
                    
                    # Cleanup
                    cleanup_cmd = f"cd /home/user/browser_automation && python3 session_manager.py delete {session_id}"
                    self.run_vm_command(cleanup_cmd, timeout=30)
                    
            except:
                success = False
        
        self.log_result("Session Manager", success, details,
                      create_result.get('error') if not success else None)
    
    def test_browser_api_v2_status(self):
        """Test unified Browser API v2 status check"""
        cmd = "cd /home/user/browser_automation && python3 browser_api_v2.py status"
        result = self.run_vm_command(cmd, timeout=120)
        
        success = False
        details = {}
        
        if result.get('success'):
            try:
                output = json.loads(result.get('stdout', '{}'))
                success = output.get('success', False)
                if success:
                    components = output.get('components', {})
                    capabilities = output.get('capabilities', {})
                    details = {
                        'version': output.get('version'),
                        'components_count': len(components),
                        'capabilities_count': len([k for k, v in capabilities.items() if v]),
                        'enhanced_search': components.get('enhanced_search', {}).get('status') == 'operational',
                        'form_handler': components.get('form_handler', {}).get('status') == 'operational',
                        'session_manager': components.get('session_manager', {}).get('status') == 'operational'
                    }
            except:
                success = False
        
        self.log_result("Browser API v2 Status", success, details,
                      result.get('error') if not success else None)
    
    def test_browser_api_v2_search(self):
        """Test unified API search functionality"""
        test_query = "python programming"
        
        cmd = f"cd /home/user/browser_automation && python3 browser_api_v2.py search '{test_query}' 3"
        result = self.run_vm_command(cmd, timeout=120)
        
        success = False
        details = {'query': test_query}
        
        if result.get('success'):
            try:
                output = json.loads(result.get('stdout', '{}'))
                success = output.get('success', False) and len(output.get('results', [])) > 0
                details.update({
                    'results_count': len(output.get('results', [])),
                    'api_version': output.get('api_version'),
                    'enhancement': output.get('enhancement', '')
                })
            except:
                success = False
        
        self.log_result("Browser API v2 Search", success, details,
                      result.get('error') if not success else None)
    
    def test_parallel_processor(self):
        """Test parallel processing functionality"""
        test_urls = ",".join(self.test_urls[:3])  # Test first 3 URLs
        
        cmd = f"cd /home/user/browser_automation && python3 parallel_processor.py fetch '{test_urls}' 3"
        result = self.run_vm_command(cmd, timeout=180)
        
        success = False
        details = {}
        
        if result.get('success'):
            try:
                output = json.loads(result.get('stdout', '{}'))
                success = output.get('success', False)
                details = {
                    'total_urls': output.get('total', 0),
                    'successful': output.get('successful', 0),
                    'failed': output.get('failed', 0),
                    'processing_time': output.get('processing_time', 0),
                    'average_time': output.get('average_time_per_url', 0)
                }
            except:
                success = False
        
        self.log_result("Parallel Processor", success, details,
                      result.get('error') if not success else None)
    
    def test_form_handler(self):
        """Test form handling capabilities"""
        # Test form analysis on a site with forms
        test_url = "https://httpbin.org/forms/post"
        
        cmd = f"cd /home/user/browser_automation && python3 browser_api_v2.py forms '{test_url}'"
        result = self.run_vm_command(cmd, timeout=90)
        
        success = False
        details = {'test_url': test_url}
        
        if result.get('success'):
            try:
                output = json.loads(result.get('stdout', '{}'))
                success = output.get('success', False)
                details.update({
                    'forms_found': output.get('forms_found', 0),
                    'api_version': output.get('api_version')
                })
            except:
                success = False
        
        self.log_result("Form Handler", success, details,
                      result.get('error') if not success else None)
    
    def run_performance_benchmark(self):
        """Run performance comparison between old and new APIs"""
        print("\n=== Performance Benchmark ===")
        
        # Test old API
        old_cmd = "cd /home/user/browser_automation && python3 working_browser_api.py search 'test query' 3"
        old_start = time.time()
        old_result = self.run_vm_command(old_cmd, timeout=90)
        old_time = time.time() - old_start
        
        # Test new API  
        new_cmd = "cd /home/user/browser_automation && python3 browser_api_v2.py search 'test query' 3"
        new_start = time.time()
        new_result = self.run_vm_command(new_cmd, timeout=90)
        new_time = time.time() - new_start
        
        benchmark = {
            'old_api_time': old_time,
            'new_api_time': new_time,
            'improvement_ratio': old_time / new_time if new_time > 0 else 0,
            'old_api_success': old_result.get('success', False),
            'new_api_success': new_result.get('success', False)
        }
        
        self.log_result("Performance Benchmark", True, benchmark)
        return benchmark
    
    def generate_report(self):
        """Generate comprehensive test report"""
        total_time = time.time() - self.start_time
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_time': total_time
            },
            'test_results': self.test_results,
            'timestamp': time.time(),
            'vm_name': self.vm_name
        }
        
        # Save report
        report_file = f"browser_upgrade_test_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n=== TEST SUMMARY ===")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {report['test_summary']['success_rate']:.1f}%")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Report saved: {report_file}")
        
        return report
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=== Browser Automation Upgrade Test Suite ===")
        print(f"Testing VM: {self.vm_name}")
        print(f"Start time: {time.ctime()}")
        print()
        
        # Module import tests
        print("--- Module Import Tests ---")
        self.test_python_module_imports()
        
        # Component functionality tests
        print("\n--- Component Functionality Tests ---")
        self.test_enhanced_search_api()
        self.test_stealth_browser()
        self.test_content_extractor()
        self.test_session_manager()
        self.test_form_handler()
        
        # Unified API tests
        print("\n--- Unified API Tests ---")
        self.test_browser_api_v2_status()
        self.test_browser_api_v2_search()
        
        # Advanced functionality tests
        print("\n--- Advanced Functionality Tests ---")
        self.test_parallel_processor()
        
        # Performance benchmark
        benchmark = self.run_performance_benchmark()
        
        # Generate final report
        report = self.generate_report()
        
        return report


def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        # Quick test mode - just essential tests
        suite = BrowserUpgradeTestSuite()
        suite.test_python_module_imports()
        suite.test_browser_api_v2_status()
        suite.test_enhanced_search_api()
        report = suite.generate_report()
    else:
        # Full test suite
        suite = BrowserUpgradeTestSuite()
        report = suite.run_all_tests()
    
    # Exit with non-zero code if tests failed
    if report['test_summary']['success_rate'] < 100:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()