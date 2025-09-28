#!/usr/bin/env python3
"""
Browser API v2 - Unified interface for enhanced browser automation
Combines all enhanced capabilities into a single, easy-to-use interface
"""

import sys
import json
import asyncio
import os
from typing import Dict, List, Optional, Any
import logging

# Import our enhanced modules
try:
    from enhanced_search_api import EnhancedSearchAPI
    from form_handler import FormHandler
    from session_manager import SessionManager
    from stealth_browser import StealthBrowser
    from content_extractor import ContentExtractor
    from parallel_processor import ParallelProcessor
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BrowserAPIv2:
    def __init__(self, use_proxy: bool = True, max_workers: int = 5):
        """
        Initialize enhanced browser API
        
        Args:
            use_proxy: Whether to use Tor proxy
            max_workers: Maximum parallel workers
        """
        self.use_proxy = use_proxy
        self.max_workers = max_workers
        
        # Initialize components
        self.search_api = EnhancedSearchAPI(use_proxy=use_proxy)
        self.form_handler = FormHandler(use_proxy=use_proxy)
        self.session_manager = SessionManager()
        self.stealth_browser = StealthBrowser(use_proxy=use_proxy)
        self.content_extractor = ContentExtractor()
        self.parallel_processor = ParallelProcessor(max_workers=max_workers)
    
    def status_check(self) -> Dict:
        """
        Comprehensive status check of all components
        
        Returns:
            Status dictionary
        """
        try:
            # Check search API
            search_test = self.search_api.search("test", max_results=1)
            search_ok = search_test.get('success', False)
            
            # Check session manager
            sessions = self.session_manager.list_sessions()
            session_ok = isinstance(sessions, list)
            
            # Check stealth browser
            stealth_ok = len(self.stealth_browser.user_agents) > 0
            
            # Check content extractor
            extractor_ok = self.content_extractor is not None
            
            # Check parallel processor
            parallel_ok = self.parallel_processor.max_workers > 0
            
            return {
                'success': True,
                'timestamp': self._get_timestamp().isoformat().isoformat(),
                'components': {
                    'enhanced_search': {
                        'status': 'operational' if search_ok else 'error',
                        'details': 'duckduckgo-search integration'
                    },
                    'form_handler': {
                        'status': 'operational',
                        'details': 'POST request automation with BeautifulSoup'
                    },
                    'session_manager': {
                        'status': 'operational' if session_ok else 'error',
                        'active_sessions': len(sessions) if session_ok else 0
                    },
                    'stealth_browser': {
                        'status': 'operational' if stealth_ok else 'error',
                        'user_agents': len(self.stealth_browser.user_agents)
                    },
                    'content_extractor': {
                        'status': 'operational' if extractor_ok else 'error',
                        'details': 'BeautifulSoup4 + structured data extraction'
                    },
                    'parallel_processor': {
                        'status': 'operational' if parallel_ok else 'error',
                        'max_workers': self.parallel_processor.max_workers
                    }
                },
                'capabilities': {
                    'enhanced_search': True,
                    'form_automation': True,
                    'session_persistence': True,
                    'anti_bot_evasion': True,
                    'content_analysis': True,
                    'parallel_processing': True,
                    'tor_integration': self.use_proxy
                },
                'version': '2.0.0',
                'mode': 'enhanced'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': self._get_timestamp().isoformat()
            }
    
    def enhanced_search(self, query: str, max_results: int = 10, 
                       search_type: str = 'text') -> Dict:
        """
        Perform enhanced search with actual results
        
        Args:
            query: Search query
            max_results: Maximum results to return
            search_type: Type of search (text, news, images)
            
        Returns:
            Search results dictionary
        """
        try:
            if search_type == 'news':
                result = self.search_api.search_news(query, max_results)
            elif search_type == 'images':
                result = self.search_api.search_images(query, max_results)
            else:
                result = self.search_api.search(query, max_results)
            
            # Add API version info
            result['api_version'] = '2.0'
            result['enhancement'] = 'duckduckgo-search integration'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'query': query
            }
    
    def analyze_forms(self, url: str) -> Dict:
        """
        Analyze forms on a webpage
        
        Args:
            url: URL to analyze
            
        Returns:
            Form analysis result
        """
        try:
            forms = self.form_handler.analyze_forms(url)
            
            return {
                'success': True,
                'url': url,
                'forms_found': len(forms),
                'forms': forms,
                'api_version': '2.0'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def submit_form(self, url: str, form_data: Dict, 
                   files: Optional[Dict] = None) -> Dict:
        """
        Submit form with enhanced capabilities
        
        Args:
            url: Form action URL
            form_data: Form field data
            files: Optional file uploads
            
        Returns:
            Submission result
        """
        try:
            result = self.form_handler.submit_form(url, form_data, files)
            result['api_version'] = '2.0'
            result['enhancement'] = 'cookie persistence + secure submission'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def create_session(self, session_id: str, initial_url: Optional[str] = None,
                      description: str = "") -> Dict:
        """
        Create persistent session
        
        Args:
            session_id: Unique session identifier
            initial_url: Optional initialization URL
            description: Session description
            
        Returns:
            Session creation result
        """
        try:
            result = self.session_manager.create_session(session_id, initial_url, description)
            result['api_version'] = '2.0'
            result['enhancement'] = 'persistent cookie management'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def session_request(self, session_id: str, url: str, method: str = 'GET',
                       data: Optional[Dict] = None) -> Dict:
        """
        Make request using persistent session
        
        Args:
            session_id: Session identifier
            url: URL to request
            method: HTTP method
            data: Optional form data
            
        Returns:
            Request result
        """
        try:
            result = self.session_manager.make_request(session_id, url, method, data)
            result['api_version'] = '2.0'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id
            }
    
    def stealth_request(self, url: str, method: str = 'GET',
                       data: Optional[Dict] = None) -> Dict:
        """
        Make request with anti-bot evasion
        
        Args:
            url: URL to request
            method: HTTP method
            data: Optional form data
            
        Returns:
            Stealth request result
        """
        try:
            result = self.stealth_browser.make_stealth_request(url, method, data)
            result['api_version'] = '2.0'
            result['enhancement'] = 'anti-bot evasion headers'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def extract_content(self, html: str, base_url: Optional[str] = None,
                       extract_type: str = 'all') -> Dict:
        """
        Extract structured content from HTML
        
        Args:
            html: HTML content to parse
            base_url: Base URL for resolving relative links
            extract_type: Type of extraction (all, metadata, links, tables, forms)
            
        Returns:
            Extraction result
        """
        try:
            self.content_extractor.parse_html(html, base_url)
            
            if extract_type == 'metadata':
                extracted = self.content_extractor.extract_metadata()
            elif extract_type == 'links':
                extracted = self.content_extractor.extract_links()
            elif extract_type == 'tables':
                extracted = self.content_extractor.extract_tables()
            elif extract_type == 'forms':
                extracted = self.content_extractor.extract_forms()
            else:
                extracted = self.content_extractor.extract_all()
            
            return {
                'success': True,
                'extracted': extracted,
                'extract_type': extract_type,
                'api_version': '2.0',
                'enhancement': 'BeautifulSoup4 + structured data'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'extract_type': extract_type
            }
    
    async def parallel_process(self, urls: List[str], operation: str = 'fetch',
                             operation_args: Optional[Dict] = None) -> Dict:
        """
        Process multiple URLs in parallel
        
        Args:
            urls: List of URLs to process
            operation: Operation type (fetch, screenshot, analyze, search)
            operation_args: Additional operation arguments
            
        Returns:
            Parallel processing result
        """
        try:
            result = await self.parallel_processor.process_urls_parallel(
                urls, operation, operation_args
            )
            result['api_version'] = '2.0'
            result['enhancement'] = 'asyncio parallel processing'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'operation': operation
            }
    
    def capture_content(self, url: str, filename_prefix: Optional[str] = None) -> Dict:
        """
        Capture page content (enhanced screenshot simulation)
        
        Args:
            url: URL to capture
            filename_prefix: Optional filename prefix
            
        Returns:
            Content capture result
        """
        try:
            # Use stealth browser for capture
            result = self.stealth_browser.make_stealth_request(url)
            
            if result.get('success'):
                # Save content to file
                timestamp = int(self._get_timestamp().timestamp())
                if filename_prefix:
                    filename = f"{filename_prefix}_{timestamp}.txt"
                else:
                    filename = f"content_capture_{timestamp}.txt"
                
                screenshot_dir = "/home/user/browser_screenshots"
                os.makedirs(screenshot_dir, exist_ok=True)
                file_path = os.path.join(screenshot_dir, filename)
                
                # Create enhanced content report
                content_report = {
                    'url': url,
                    'timestamp': self._get_timestamp().isoformat().isoformat(),
                    'status_code': result.get('status_code', 0),
                    'response_time': result.get('response_time', 0),
                    'content_size': result.get('content_size', 0),
                    'user_agent': result.get('user_agent', ''),
                    'via_tor': self.use_proxy,
                    'api_version': '2.0',
                    'content': result.get('content', '')
                }
                
                with open(file_path, 'w') as f:
                    json.dump(content_report, f, indent=2)
                
                file_size = os.path.getsize(file_path)
                
                return {
                    'success': True,
                    'screenshot_path': file_path,
                    'filename': filename,
                    'file_size': file_size,
                    'content_length': result.get('content_size', 0),
                    'url_captured': url,
                    'method': 'enhanced_stealth_capture',
                    'api_version': '2.0'
                }
            else:
                return result
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def bulk_operation(self, urls: List[str], operation: str = 'capture',
                      batch_name: Optional[str] = None) -> Dict:
        """
        Perform bulk operations on multiple URLs
        
        Args:
            urls: List of URLs to process
            operation: Operation type
            batch_name: Optional batch identifier
            
        Returns:
            Bulk operation result
        """
        try:
            async def run_bulk():
                if operation == 'capture':
                    return await self.parallel_process(urls, 'screenshot')
                elif operation == 'analyze':
                    return await self.parallel_process(urls, 'analyze')
                elif operation == 'fetch':
                    return await self.parallel_process(urls, 'fetch')
                else:
                    return {
                        'success': False,
                        'error': f'Unknown bulk operation: {operation}'
                    }
            
            # Run async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(run_bulk())
            finally:
                loop.close()
            
            # Add batch metadata
            result['batch_name'] = batch_name or f"bulk_{operation}_{int(self._get_timestamp().timestamp())}"
            result['api_version'] = '2.0'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'operation': operation
            }
    
    def custom_automation(self, task_description: str, target_url: str = "",
                         custom_parameters: Optional[Dict] = None) -> Dict:
        """
        Custom automation task routing
        
        Args:
            task_description: Description of task to perform
            target_url: Optional target URL
            custom_parameters: Optional custom parameters
            
        Returns:
            Automation result
        """
        try:
            params = custom_parameters or {}
            
            # Route based on task description
            desc_lower = task_description.lower()
            
            if 'search' in desc_lower:
                query = params.get('query', target_url.split('/')[-1] if target_url else task_description)
                return self.enhanced_search(query, params.get('max_results', 10))
            
            elif 'form' in desc_lower:
                if target_url:
                    return self.analyze_forms(target_url)
                else:
                    return {'success': False, 'error': 'URL required for form analysis'}
            
            elif 'content' in desc_lower or 'extract' in desc_lower:
                if target_url:
                    # Fetch and extract content
                    stealth_result = self.stealth_request(target_url)
                    if stealth_result.get('success'):
                        return self.extract_content(stealth_result.get('content', ''), target_url)
                    else:
                        return stealth_result
                else:
                    return {'success': False, 'error': 'URL required for content extraction'}
            
            elif 'capture' in desc_lower or 'screenshot' in desc_lower:
                if target_url:
                    return self.capture_content(target_url, params.get('filename_prefix'))
                else:
                    return {'success': False, 'error': 'URL required for content capture'}
            
            else:
                # Default to status check
                return self.status_check()
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'task_description': task_description
            }
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now()
    
    def cleanup(self):
        """Cleanup resources"""
        self.parallel_processor.cleanup()


def main():
    """Command line interface for Browser API v2"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: browser_api_v2.py <command> [args...]',
            'commands': {
                'status': 'Check API status',
                'search': '<query> [max_results] - Enhanced search',
                'forms': '<url> - Analyze forms',
                'submit': '<url> <form_data_json> - Submit form',
                'session': '<action> <session_id> [url] - Session management',
                'stealth': '<url> - Stealth request',
                'extract': '<html_file> [base_url] - Extract content',
                'capture': '<url> [filename_prefix] - Capture content',
                'bulk': '<operation> <urls_comma_separated> - Bulk operations',
                'custom': '<task_description> [target_url] [params_json] - Custom automation'
            }
        }, indent=2))
        sys.exit(1)
    
    command = sys.argv[1].lower()
    api = BrowserAPIv2()
    
    try:
        if command == 'status':
            result = api.status_check()
        
        elif command == 'search':
            query = sys.argv[2] if len(sys.argv) > 2 else ''
            max_results = int(sys.argv[3]) if len(sys.argv) > 3 else 10
            result = api.enhanced_search(query, max_results)
        
        elif command == 'forms':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            result = api.analyze_forms(url)
        
        elif command == 'submit':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            form_data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
            result = api.submit_form(url, form_data)
        
        elif command == 'session':
            action = sys.argv[2] if len(sys.argv) > 2 else 'create'
            session_id = sys.argv[3] if len(sys.argv) > 3 else f"session_{int(api._get_timestamp().timestamp())}"
            
            if action == 'create':
                url = sys.argv[4] if len(sys.argv) > 4 else None
                result = api.create_session(session_id, url)
            elif action == 'request':
                url = sys.argv[4] if len(sys.argv) > 4 else ''
                result = api.session_request(session_id, url)
            else:
                result = {'success': False, 'error': f'Unknown session action: {action}'}
        
        elif command == 'stealth':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            result = api.stealth_request(url)
        
        elif command == 'extract':
            html_file = sys.argv[2] if len(sys.argv) > 2 else ''
            base_url = sys.argv[3] if len(sys.argv) > 3 else None
            
            if html_file == '-':
                html_content = sys.stdin.read()
            else:
                with open(html_file, 'r') as f:
                    html_content = f.read()
            
            result = api.extract_content(html_content, base_url)
        
        elif command == 'capture':
            url = sys.argv[2] if len(sys.argv) > 2 else ''
            filename_prefix = sys.argv[3] if len(sys.argv) > 3 else None
            result = api.capture_content(url, filename_prefix)
        
        elif command == 'bulk':
            operation = sys.argv[2] if len(sys.argv) > 2 else 'capture'
            urls = sys.argv[3].split(',') if len(sys.argv) > 3 else []
            result = api.bulk_operation(urls, operation)
        
        elif command == 'custom':
            task_description = sys.argv[2] if len(sys.argv) > 2 else ''
            target_url = sys.argv[3] if len(sys.argv) > 3 else ''
            custom_parameters = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
            result = api.custom_automation(task_description, target_url, custom_parameters)
        
        else:
            result = {
                'success': False,
                'error': f'Unknown command: {command}'
            }
        
        # Output result
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e),
            'command': command
        }, indent=2))
    
    finally:
        api.cleanup()


if __name__ == '__main__':
    main()