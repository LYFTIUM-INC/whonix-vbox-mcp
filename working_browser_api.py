#!/usr/bin/env python3
"""
Working Browser API - Fallback Implementation
Provides working browser automation functionality even when headless browsers fail
"""

import json
import sys
import subprocess
import os
import urllib.parse
import urllib.request
import re
from datetime import datetime
from typing import Dict, List, Optional, Union

class WorkingBrowserAutomation:
    """Working browser automation with fallback methods"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.screenshot_dir = "/home/user/browser_screenshots"
        self.ensure_directories()
    
    def ensure_directories(self):
        """Ensure required directories exist"""
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent path traversal"""
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_."
        sanitized = ''.join(c for c in filename if c in safe_chars)
        return sanitized[:100]
    
    def create_error_response(self, error_type: str, message: str, context: Dict = None) -> Dict:
        """Standardized error response format"""
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": message,
                "context": context or {},
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def create_success_response(self, data: Dict) -> Dict:
        """Standardized success response format"""
        response = {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        return response
    
    def get_proxy_env(self) -> Dict[str, str]:
        """Get environment with Tor proxy configuration"""
        env = os.environ.copy()
        env.update({
            'http_proxy': 'socks5://127.0.0.1:9050',
            'https_proxy': 'socks5://127.0.0.1:9050'
        })
        return env
    
    def status_check(self) -> Dict:
        """Check status of available tools"""
        try:
            # Check available tools
            tools_available = {}
            
            # Check curl
            try:
                result = subprocess.run(['curl', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                tools_available['curl'] = result.returncode == 0
            except:
                tools_available['curl'] = False
            
            # Check wget
            try:
                result = subprocess.run(['wget', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                tools_available['wget'] = result.returncode == 0
            except:
                tools_available['wget'] = False
            
            # Check python urllib
            tools_available['urllib'] = True  # Always available
            
            # Check tor connection
            tor_working = self.test_tor_connection()
            
            return self.create_success_response({
                "tools_available": tools_available,
                "tor_connection": tor_working,
                "framework_status": "operational",
                "vm_status": "ready",
                "screenshot_directory": self.screenshot_dir,
                "environment": "working_fallback",
                "note": "Using fallback web automation - no headless browser screenshots available"
            })
            
        except Exception as e:
            return self.create_error_response("status_check_failed", str(e))
    
    def test_tor_connection(self) -> bool:
        """Test if Tor connection is working"""
        try:
            # Test connection to Tor check page
            env = self.get_proxy_env()
            result = subprocess.run([
                'curl', '-s', '--socks5-hostname', '127.0.0.1:9050',
                'https://check.torproject.org/', '--max-time', '10'
            ], capture_output=True, text=True, env=env, timeout=15)
            
            return "Congratulations" in result.stdout and result.returncode == 0
        except:
            return False
    
    def fetch_page_content(self, url: str) -> Dict:
        """Fetch page content using available tools"""
        try:
            # Validate URL
            if not url or not isinstance(url, str):
                return self.create_error_response("invalid_url", "URL must be a non-empty string")
            
            # Try curl first (best Tor support)
            try:
                env = self.get_proxy_env()
                result = subprocess.run([
                    'curl', '-s', '--socks5-hostname', '127.0.0.1:9050',
                    url, '--max-time', str(self.timeout)
                ], capture_output=True, text=True, env=env, timeout=self.timeout + 5)
                
                if result.returncode == 0:
                    return self.create_success_response({
                        "url": url,
                        "content_length": len(result.stdout),
                        "content_preview": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                        "method": "curl",
                        "via_tor": True
                    })
            except Exception as e:
                pass
            
            # Fallback to wget
            try:
                env = self.get_proxy_env()
                result = subprocess.run([
                    'wget', '-O', '-', url, '--timeout=' + str(self.timeout)
                ], capture_output=True, text=True, env=env, timeout=self.timeout + 5)
                
                if result.returncode == 0:
                    return self.create_success_response({
                        "url": url,
                        "content_length": len(result.stdout),
                        "content_preview": result.stdout[:500] + "..." if len(result.stdout) > 500 else result.stdout,
                        "method": "wget",
                        "via_tor": True
                    })
            except Exception as e:
                pass
            
            return self.create_error_response("fetch_failed", "All fetch methods failed", {"url": url})
                
        except Exception as e:
            return self.create_error_response("fetch_exception", str(e))
    
    def simulate_screenshot(self, url: str, custom_filename: str = None) -> Dict:
        """Simulate screenshot by fetching page content and creating a report"""
        try:
            # Fetch the page content
            content_result = self.fetch_page_content(url)
            
            if not content_result.get("success"):
                return content_result
            
            # Create a "screenshot" report file
            timestamp = int(datetime.now().timestamp())
            if custom_filename:
                safe_filename = self.sanitize_filename(custom_filename)
                filename = f"{safe_filename}_{timestamp}.txt"
            else:
                filename = f"page_content_{timestamp}.txt"
            
            report_path = os.path.join(self.screenshot_dir, filename)
            
            # Create page report
            page_report = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "content_length": content_result.get("content_length", 0),
                "method": content_result.get("method", "unknown"),
                "via_tor": content_result.get("via_tor", False),
                "content_preview": content_result.get("content_preview", ""),
                "note": "This is a page content report - headless browser screenshots unavailable in this VM environment"
            }
            
            # Save report
            with open(report_path, 'w') as f:
                json.dump(page_report, f, indent=2)
            
            file_size = os.path.getsize(report_path)
            
            return self.create_success_response({
                "screenshot_path": report_path,
                "file_size": file_size,
                "url_captured": url,
                "filename": filename,
                "content_length": content_result.get("content_length", 0),
                "method": "page_content_report",
                "note": "Screenshot simulated as page content report due to browser limitations"
            })
            
        except Exception as e:
            return self.create_error_response("screenshot_exception", str(e))
    
    def search_with_content(self, query: str, search_engine: str = "duckduckgo") -> Dict:
        """Perform search and fetch content"""
        try:
            # URL encode the query
            encoded_query = urllib.parse.quote_plus(query)
            
            # Build search URL
            if search_engine.lower() == "duckduckgo":
                search_url = f"https://duckduckgo.com/?q={encoded_query}"
            else:
                return self.create_error_response("invalid_search_engine", "Only DuckDuckGo supported currently")
            
            # Fetch search results
            content_result = self.fetch_page_content(search_url)
            
            if not content_result.get("success"):
                return content_result
            
            # Create search report
            safe_query = self.sanitize_filename(query.replace(" ", "_"))
            timestamp = int(datetime.now().timestamp())
            filename = f"search_{safe_query}_{timestamp}.txt"
            report_path = os.path.join(self.screenshot_dir, filename)
            
            # Extract some basic info from the HTML
            content = content_result.get("content_preview", "")
            
            # Simple extraction of search result titles (basic regex)
            titles = re.findall(r'<a[^>]*class="[^"]*result[^"]*"[^>]*>([^<]+)</a>', content, re.IGNORECASE)
            if not titles:
                titles = re.findall(r'<h\d[^>]*>([^<]+)</h\d>', content, re.IGNORECASE)
            
            search_report = {
                "search_query": query,
                "search_engine": search_engine,
                "search_url": search_url,
                "timestamp": datetime.now().isoformat(),
                "content_length": content_result.get("content_length", 0),
                "method": content_result.get("method", "unknown"),
                "via_tor": content_result.get("via_tor", False),
                "extracted_titles": titles[:10],  # First 10 titles
                "content_preview": content[:1000],
                "note": "Search results extracted from HTML - visual screenshots unavailable"
            }
            
            # Save search report
            with open(report_path, 'w') as f:
                json.dump(search_report, f, indent=2)
            
            file_size = os.path.getsize(report_path)
            
            return self.create_success_response({
                "search_query": query,
                "search_engine": search_engine,
                "screenshot_path": report_path,
                "file_size": file_size,
                "url_captured": search_url,
                "extracted_titles": titles[:5],  # Return first 5 in response
                "method": "content_extraction"
            })
            
        except Exception as e:
            return self.create_error_response("search_exception", str(e))
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> Dict:
        """Clean up old files"""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            
            cleaned_files = []
            total_size_freed = 0
            
            for filename in os.listdir(self.screenshot_dir):
                file_path = os.path.join(self.screenshot_dir, filename)
                if os.path.isfile(file_path):
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > max_age_seconds:
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            cleaned_files.append(filename)
                            total_size_freed += file_size
                        except Exception:
                            continue
            
            return self.create_success_response({
                "files_cleaned": len(cleaned_files),
                "size_freed_bytes": total_size_freed,
                "max_age_hours": max_age_hours,
                "cleaned_files": cleaned_files[:10]
            })
            
        except Exception as e:
            return self.create_error_response("cleanup_failed", str(e))

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print(json.dumps({
            "success": False,
            "error": "Usage: python3 working_browser_api.py <command> [args...]"
        }, indent=2))
        sys.exit(1)
    
    automation = WorkingBrowserAutomation()
    command = sys.argv[1].lower()
    
    try:
        if command == "status":
            result = automation.status_check()
        elif command == "screenshot" and len(sys.argv) >= 3:
            url = sys.argv[2]
            custom_filename = sys.argv[3] if len(sys.argv) > 3 else None
            result = automation.simulate_screenshot(url, custom_filename)
        elif command == "search" and len(sys.argv) >= 3:
            query = sys.argv[2]
            search_engine = sys.argv[3] if len(sys.argv) > 3 else "duckduckgo"
            result = automation.search_with_content(query, search_engine)
        elif command == "fetch" and len(sys.argv) >= 3:
            url = sys.argv[2]
            result = automation.fetch_page_content(url)
        elif command == "cleanup":
            max_age = int(sys.argv[2]) if len(sys.argv) > 2 else 24
            result = automation.cleanup_old_files(max_age)
        else:
            result = automation.create_error_response(
                "invalid_command",
                f"Unknown command: {command}. Available: status, screenshot, search, fetch, cleanup"
            )
        
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        error_result = automation.create_error_response("main_exception", str(e))
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()