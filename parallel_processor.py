#!/usr/bin/env python3
"""
Parallel Processor - Async batch processing for browser operations
Provides parallel URL processing with rate limiting and error handling
"""

import asyncio
import subprocess
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional, Any, Callable
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ParallelProcessor:
    def __init__(self, max_workers: int = 5, rate_limit: float = 1.0):
        """
        Initialize parallel processor
        
        Args:
            max_workers: Maximum number of concurrent workers
            rate_limit: Minimum delay between batches (seconds)
        """
        self.max_workers = max_workers
        self.rate_limit = rate_limit
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # User agent for consistency
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    
    async def process_urls_parallel(self, urls: List[str], 
                                  operation: str = 'fetch',
                                  operation_args: Optional[Dict] = None) -> Dict:
        """
        Process multiple URLs in parallel
        
        Args:
            urls: List of URLs to process
            operation: Type of operation (fetch, screenshot, analyze)
            operation_args: Additional arguments for operation
            
        Returns:
            Dictionary with batch results
        """
        if not urls:
            return {
                'success': True,
                'total': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }
        
        start_time = time.time()
        
        # Create tasks for all URLs
        tasks = []
        for idx, url in enumerate(urls):
            task = asyncio.create_task(
                self._process_single_url(url, operation, operation_args or {}, idx)
            )
            tasks.append(task)
        
        # Wait for all tasks with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300  # 5 minute timeout for entire batch
            )
        except asyncio.TimeoutError:
            logger.error("Batch processing timeout")
            return {
                'success': False,
                'error': 'Batch processing timeout',
                'total': len(urls),
                'results': []
            }
        
        # Process results
        successful = 0
        failed = 0
        processed_results = []
        
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[idx] if idx < len(urls) else 'unknown',
                    'success': False,
                    'error': str(result),
                    'index': idx
                })
                failed += 1
            else:
                if result.get('success', False):
                    successful += 1
                else:
                    failed += 1
                processed_results.append(result)
        
        total_time = time.time() - start_time
        
        return {
            'success': True,
            'total': len(urls),
            'successful': successful,
            'failed': failed,
            'processing_time': total_time,
            'average_time_per_url': total_time / len(urls),
            'operation': operation,
            'results': processed_results
        }
    
    async def _process_single_url(self, url: str, operation: str, 
                                args: Dict, index: int) -> Dict:
        """
        Process a single URL asynchronously
        
        Args:
            url: URL to process
            operation: Type of operation
            args: Operation arguments
            index: URL index in batch
            
        Returns:
            Processing result
        """
        loop = asyncio.get_event_loop()
        
        try:
            if operation == 'fetch':
                result = await loop.run_in_executor(
                    self.executor,
                    self._fetch_url,
                    url, args
                )
            elif operation == 'screenshot':
                result = await loop.run_in_executor(
                    self.executor,
                    self._screenshot_url,
                    url, args
                )
            elif operation == 'analyze':
                result = await loop.run_in_executor(
                    self.executor,
                    self._analyze_url,
                    url, args
                )
            elif operation == 'search':
                result = await loop.run_in_executor(
                    self.executor,
                    self._search_query,
                    url, args  # In this case, url is the search query
                )
            else:
                result = {
                    'success': False,
                    'error': f'Unknown operation: {operation}'
                }
            
            # Add metadata
            result['url'] = url
            result['index'] = index
            result['operation'] = operation
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing URL {url}: {str(e)}")
            return {
                'url': url,
                'index': index,
                'success': False,
                'error': str(e),
                'operation': operation
            }
    
    def _fetch_url(self, url: str, args: Dict) -> Dict:
        """
        Fetch URL content using curl
        
        Args:
            url: URL to fetch
            args: Additional arguments
            
        Returns:
            Fetch result
        """
        try:
            start_time = time.time()
            
            # Build curl command
            cmd = [
                'curl', '-s', '-L',  # Silent, follow redirects
                '-A', self.user_agent,
                '--socks5-hostname', '127.0.0.1:9050',
                '--max-time', str(args.get('timeout', 30)),
                '--compressed',
                '-w', '\n%{http_code}\n%{time_total}\n%{size_download}'
            ]
            
            # Add cookies if provided
            if args.get('cookie_file'):
                cmd.extend(['-b', args['cookie_file'], '-c', args['cookie_file']])
            
            cmd.append(url)
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=args.get('timeout', 30) + 5)
            
            # Parse response
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 3:
                size_download = lines[-1]
                time_total = lines[-2]
                status_code = lines[-3]
                content = '\n'.join(lines[:-3])
            else:
                status_code = '000'
                time_total = '0'
                size_download = '0'
                content = result.stdout
            
            processing_time = time.time() - start_time
            
            return {
                'success': result.returncode == 0 and int(status_code) < 400,
                'status_code': int(status_code) if status_code.isdigit() else 0,
                'response_time': float(time_total) if time_total.replace('.', '').isdigit() else 0,
                'content_size': int(size_download) if size_download.isdigit() else 0,
                'processing_time': processing_time,
                'content_preview': content[:500] if content else '',
                'has_content': len(content) > 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request timeout',
                'processing_time': args.get('timeout', 30)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': 0
            }
    
    def _screenshot_url(self, url: str, args: Dict) -> Dict:
        """
        Capture URL content (simulated screenshot)
        
        Args:
            url: URL to capture
            args: Additional arguments
            
        Returns:
            Screenshot result
        """
        try:
            # Use the working browser API for screenshots
            cmd = [
                'python3', '/home/user/browser_automation/working_browser_api.py',
                'screenshot', url
            ]
            
            if args.get('filename_prefix'):
                cmd.append(args['filename_prefix'])
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    return {
                        'success': response_data.get('success', False),
                        'screenshot_path': response_data.get('screenshot_path', ''),
                        'file_size': response_data.get('file_size', 0),
                        'content_length': response_data.get('content_length', 0)
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid JSON response from screenshot API'
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Screenshot command failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_url(self, url: str, args: Dict) -> Dict:
        """
        Analyze URL content
        
        Args:
            url: URL to analyze
            args: Additional arguments
            
        Returns:
            Analysis result
        """
        try:
            # First fetch the content
            fetch_result = self._fetch_url(url, args)
            
            if not fetch_result.get('success'):
                return fetch_result
            
            # Get full content for analysis
            cmd = [
                'curl', '-s', '-L',
                '-A', self.user_agent,
                '--socks5-hostname', '127.0.0.1:9050',
                '--max-time', '30',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=35)
            
            if result.returncode != 0:
                return {
                    'success': False,
                    'error': 'Failed to fetch content for analysis'
                }
            
            content = result.stdout
            
            # Basic content analysis
            analysis = {
                'content_length': len(content),
                'word_count': len(content.split()),
                'line_count': len(content.splitlines()),
                'has_forms': '<form' in content.lower(),
                'has_javascript': '<script' in content.lower(),
                'has_css': '<style' in content.lower() or 'stylesheet' in content.lower(),
                'has_images': '<img' in content.lower(),
                'has_links': '<a ' in content.lower(),
                'title': '',
                'meta_description': ''
            }
            
            # Extract title
            import re
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE)
            if title_match:
                analysis['title'] = title_match.group(1).strip()
            
            # Extract meta description
            desc_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']+)["\']', content, re.IGNORECASE)
            if desc_match:
                analysis['meta_description'] = desc_match.group(1).strip()
            
            return {
                'success': True,
                'analysis': analysis,
                'status_code': fetch_result.get('status_code', 0)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _search_query(self, query: str, args: Dict) -> Dict:
        """
        Perform search query
        
        Args:
            query: Search query
            args: Additional arguments
            
        Returns:
            Search result
        """
        try:
            # Use enhanced search API
            cmd = [
                'python3', '/home/user/browser_automation/enhanced_search_api.py',
                query, str(args.get('max_results', 10))
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    response_data = json.loads(result.stdout)
                    return {
                        'success': response_data.get('success', False),
                        'query': query,
                        'results_count': response_data.get('total', 0),
                        'results': response_data.get('results', [])[:5]  # First 5 results
                    }
                except json.JSONDecodeError:
                    return {
                        'success': False,
                        'error': 'Invalid JSON response from search API'
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Search command failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_process_with_rate_limit(self, items: List[str], 
                                          operation: str,
                                          batch_size: int = None,
                                          delay_between_batches: float = None) -> List[Dict]:
        """
        Process items in batches with rate limiting
        
        Args:
            items: List of items to process
            operation: Operation type
            batch_size: Size of each batch (defaults to max_workers)
            delay_between_batches: Delay between batches
            
        Returns:
            List of all results
        """
        if not batch_size:
            batch_size = self.max_workers
        
        if not delay_between_batches:
            delay_between_batches = self.rate_limit
        
        all_results = []
        
        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(items) + batch_size - 1)//batch_size}")
            
            batch_result = await self.process_urls_parallel(batch, operation)
            all_results.extend(batch_result.get('results', []))
            
            # Rate limiting delay between batches
            if i + batch_size < len(items):
                await asyncio.sleep(delay_between_batches)
        
        return all_results
    
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)


async def main():
    """Command line interface for parallel processor"""
    if len(sys.argv) < 3:
        print(json.dumps({
            'success': False,
            'error': 'Usage: parallel_processor.py <operation> <urls_or_queries>',
            'operations': ['fetch', 'screenshot', 'analyze', 'search'],
            'example': 'parallel_processor.py fetch "url1,url2,url3"'
        }))
        sys.exit(1)
    
    operation = sys.argv[1]
    items = sys.argv[2].split(',')
    
    # Optional parameters
    max_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    
    processor = ParallelProcessor(max_workers=max_workers)
    
    try:
        result = await processor.process_urls_parallel(items, operation)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(json.dumps({
            'success': False,
            'error': str(e)
        }))
    finally:
        processor.cleanup()


if __name__ == '__main__':
    asyncio.run(main())