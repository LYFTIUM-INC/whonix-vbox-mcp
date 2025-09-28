#!/usr/bin/env python3
"""
Stealth Browser - Anti-bot detection evasion techniques
Provides user-agent rotation, realistic headers, and behavior patterns
"""

import random
import time
import subprocess
import json
import sys
import os
import hashlib
from typing import Dict, List, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StealthBrowser:
    def __init__(self, use_proxy: bool = True):
        """
        Initialize stealth browser with evasion techniques
        
        Args:
            use_proxy: Whether to use Tor proxy
        """
        self.use_proxy = use_proxy
        
        # Realistic user agents (2024 versions)
        self.user_agents = [
            # Chrome on Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            
            # Firefox on Linux
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:122.0) Gecko/20100101 Firefox/122.0',
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0',
            
            # Chrome on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            
            # Firefox on Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
            
            # Safari on Mac
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        # Realistic accept languages
        self.accept_languages = [
            'en-US,en;q=0.9',
            'en-GB,en;q=0.9',
            'en-US,en;q=0.9,fr;q=0.8',
            'en-US,en;q=0.9,de;q=0.8',
            'en-US,en;q=0.9,es;q=0.8'
        ]
        
        # Browser fingerprint components
        self.browser_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Linux"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Dnt': '1'
        }
        
        # Referer patterns
        self.referer_patterns = [
            'https://www.google.com/',
            'https://duckduckgo.com/',
            'https://www.bing.com/',
            'https://search.yahoo.com/',
            None  # Direct navigation
        ]
        
        # Timing patterns (in seconds)
        self.timing_patterns = {
            'page_load': (2, 5),      # Time to load a page
            'read_time': (5, 30),      # Time spent reading
            'form_fill': (10, 45),     # Time to fill forms
            'click_delay': (0.5, 2),   # Delay between clicks
            'scroll_time': (1, 3)      # Time to scroll
        }
    
    def get_random_user_agent(self) -> str:
        """Get a random realistic user agent"""
        return random.choice(self.user_agents)
    
    def get_random_accept_language(self) -> str:
        """Get a random accept language"""
        return random.choice(self.accept_languages)
    
    def get_random_referer(self) -> Optional[str]:
        """Get a random referer or None for direct navigation"""
        return random.choice(self.referer_patterns)
    
    def get_stealth_headers(self, url: Optional[str] = None) -> Dict[str, str]:
        """
        Generate a complete set of stealth headers
        
        Args:
            url: Optional URL for context-aware headers
            
        Returns:
            Dictionary of headers
        """
        headers = self.browser_headers.copy()
        
        # Random user agent
        user_agent = self.get_random_user_agent()
        headers['User-Agent'] = user_agent
        
        # Random accept language
        headers['Accept-Language'] = self.get_random_accept_language()
        
        # Random referer
        referer = self.get_random_referer()
        if referer:
            headers['Referer'] = referer
            headers['Sec-Fetch-Site'] = 'cross-site'
        
        # Adjust platform headers based on user agent
        if 'Windows' in user_agent:
            headers['Sec-Ch-Ua-Platform'] = '"Windows"'
        elif 'Macintosh' in user_agent:
            headers['Sec-Ch-Ua-Platform'] = '"macOS"'
        else:
            headers['Sec-Ch-Ua-Platform'] = '"Linux"'
        
        # Adjust browser headers based on user agent
        if 'Firefox' in user_agent:
            # Firefox doesn't send Chrome-specific headers
            headers.pop('Sec-Ch-Ua', None)
            headers.pop('Sec-Ch-Ua-Mobile', None)
            headers.pop('Sec-Ch-Ua-Platform', None)
        
        return headers
    
    def get_curl_stealth_args(self, include_timing: bool = True) -> List[str]:
        """
        Generate curl arguments for stealth mode
        
        Args:
            include_timing: Whether to include timing delays
            
        Returns:
            List of curl command arguments
        """
        headers = self.get_stealth_headers()
        args = []
        
        # Add all headers
        for key, value in headers.items():
            args.extend(['-H', f'{key}: {value}'])
        
        # Additional curl options for realism
        args.extend([
            '--compressed',           # Handle compression
            '--http2',               # Use HTTP/2
            '--tcp-keepalive',       # Keep connection alive
            '--tcp-nodelay',         # Disable Nagle's algorithm
            '--connect-timeout', '30',
            '--max-time', '60'
        ])
        
        # Add proxy if enabled
        if self.use_proxy:
            args.extend(['--socks5-hostname', '127.0.0.1:9050'])
        
        return args
    
    def random_delay(self, delay_type: str = 'click_delay') -> float:
        """
        Generate human-like random delay
        
        Args:
            delay_type: Type of delay from timing_patterns
            
        Returns:
            Delay duration in seconds
        """
        if delay_type in self.timing_patterns:
            min_delay, max_delay = self.timing_patterns[delay_type]
        else:
            min_delay, max_delay = 0.5, 2.0
        
        # Add some randomness with normal distribution
        mean = (min_delay + max_delay) / 2
        std_dev = (max_delay - min_delay) / 4
        
        delay = random.gauss(mean, std_dev)
        # Ensure within bounds
        delay = max(min_delay, min(delay, max_delay))
        
        time.sleep(delay)
        return delay
    
    def make_stealth_request(self, url: str, method: str = 'GET',
                           data: Optional[Dict] = None,
                           cookies: Optional[str] = None) -> Dict:
        """
        Make HTTP request with full stealth mode
        
        Args:
            url: URL to request
            method: HTTP method
            data: Optional form data
            cookies: Optional cookie file path
            
        Returns:
            Response dictionary
        """
        try:
            # Human-like delay before request
            self.random_delay('click_delay')
            
            # Build curl command with stealth headers
            cmd = ['curl', '-s', '-L'] + self.get_curl_stealth_args()
            
            # Add cookies if provided
            if cookies and os.path.exists(cookies):
                cmd.extend(['-b', cookies, '-c', cookies])
            
            # Add method and data
            if method == 'POST' and data:
                for key, value in data.items():
                    cmd.extend(['-d', f'{key}={value}'])
            elif method != 'GET':
                cmd.extend(['-X', method])
            
            # Add response metrics
            cmd.extend(['-w', '\n%{http_code}\n%{time_total}\n%{size_download}'])
            
            cmd.append(url)
            
            # Execute request
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
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
            
            # Simulate reading time based on content size
            if int(size_download) > 0:
                # Approximate reading speed: 200 words per minute
                # Assuming 5 characters per word
                words = int(size_download) / 5
                reading_time = min((words / 200) * 60, 30)  # Cap at 30 seconds
                if reading_time > 1:
                    time.sleep(random.uniform(1, min(reading_time, 5)))
            
            return {
                'success': result.returncode == 0,
                'status_code': int(status_code) if status_code.isdigit() else 0,
                'response_time': float(time_total) if time_total.replace('.', '').isdigit() else 0,
                'content_size': int(size_download) if size_download.isdigit() else 0,
                'content': content,
                'url': url,
                'method': method,
                'user_agent': self.get_random_user_agent()
            }
            
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Request timeout',
                'url': url
            }
        except Exception as e:
            logger.error(f"Stealth request failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
    
    def simulate_human_browsing(self, urls: List[str], 
                              session_file: Optional[str] = None) -> List[Dict]:
        """
        Simulate human-like browsing pattern across multiple pages
        
        Args:
            urls: List of URLs to visit
            session_file: Optional cookie file for session
            
        Returns:
            List of response dictionaries
        """
        results = []
        
        for idx, url in enumerate(urls):
            # First page load is usually direct
            if idx == 0:
                self.browser_headers.pop('Referer', None)
            else:
                # Subsequent pages have previous URL as referer
                self.browser_headers['Referer'] = urls[idx - 1]
            
            # Make request
            result = self.make_stealth_request(url, cookies=session_file)
            results.append(result)
            
            # Simulate reading/interaction time
            if idx < len(urls) - 1:  # Not the last page
                self.random_delay('read_time')
        
        return results
    
    def rotate_identity(self) -> Dict:
        """
        Rotate browser identity by changing user agent and headers
        
        Returns:
            New identity information
        """
        new_agent = self.get_random_user_agent()
        new_language = self.get_random_accept_language()
        
        # Determine browser type from user agent
        if 'Chrome' in new_agent:
            browser_type = 'Chrome'
        elif 'Firefox' in new_agent:
            browser_type = 'Firefox'
        elif 'Safari' in new_agent:
            browser_type = 'Safari'
        else:
            browser_type = 'Unknown'
        
        # Determine platform
        if 'Windows' in new_agent:
            platform = 'Windows'
        elif 'Macintosh' in new_agent:
            platform = 'macOS'
        else:
            platform = 'Linux'
        
        return {
            'user_agent': new_agent,
            'accept_language': new_language,
            'browser': browser_type,
            'platform': platform,
            'identity_hash': hashlib.md5(new_agent.encode()).hexdigest()[:8]
        }


def main():
    """Command line interface for stealth browser"""
    if len(sys.argv) < 2:
        print(json.dumps({
            'success': False,
            'error': 'Usage: stealth_browser.py <command> [args]',
            'commands': ['request', 'browse', 'identity']
        }))
        sys.exit(1)
    
    command = sys.argv[1]
    browser = StealthBrowser()
    
    if command == 'request':
        url = sys.argv[2] if len(sys.argv) > 2 else ''
        if not url:
            print(json.dumps({'success': False, 'error': 'URL required'}))
            sys.exit(1)
        
        result = browser.make_stealth_request(url)
        # Limit content in output
        if 'content' in result:
            result['content_preview'] = result['content'][:500]
            result['content_length'] = len(result['content'])
            del result['content']
        
        print(json.dumps(result, indent=2))
    
    elif command == 'browse':
        # Simulate browsing multiple pages
        if len(sys.argv) > 2:
            urls = sys.argv[2].split(',')
            results = browser.simulate_human_browsing(urls)
            
            # Summarize results
            summary = {
                'success': True,
                'pages_visited': len(results),
                'successful': sum(1 for r in results if r.get('success')),
                'total_time': sum(r.get('response_time', 0) for r in results),
                'results': []
            }
            
            for r in results:
                summary['results'].append({
                    'url': r.get('url'),
                    'status': r.get('status_code'),
                    'success': r.get('success')
                })
            
            print(json.dumps(summary, indent=2))
        else:
            print(json.dumps({'success': False, 'error': 'URLs required'}))
    
    elif command == 'identity':
        # Rotate and show new identity
        import hashlib
        identity = browser.rotate_identity()
        print(json.dumps(identity, indent=2))
    
    else:
        print(json.dumps({
            'success': False,
            'error': f'Unknown command: {command}'
        }))


if __name__ == '__main__':
    main()