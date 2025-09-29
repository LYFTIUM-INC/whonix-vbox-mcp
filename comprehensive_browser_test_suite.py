#!/usr/bin/env python3
"""
Comprehensive Browser Automation Test Suite
Tests all new browser_api_v2 tools through MCP interface
"""

import json
import subprocess
import time
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveBrowserTestSuite:
    def __init__(self):
        self.vm_name = "Whonix-Workstation-Xfce"
        self.start_time = time.time()
        self.test_results = []
        
        # Test configuration
        self.test_queries = [
            "python programming tutorial",
            "cybersecurity best practices", 
            "tor browser usage guide"
        ]
        
        self.test_urls = [
            "https://httpbin.org/get",
            "https://example.com",
            "https://httpbin.org/user-agent"
        ]
        
        print(f"🚀 Starting Comprehensive Browser Automation Test Suite")
        print(f"📅 Start Time: {datetime.now()}")
        print(f"🖥️  VM: {self.vm_name}")
        print("=" * 60)
    
    def log_test_result(self, test_name: str, success: bool, duration: float, details: Dict = None, error: str = None):
        """Log individual test result"""
        result = {
            'test_name': test_name,
            'success': success,
            'duration_seconds': round(duration, 2),
            'timestamp': datetime.now().isoformat(),
            'details': details or {},
            'error': error
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.1f}s)")
        if error:
            print(f"    💥 Error: {error}")
        if details:
            for key, value in details.items():
                print(f"    📊 {key}: {value}")
        print()
    
    def execute_mcp_function(self, function_name: str, *args, timeout: int = 120) -> Dict:
        """Execute MCP function and return parsed result"""
        try:
            # Build command to call MCP function
            cmd = [
                'python3', 
                '/home/dell/coding/mcp/vbox-whonix/consolidated_mcp_whonix_with_file_transfer.py',
                function_name,
                self.vm_name,
                *args
            ]
            
            start_time = time.time()
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout
            )
            duration = time.time() - start_time
            
            if result.returncode == 0:
                try:
                    # Try to parse JSON from stdout
                    output_lines = result.stdout.strip().split('\n')
                    json_line = None
                    
                    # Find JSON response in output
                    for line in reversed(output_lines):
                        if line.strip().startswith('{') and line.strip().endswith('}'):
                            json_line = line.strip()
                            break
                    
                    if json_line:
                        parsed = json.loads(json_line)
                        return {
                            'success': True,
                            'duration': duration,
                            'data': parsed,
                            'stdout': result.stdout,
                            'stderr': result.stderr
                        }
                    else:
                        return {
                            'success': True,
                            'duration': duration,
                            'data': {'raw_output': result.stdout},
                            'stdout': result.stdout,
                            'stderr': result.stderr
                        }
                        
                except json.JSONDecodeError:
                    return {
                        'success': True,  # Command succeeded but no JSON
                        'duration': duration,
                        'data': {'raw_output': result.stdout},
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
            else:
                return {
                    'success': False,
                    'duration': duration,
                    'error': result.stderr or 'Command failed',
                    'stdout': result.stdout,
                    'stderr': result.stderr
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'duration': timeout,
                'error': f'Command timeout after {timeout}s'
            }
        except Exception as e:
            return {
                'success': False,
                'duration': 0,
                'error': str(e)
            }
    
    def test_browser_automation_status_check(self):
        """Test 1: Browser automation status check"""
        print("🔍 Test 1: Browser Automation Status Check")
        
        result = self.execute_mcp_function('browser_automation_status_check')
        
        success = result.get('success', False)
        details = {}
        error = result.get('error')
        
        if success and result.get('data'):
            data = result.get('data', {})
            if isinstance(data, dict):
                details = {
                    'components_reported': len(data.get('components', {})),
                    'api_version': data.get('version', 'Unknown'),
                    'capabilities': len(data.get('capabilities', {})),
                }
                # Check if it's using the new API
                if 'browser_api_v2' in str(data):
                    details['using_new_api'] = True
                else:
                    details['using_new_api'] = False
        
        self.log_test_result(
            "Browser Status Check", 
            success, 
            result.get('duration', 0),
            details, 
            error
        )
        
        return success
    
    def test_browser_intelligent_search(self):
        """Test 2: Browser intelligent search"""
        print("🔍 Test 2: Browser Intelligent Search")
        
        test_results = []
        
        for i, query in enumerate(self.test_queries[:2], 1):  # Test first 2 queries
            print(f"  🔎 Search {i}: '{query}'")
            
            result = self.execute_mcp_function('browser_intelligent_search', query)
            
            success = result.get('success', False)
            details = {'query': query}
            error = result.get('error')
            
            if success and result.get('data'):
                data = result.get('data', {})
                if isinstance(data, dict):
                    # Check for search results
                    results = data.get('results', [])
                    if isinstance(results, list):
                        details['results_count'] = len(results)
                        details['has_real_results'] = len(results) > 0
                        
                        # Check if results have titles and URLs (not just redirects)
                        if results:
                            first_result = results[0] if results else {}
                            details['has_titles'] = 'title' in first_result
                            details['has_urls'] = 'href' in first_result or 'url' in first_result
                            details['result_quality'] = 'high' if details['has_titles'] and details['has_urls'] else 'low'
                    
                    # Check for success indicators
                    details['api_success'] = data.get('success', False)
                    details['total_results'] = data.get('total', 0)
            
            self.log_test_result(
                f"Search Query: {query[:30]}...",
                success,
                result.get('duration', 0),
                details,
                error
            )
            
            test_results.append(success)
        
        return all(test_results)
    
    def test_browser_capture_page_screenshot(self):
        """Test 3: Browser page capture"""
        print("🔍 Test 3: Browser Page Capture")
        
        test_results = []
        
        for i, url in enumerate(self.test_urls[:2], 1):  # Test first 2 URLs
            print(f"  📸 Capture {i}: {url}")
            
            result = self.execute_mcp_function('browser_capture_page_screenshot', url)
            
            success = result.get('success', False)
            details = {'url': url}
            error = result.get('error')
            
            if success and result.get('data'):
                data = result.get('data', {})
                if isinstance(data, dict):
                    # Check capture details
                    details['capture_success'] = data.get('success', False)
                    details['content_length'] = data.get('content_length', 0)
                    details['status_code'] = data.get('status_code', 0)
                    
                    # Check for enhanced features
                    if 'metadata' in data:
                        details['has_metadata'] = True
                    if 'enhanced' in str(data):
                        details['using_enhanced_api'] = True
            
            self.log_test_result(
                f"Page Capture: {url}",
                success,
                result.get('duration', 0),
                details,
                error
            )
            
            test_results.append(success)
        
        return all(test_results)
    
    def test_browser_bulk_screenshot_capture(self):
        """Test 4: Browser bulk capture (parallel processing)"""
        print("🔍 Test 4: Browser Bulk Capture (Parallel Processing)")
        
        # Test with multiple URLs to see parallel processing
        url_list = ",".join(self.test_urls[:3])
        
        result = self.execute_mcp_function('browser_bulk_screenshot_capture', url_list)
        
        success = result.get('success', False)
        details = {'url_count': len(self.test_urls[:3])}
        error = result.get('error')
        
        if success and result.get('data'):
            data = result.get('data', {})
            if isinstance(data, dict):
                # Check bulk processing results
                details['bulk_success'] = data.get('success', False)
                details['total_processed'] = data.get('total', 0)
                details['successful'] = data.get('successful', 0)
                details['failed'] = data.get('failed', 0)
                details['processing_time'] = data.get('processing_time', 0)
                
                # Calculate performance metrics
                if details['processing_time'] > 0:
                    details['urls_per_second'] = round(details['total_processed'] / details['processing_time'], 2)
                
                # Check if parallel processing was used
                if 'parallel' in str(data).lower() or details['urls_per_second'] > 1:
                    details['parallel_processing'] = True
        
        self.log_test_result(
            "Bulk Screenshot Capture",
            success,
            result.get('duration', 0),
            details,
            error
        )
        
        return success
    
    def test_browser_custom_automation_task(self):
        """Test 5: Browser custom automation"""
        print("🔍 Test 5: Browser Custom Automation")
        
        # Test different custom automation tasks
        test_tasks = [
            ("search", "Find information about python"),
            ("analyze", "Extract metadata from webpage"),
            ("status", "Check system status")
        ]
        
        test_results = []
        
        for task_type, task_description in test_tasks[:2]:  # Test first 2 tasks
            print(f"  🔧 Custom Task: {task_description}")
            
            result = self.execute_mcp_function('browser_custom_automation_task', task_description)
            
            success = result.get('success', False)
            details = {
                'task_type': task_type,
                'task_description': task_description
            }
            error = result.get('error')
            
            if success and result.get('data'):
                data = result.get('data', {})
                if isinstance(data, dict):
                    details['task_success'] = data.get('success', False)
                    details['has_routing'] = any(key in data for key in ['search', 'capture', 'status'])
                    
                    # Check for enhanced capabilities
                    if 'browser_api_v2' in str(data):
                        details['using_enhanced_api'] = True
            
            self.log_test_result(
                f"Custom Task: {task_description[:30]}...",
                success,
                result.get('duration', 0),
                details,
                error
            )
            
            test_results.append(success)
        
        return all(test_results)
    
    def test_vm_browser_environment(self):
        """Test 6: VM browser environment setup"""
        print("🔍 Test 6: VM Browser Environment")
        
        # Test if the VM has the enhanced browser components
        result = self.execute_mcp_function('execute_vm_command', 'ls -la /home/user/browser_automation/')
        
        success = result.get('success', False)
        details = {}
        error = result.get('error')
        
        if success and result.get('data'):
            output = result.get('stdout', '')
            
            # Check for key files
            expected_files = [
                'browser_api_v2.py',
                'enhanced_search_api.py',
                'form_handler.py',
                'session_manager.py',
                'stealth_browser.py',
                'content_extractor.py',
                'parallel_processor.py'
            ]
            
            files_found = []
            for file in expected_files:
                if file in output:
                    files_found.append(file)
            
            details = {
                'expected_files': len(expected_files),
                'files_found': len(files_found),
                'deployment_complete': len(files_found) == len(expected_files),
                'missing_files': [f for f in expected_files if f not in files_found]
            }
        
        self.log_test_result(
            "VM Browser Environment",
            success,
            result.get('duration', 0),
            details,
            error
        )
        
        return success
    
    def generate_performance_report(self):
        """Generate comprehensive performance report"""
        end_time = time.time()
        total_duration = end_time - self.start_time
        
        # Calculate statistics
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Performance metrics
        avg_duration = sum(result['duration_seconds'] for result in self.test_results) / total_tests if total_tests > 0 else 0
        fastest_test = min(self.test_results, key=lambda x: x['duration_seconds'])['duration_seconds'] if self.test_results else 0
        slowest_test = max(self.test_results, key=lambda x: x['duration_seconds'])['duration_seconds'] if self.test_results else 0
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'success_rate_percent': round(success_rate, 1),
                'total_duration_seconds': round(total_duration, 2)
            },
            'performance_metrics': {
                'average_test_duration': round(avg_duration, 2),
                'fastest_test_duration': round(fastest_test, 2),
                'slowest_test_duration': round(slowest_test, 2),
                'tests_per_minute': round((total_tests / total_duration) * 60, 1) if total_duration > 0 else 0
            },
            'detailed_results': self.test_results,
            'timestamp': datetime.now().isoformat(),
            'vm_name': self.vm_name
        }
        
        # Save report
        report_filename = f"comprehensive_browser_test_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print("=" * 60)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 60)
        print(f"🎯 Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        print(f"⏱️  Total Test Duration: {total_duration:.1f}s")
        print(f"📈 Average Test Duration: {avg_duration:.1f}s")
        print(f"🏃 Tests per Minute: {report['performance_metrics']['tests_per_minute']}")
        print(f"⚡ Fastest Test: {fastest_test:.1f}s")
        print(f"🐌 Slowest Test: {slowest_test:.1f}s")
        print()
        
        if failed_tests > 0:
            print("❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test_name']}: {result.get('error', 'Unknown error')}")
        else:
            print("✅ ALL TESTS PASSED!")
        
        print()
        print(f"📄 Detailed report saved: {report_filename}")
        print("=" * 60)
        
        return report
    
    def run_comprehensive_test_suite(self):
        """Run all tests in sequence"""
        print("🎬 Starting comprehensive browser automation test suite...")
        print()
        
        # Test sequence
        tests = [
            ("VM Environment Check", self.test_vm_browser_environment),
            ("Status Check", self.test_browser_automation_status_check),
            ("Intelligent Search", self.test_browser_intelligent_search),
            ("Page Capture", self.test_browser_capture_page_screenshot),
            ("Bulk Processing", self.test_browser_bulk_screenshot_capture),
            ("Custom Automation", self.test_browser_custom_automation_task)
        ]
        
        for test_name, test_function in tests:
            print(f"🔄 Running: {test_name}")
            try:
                test_function()
            except Exception as e:
                self.log_test_result(test_name, False, 0, {}, str(e))
            print("-" * 40)
        
        # Generate final report
        return self.generate_performance_report()


def main():
    """Main test runner"""
    suite = ComprehensiveBrowserTestSuite()
    report = suite.run_comprehensive_test_suite()
    
    # Exit with appropriate code
    success_rate = report['test_summary']['success_rate_percent']
    if success_rate >= 80:
        print("🎉 Test suite completed successfully!")
        sys.exit(0)
    else:
        print(f"⚠️  Test suite completed with {success_rate:.1f}% success rate")
        sys.exit(1)


if __name__ == '__main__':
    main()